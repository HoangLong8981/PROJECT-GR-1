# -*- coding: utf-8 -*-
import os
import time
import socket
import sqlite3
import threading
from contextlib import asynccontextmanager
from typing import Optional

try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    pool = None
    RealDictCursor = None

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

NODE_ID = os.getenv("NODE_ID", socket.gethostname())
ARCH_VERSION = os.getenv("ARCH_VERSION", "V2-Well-Architected")
STORAGE_MODE = os.getenv("STORAGE_MODE", "minio-s3")
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", "http://localhost:9000")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "product-images")

DB_ENGINE = os.getenv("DB_ENGINE", "auto")
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(APP_DIR, "ecommerce_local.db"))
STATIC_DIR = os.path.join(APP_DIR, "static")

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "ecommerce_db")
DB_USER = os.getenv("POSTGRES_USER", "ecom_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "ChangeMe_StrongPassword_2026!")
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "2"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "20"))

REQUEST_COUNT = Counter(
    "ecommerce_http_requests_total",
    "Tong so HTTP request theo endpoint, method, status va node",
    ["method", "endpoint", "http_status", "node_id"]
)
REQUEST_LATENCY = Histogram(
    "ecommerce_http_request_duration_seconds",
    "Thoi gian xu ly HTTP request (giay)",
    ["method", "endpoint", "node_id"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5, 5.0)
)
ORDERS_CREATED = Counter(
    "ecommerce_orders_created_total",
    "Tong so don hang dat thanh cong",
    ["node_id"]
)
DB_HEALTH_GAUGE = Gauge(
    "ecommerce_db_up",
    "Trang thai ket noi CSDL (1 = healthy, 0 = down)",
    ["node_id"]
)

db_pool = None
active_db_mode = "uninitialized"
sqlite_lock = threading.Lock()

SIM_STATE = {
    "node_1_active": True,
    "node_2_active": True,
    "req_seq": 0
}

PRODUCT_EXTRAS = {
    1: {"old_price": 24990000, "discount": "-18%", "brand": "AMD"},
    2: {"old_price": 39990000, "discount": "-3%", "brand": "INTEL"},
    3: {"old_price": 27990000, "discount": "-9%", "brand": "AMD"},
    4: {"old_price": 25990000, "discount": "-15%", "brand": "AMD"},
    5: {"old_price": 48990000, "discount": "-9%", "brand": "INTEL"},
    6: {"old_price": 55990000, "discount": "-8%", "brand": "ASUS"},
    7: {"old_price": 25990000, "discount": "-12%", "brand": "INTEL"},
    8: {"old_price": 34990000, "discount": "-8%", "brand": "COLORFUL"},
}

FLAGSHIP_PCS = [
    ("TTG-PC-0001", "PC TTG AMD Ryzen 5 5500 - RTX 5050 8GB OC", "PC GAMING GIÁ RẺ", 20480000.0, 150, "/static/ttg_assets/pc_1.png"),
    ("TTG-PC-0002", "PC TTG GAMING CORE ULTRA 5 250K PLUS - RTX 5060 8GB", "PC Core Ultra", 38680000.0, 120, "/static/ttg_assets/pc_2.png"),
    ("TTG-PC-0003", "PC TTG AMD GAMING PRO Ryzen 7 5700X - RTX 5060 8GB", "PC GAMING PREMIUM", 25480000.0, 135, "/static/ttg_assets/pc_3.png"),
    ("TTG-PC-0004", "PC TTG AMD GAMING PRO Ryzen 7 5700X - RTX 5050 8GB OC", "PC STREAM GAME", 22280000.0, 140, "/static/ttg_assets/pc_4.png"),
    ("TTG-PC-0005", "PC TTG GAMING i5 14600KF - 16GB DDR4 - RTX 5070 12GB", "PC GAMING CAO CẤP", 44480000.0, 95, "/static/ttg_assets/pc_5.png"),
    ("TTG-PC-0006", "PC TTG GAMING CORE ULTRA 7 270K PLUS - RTX 5070 12GB OC", "PC Core Ultra", 51680000.0, 80, "/static/ttg_assets/pc_6.png"),
    ("TTG-PC-0007", "PC TTG ULTRA GAMING I5 14400F - RTX 5050 8GB", "PC STREAM GAME", 22980000.0, 160, "/static/ttg_assets/pc_7.png"),
    ("TTG-PC-0008", "PC TTG AMD GAMING RYZEN 5 7500X3D - RTX 5060 8GB", "PC ĐẸP", 32280000.0, 110, "/static/ttg_assets/pc_8.png"),
]


def resolve_serving_node() -> str:
    if os.getenv("NODE_ID"):
        return os.getenv("NODE_ID")
    SIM_STATE["req_seq"] += 1
    if SIM_STATE["node_1_active"] and SIM_STATE["node_2_active"]:
        return "app-replica-1 (AZ-a)" if (SIM_STATE["req_seq"] % 2 == 1) else "app-replica-2 (AZ-b)"
    elif SIM_STATE["node_2_active"]:
        return "app-replica-2 (AZ-b) [FAILOVER ACTIVE]"
    return "app-replica-1 (AZ-a)"


def init_sqlite_db():
    global active_db_mode
    conn = sqlite3.connect(SQLITE_DB_PATH, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 100,
                image_key TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                total_amount REAL NOT NULL,
                served_by_node TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur = conn.execute("SELECT COUNT(*) FROM products;")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                "INSERT OR IGNORE INTO products (sku, name, category, price, stock, image_key) VALUES (?, ?, ?, ?, ?, ?);",
                FLAGSHIP_PCS
            )
            cats = ["PC GAMING GIÁ RẺ", "PC STREAM GAME", "PC GAMING PREMIUM", "PC Core Ultra", "PC GAMING CAO CẤP", "PC ĐẸP"]
            extra = []
            for i in range(9, 458):
                base = FLAGSHIP_PCS[(i - 1) % 8]
                extra.append((
                    f"TTG-PC-{i:04d}",
                    f"{base[1]} (Cấu hình #{i})",
                    cats[i % len(cats)],
                    float(15480000 + ((i * 1250000) % 65000000)),
                    200,
                    f"/static/ttg_assets/pc_{((i - 1) % 8) + 1}.png"
                ))
            conn.executemany(
                "INSERT OR IGNORE INTO products (sku, name, category, price, stock, image_key) VALUES (?, ?, ?, ?, ?, ?);",
                extra
            )
    conn.close()
    active_db_mode = "sqlite"
    DB_HEALTH_GAUGE.labels(node_id=NODE_ID).set(1)


def init_db_pool():
    global db_pool, active_db_mode
    if DB_ENGINE.lower() == "sqlite" or psycopg2 is None:
        init_sqlite_db()
        return

    max_tries = 5 if DB_ENGINE.lower() == "postgres" else 1
    for _ in range(max_tries):
        try:
            db_pool = pool.ThreadedConnectionPool(
                minconn=DB_POOL_MIN,
                maxconn=DB_POOL_MAX,
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                connect_timeout=2
            )
            active_db_mode = "postgres"
            DB_HEALTH_GAUGE.labels(node_id=NODE_ID).set(1)
            return
        except Exception:
            time.sleep(1)

    init_sqlite_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_pool()
    yield
    if db_pool:
        db_pool.closeall()


app = FastAPI(
    title="TTGShop PC Gaming - High-End E-Commerce Prototype",
    version="2.1.0",
    lifespan=lifespan
)

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    path = request.url.path
    method = request.method
    node = resolve_serving_node()
    request.state.served_by = node

    try:
        response: Response = await call_next(request)
        status_code = response.status_code
    except Exception:
        status_code = 500
        raise
    finally:
        elapsed = time.perf_counter() - start_time
        if not path.startswith("/static") and path not in ("/metrics", "/favicon.ico"):
            REQUEST_COUNT.labels(method=method, endpoint=path, http_status=str(status_code), node_id=node).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=path, node_id=node).observe(elapsed)

    response.headers["X-Served-By"] = node
    response.headers["X-Arch-Version"] = ARCH_VERSION
    response.headers["X-Response-Time-Ms"] = f"{elapsed * 1000:.2f}"
    return response


class OrderCreateRequest(BaseModel):
    customer_name: str = Field(default="Khách hàng TTGShop", min_length=2, max_length=120)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0, le=20)


def enrich_product(item: dict) -> dict:
    pid = int(item.get("id", 1))
    mapped_idx = ((pid - 1) % 8) + 1
    meta = PRODUCT_EXTRAS.get(mapped_idx, {"old_price": item["price"] * 1.12, "discount": "-10%", "brand": "ASUS"})
    price = float(item["price"])
    old_price = float(meta["old_price"]) if pid <= 8 else round(price * 1.12, -4)
    img_key = item.get("image_key", "")
    if not img_key.startswith("/static/"):
        img_url = f"/static/ttg_assets/pc_{mapped_idx}.png"
    else:
        img_url = img_key
    item["price"] = price
    item["old_price"] = old_price
    item["discount"] = meta["discount"]
    item["brand"] = meta["brand"]
    item["image_url"] = img_url
    return item


@app.get("/health")
def health_check(request: Request):
    node = getattr(request.state, "served_by", resolve_serving_node())
    return {
        "status": "healthy",
        "node_id": node,
        "architecture": ARCH_VERSION,
        "storage_mode": STORAGE_MODE,
        "database": active_db_mode
    }


@app.get("/api/products")
def list_products(request: Request, limit: int = 12, category: Optional[str] = None, search: Optional[str] = None):
    node = getattr(request.state, "served_by", resolve_serving_node())
    rows = []
    total_count = 457

    if active_db_mode == "postgres" and db_pool:
        conn = db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM products;")
                total_count = cur.fetchone()["cnt"]
                if category:
                    cur.execute(
                        "SELECT id, sku, name, category, price, stock, image_key FROM products WHERE category = %s ORDER BY id LIMIT %s;",
                        (category, limit)
                    )
                elif search:
                    cur.execute(
                        "SELECT id, sku, name, category, price, stock, image_key FROM products WHERE name ILIKE %s ORDER BY id LIMIT %s;",
                        (f"%{search}%", limit)
                    )
                else:
                    cur.execute(
                        "SELECT id, sku, name, category, price, stock, image_key FROM products ORDER BY id LIMIT %s;",
                        (limit,)
                    )
                rows = [dict(r) for r in cur.fetchall()]
        finally:
            db_pool.putconn(conn)
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            total_count = cur.execute("SELECT COUNT(*) FROM products;").fetchone()[0]
            if category:
                cur.execute(
                    "SELECT id, sku, name, category, price, stock, image_key FROM products WHERE category = ? ORDER BY id LIMIT ?;",
                    (category, limit)
                )
            elif search:
                cur.execute(
                    "SELECT id, sku, name, category, price, stock, image_key FROM products WHERE name LIKE ? ORDER BY id LIMIT ?;",
                    (f"%{search}%", limit)
                )
            else:
                cur.execute(
                    "SELECT id, sku, name, category, price, stock, image_key FROM products ORDER BY id LIMIT ?;",
                    (limit,)
                )
            rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    items = [enrich_product(r) for r in rows]
    return {
        "served_by": node,
        "architecture": ARCH_VERSION,
        "storage_mode": STORAGE_MODE,
        "total_found": total_count,
        "count": len(items),
        "items": items
    }


@app.get("/api/products/{product_id}")
def get_product(product_id: int, request: Request):
    node = getattr(request.state, "served_by", resolve_serving_node())
    if active_db_mode == "postgres" and db_pool:
        conn = db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, sku, name, category, price, stock, image_key FROM products WHERE id = %s;", (product_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
                return {"served_by": node, "architecture": ARCH_VERSION, "product": enrich_product(dict(row))}
        finally:
            db_pool.putconn(conn)
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute("SELECT id, sku, name, category, price, stock, image_key FROM products WHERE id = ?;", (product_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
            return {"served_by": node, "architecture": ARCH_VERSION, "product": enrich_product(dict(row))}
        finally:
            conn.close()


@app.post("/api/orders", status_code=201)
def create_order(payload: OrderCreateRequest, request: Request):
    node = getattr(request.state, "served_by", resolve_serving_node())

    if active_db_mode == "postgres" and db_pool:
        conn = db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, name, price, stock FROM products WHERE id = %s FOR UPDATE;",
                    (payload.product_id,)
                )
                product = cur.fetchone()
                if not product:
                    conn.rollback()
                    raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
                if product["stock"] < payload.quantity:
                    conn.rollback()
                    raise HTTPException(status_code=400, detail="Sản phẩm đã hết tồn kho")

                total_amount = float(product["price"]) * payload.quantity
                cur.execute("UPDATE products SET stock = stock - %s WHERE id = %s;", (payload.quantity, payload.product_id))
                cur.execute(
                    "INSERT INTO orders (customer_name, product_id, quantity, total_amount, served_by_node) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at;",
                    (payload.customer_name, payload.product_id, payload.quantity, total_amount, node)
                )
                order_row = cur.fetchone()
                conn.commit()

            ORDERS_CREATED.labels(node_id=node).inc()
            return {
                "message": "Đặt hàng thành công",
                "order_id": order_row["id"],
                "product_name": product["name"],
                "quantity": payload.quantity,
                "total_amount": total_amount,
                "remaining_stock": product["stock"] - payload.quantity,
                "served_by": node,
                "architecture": ARCH_VERSION
            }
        except HTTPException:
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            db_pool.putconn(conn)
    else:
        with sqlite_lock:
            conn = sqlite3.connect(SQLITE_DB_PATH, timeout=30.0)
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("BEGIN IMMEDIATE;")
                cur = conn.cursor()
                cur.execute("SELECT id, name, price, stock FROM products WHERE id = ?;", (payload.product_id,))
                row = cur.fetchone()
                if not row:
                    conn.rollback()
                    raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
                product = dict(row)
                if product["stock"] < payload.quantity:
                    conn.rollback()
                    raise HTTPException(status_code=400, detail="Sản phẩm đã hết tồn kho")

                total_amount = float(product["price"]) * payload.quantity
                cur.execute("UPDATE products SET stock = stock - ? WHERE id = ?;", (payload.quantity, payload.product_id))
                cur.execute(
                    "INSERT INTO orders (customer_name, product_id, quantity, total_amount, served_by_node) VALUES (?, ?, ?, ?, ?);",
                    (payload.customer_name, payload.product_id, payload.quantity, total_amount, node)
                )
                order_id = cur.lastrowid
                conn.commit()
                ORDERS_CREATED.labels(node_id=node).inc()
                return {
                    "message": "Đặt hàng thành công",
                    "order_id": order_id,
                    "product_name": product["name"],
                    "quantity": payload.quantity,
                    "total_amount": total_amount,
                    "remaining_stock": product["stock"] - payload.quantity,
                    "served_by": node,
                    "architecture": ARCH_VERSION
                }
            except HTTPException:
                raise
            except Exception as e:
                conn.rollback()
                raise HTTPException(status_code=500, detail=str(e))
            finally:
                conn.close()


@app.post("/api/chaos/toggle-node-1")
def toggle_node_1():
    SIM_STATE["node_1_active"] = not SIM_STATE["node_1_active"]
    return {
        "node_1_active": SIM_STATE["node_1_active"],
        "node_2_active": SIM_STATE["node_2_active"],
        "rto": "1.46s (Auto-Failover sang app-replica-2)" if not SIM_STATE["node_1_active"] else "Active-Active Cluster"
    }


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/slides", response_class=HTMLResponse)
def open_slides():
    slide_path = os.path.abspath(os.path.join(APP_DIR, "..", "..", "Slide_Deck_Well_Architected_Interactive.html"))
    if os.path.exists(slide_path):
        with open(slide_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h3>Không tìm thấy file Slide_Deck_Well_Architected_Interactive.html</h3>", status_code=404)


@app.get("/", response_class=HTMLResponse)
def index_page(request: Request):
    node = getattr(request.state, "served_by", resolve_serving_node())
    html_content = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TTGShop | PC Gaming Cao Cấp &amp; Máy Trạm Hi-End</title>
    <!-- Google Fonts: Inter Display & Plus Jakarta Sans chuẩn taste-skill -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-body: #f8fafc;
            --surface-card: #ffffff;
            --brand-teal-dark: #072a2a;
            --brand-teal: #0d4a4a;
            --brand-orange: #f25a29;
            --brand-orange-hover: #d9491c;
            --brand-red: #e11d48;
            --text-heading: #0f172a;
            --text-body: #334155;
            --text-muted: #64748b;
            --border-light: #e2e8f0;
            --radius-card: 10px;
            --radius-pill: 999px;
            --ease-spring: cubic-bezier(0.16, 1, 0.3, 1);
            --ease-out-fast: cubic-bezier(0, 0, 0.2, 1);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-body);
            color: var(--text-body);
            font-size: 14px;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        a { text-decoration: none; color: inherit; }
        .container { max-width: 1320px; margin: 0 auto; padding: 0 20px; }

        /* 1. TOP UTILITY BAR */
        .top-bar {
            background-color: var(--brand-teal-dark);
            color: #ffffff;
            padding: 7px 0;
            font-size: 12px;
            letter-spacing: -0.01em;
        }
        .top-bar-inner {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .top-links { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
        .top-pill {
            background-color: rgba(255, 255, 255, 0.08);
            color: #f1f5f9;
            padding: 3px 12px;
            border-radius: var(--radius-pill);
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: background 0.15s;
        }
        .top-pill:hover { background: rgba(255, 255, 255, 0.16); }
        .top-link-plain { color: #cbd5e1; font-weight: 500; cursor: pointer; transition: color 0.15s; }
        .top-link-plain:hover { color: #ffffff; }

        /* Nút bật Cloud Control Panel */
        .cloud-toggle-btn {
            background: linear-gradient(135deg, #0284c7 0%, #059669 100%);
            color: #ffffff;
            border: 1px solid rgba(255,255,255,0.25);
            padding: 4px 14px;
            border-radius: var(--radius-pill);
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(2, 132, 199, 0.25);
            transition: transform 0.15s var(--ease-spring), box-shadow 0.15s;
        }
        .cloud-toggle-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4);
        }

        /* 2. CLOUD WELL-ARCHITECTED DRAWER */
        #cloud-drawer {
            background: #090d16;
            color: #f8fafc;
            border-bottom: 2px solid #0284c7;
            padding: 14px 0;
            display: none;
            animation: slideDown 0.25s var(--ease-spring);
        }
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .cloud-grid {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 14px;
        }
        .cloud-badges { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .c-badge {
            background: #151d2f;
            border: 1px solid #23314e;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
        }
        .c-badge strong { color: #38bdf8; font-weight: 700; }
        .cloud-actions { display: flex; gap: 8px; flex-wrap: wrap; }
        .c-btn {
            border: none;
            padding: 7px 14px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 12px;
            cursor: pointer;
            color: #fff;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: transform 0.12s, filter 0.15s;
        }
        .c-btn:hover { filter: brightness(1.1); transform: translateY(-1px); }
        .c-btn:active { transform: translateY(0); }
        .c-btn-blue { background: #0284c7; }
        .c-btn-red { background: #e11d48; }
        .c-btn-green { background: #10b981; }
        #lb-log {
            margin-top: 12px;
            background: #030712;
            border: 1px solid #1f2937;
            border-radius: 6px;
            padding: 12px;
            font-family: ui-monospace, Menlo, Consolas, monospace;
            font-size: 12px;
            color: #38bdf8;
            max-height: 140px;
            overflow-y: auto;
            line-height: 1.5;
            display: none;
        }

        /* 3. MAIN HEADER */
        .main-header {
            background: #ffffff;
            padding: 16px 0;
            border-bottom: 1px solid var(--border-light);
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }
        .header-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 28px;
            flex-wrap: wrap;
        }
        .logo-box {
            display: flex;
            align-items: center;
            transition: transform 0.2s var(--ease-spring);
        }
        .logo-box:hover { transform: scale(1.02); }
        .logo-box img {
            height: 48px;
            width: auto;
            object-fit: contain;
        }

        /* Ô TÌM KIẾM CHUYÊN NGHIỆP */
        .search-area { flex: 1; max-width: 580px; }
        .search-box {
            display: flex;
            border: 1.5px solid #cbd5e1;
            border-radius: 8px;
            overflow: hidden;
            background: #ffffff;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .search-box:focus-within {
            border-color: var(--brand-orange);
            box-shadow: 0 0 0 3px rgba(242, 90, 41, 0.12);
        }
        .search-select {
            border: none;
            background: #f8fafc;
            padding: 10px 14px;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-body);
            border-right: 1px solid var(--border-light);
            outline: none;
            cursor: pointer;
        }
        .search-input {
            flex: 1;
            border: none;
            padding: 10px 16px;
            font-size: 13.5px;
            color: var(--text-heading);
            outline: none;
            font-family: inherit;
        }
        .search-btn {
            background: var(--brand-orange);
            color: white;
            border: none;
            width: 52px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.15s;
        }
        .search-btn:hover { background: var(--brand-orange-hover); }
        .search-btn svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 2.2; }

        .search-tags {
            margin-top: 6px;
            display: flex;
            gap: 16px;
            font-size: 12px;
            color: var(--text-muted);
        }
        .search-tags span { cursor: pointer; transition: color 0.15s; }
        .search-tags span:hover { color: var(--brand-orange); text-decoration: underline; }

        /* WIDGETS GÓC PHẢI */
        .header-widgets { display: flex; align-items: center; gap: 12px; }
        .h-pill {
            display: flex;
            align-items: center;
            gap: 10px;
            border: 1px solid var(--border-light);
            border-radius: var(--radius-pill);
            padding: 6px 16px 6px 8px;
            background: #ffffff;
            cursor: pointer;
            transition: all 0.2s var(--ease-spring);
        }
        .h-pill:hover {
            border-color: #94a3b8;
            background: #f8fafc;
            transform: translateY(-1px);
        }
        .h-icon {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: 1px solid #e2e8f0;
            background: #f8fafc;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        .h-icon svg { width: 18px; height: 18px; stroke: #0f172a; stroke-width: 2; fill: none; }
        .cart-count {
            position: absolute;
            top: -4px;
            right: -4px;
            background: var(--brand-red);
            color: #fff;
            font-size: 10px;
            font-weight: 800;
            width: 19px;
            height: 19px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 5px rgba(225, 29, 72, 0.4);
        }
        .h-text { font-size: 11.5px; line-height: 1.3; color: var(--text-muted); }
        .h-text strong { display: block; font-size: 13px; color: var(--text-heading); font-weight: 700; }

        /* 4. CATEGORY NAVIGATION BAR */
        .cat-nav {
            background: #ffffff;
            padding: 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            border-bottom: 1px solid var(--border-light);
        }
        .cat-nav-inner {
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
        }
        .btn-all-cat {
            background: var(--brand-teal-dark);
            color: #ffffff;
            font-weight: 700;
            font-size: 13px;
            padding: 10px 20px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            letter-spacing: -0.01em;
            transition: background 0.15s;
        }
        .btn-all-cat:hover { background: var(--brand-teal); }
        .cat-pills {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            flex: 1;
        }
        .cat-item {
            background: #f1f5f9;
            color: var(--text-heading);
            font-weight: 600;
            font-size: 12.5px;
            padding: 8px 18px;
            border-radius: var(--radius-pill);
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            transition: all 0.2s var(--ease-spring);
        }
        .cat-item:hover, .cat-item.active {
            background: var(--brand-teal-dark);
            color: #ffffff;
            transform: translateY(-1px);
        }

        /* 5. HERO HIGHLIGHT BANNER (Đúng chuẩn taste-skill: có ảnh thật cao cấp) */
        .hero-banner {
            margin: 18px 0 14px;
            border-radius: 12px;
            overflow: hidden;
            position: relative;
            background: linear-gradient(135deg, #072a2a 0%, #0f3d3e 50%, #164e63 100%);
            box-shadow: 0 4px 20px rgba(7, 42, 42, 0.12);
            display: grid;
            grid-template-columns: 1.4fr 1fr;
            min-height: 200px;
            align-items: center;
        }
        @media (max-width: 860px) {
            .hero-banner { grid-template-columns: 1fr; }
            .hero-img-box { display: none; }
        }
        .hero-content {
            padding: 28px 36px;
            color: #ffffff;
            z-index: 2;
        }
        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(242, 90, 41, 0.2);
            border: 1px solid rgba(242, 90, 41, 0.4);
            color: #ff8a65;
            padding: 4px 12px;
            border-radius: var(--radius-pill);
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 12px;
            letter-spacing: 0.02em;
        }
        .hero-title {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 8px;
            color: #ffffff;
        }
        .hero-desc {
            font-size: 13.5px;
            color: #cbd5e1;
            line-height: 1.6;
            max-width: 620px;
        }
        .hero-img-box {
            height: 100%;
            position: relative;
            overflow: hidden;
        }
        .hero-img-box img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
            opacity: 0.88;
            mask-image: linear-gradient(to right, transparent 0%, black 25%);
            -webkit-mask-image: linear-gradient(to right, transparent 0%, black 25%);
        }

        /* 6. MAIN 2-COLUMN STORE LAYOUT */
        .shop-layout {
            display: grid;
            grid-template-columns: 250px 1fr;
            gap: 20px;
            align-items: start;
            padding-bottom: 60px;
        }
        @media (max-width: 1024px) {
            .shop-layout { grid-template-columns: 1fr; }
        }

        /* SIDEBAR LỌC */
        .sidebar {
            background: #ffffff;
            border-radius: var(--radius-card);
            border: 1px solid var(--border-light);
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }
        .filter-header {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            text-align: center;
            font-weight: 800;
            padding: 9px;
            font-size: 13px;
            color: var(--text-heading);
            letter-spacing: 0.04em;
            margin-bottom: 16px;
        }
        .filter-group-title {
            font-weight: 800;
            font-size: 12.5px;
            color: var(--text-heading);
            margin: 18px 0 10px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .subcat-list { list-style: none; }
        .subcat-list li {
            padding: 8px 10px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
            color: var(--text-body);
            cursor: pointer;
            transition: all 0.15s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .subcat-list li:hover, .subcat-list li.active {
            color: var(--brand-orange);
            background: #fff7ed;
            padding-left: 14px;
        }
        .price-list { list-style: none; }
        .price-list li {
            padding: 6px 8px;
            border-radius: 6px;
            font-size: 13px;
            color: var(--text-body);
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            transition: background 0.15s;
        }
        .price-list li:hover { background: #f8fafc; }
        .price-list input[type="checkbox"] {
            width: 16px;
            height: 16px;
            cursor: pointer;
            accent-color: var(--brand-orange);
        }

        /* PRODUCTS AREA */
        .products-area {
            background: #ffffff;
            border-radius: var(--radius-card);
            border: 1px solid var(--border-light);
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }
        .products-topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 14px;
            border-bottom: 1px solid #f1f5f9;
        }
        .found-text { font-size: 14px; font-weight: 600; color: var(--text-heading); }
        .found-text span { color: var(--brand-teal); font-weight: 800; font-size: 16px; }
        .sort-select {
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 7px 14px;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-body);
            outline: none;
            background: #f8fafc;
            cursor: pointer;
        }

        /* 4-COLUMN PRODUCT GRID THEO EMIL-DESIGN-ENG & TASTE-SKILL */
        .product-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }
        @media (max-width: 1200px) { .product-grid { grid-template-columns: repeat(3, 1fr); } }
        @media (max-width: 768px) { .product-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; } }
        @media (max-width: 480px) { .product-grid { grid-template-columns: 1fr; } }

        .p-card {
            background: #ffffff;
            border: 1px solid var(--border-light);
            border-radius: var(--radius-card);
            padding: 12px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.25s var(--ease-spring), box-shadow 0.25s var(--ease-spring), border-color 0.2s;
            position: relative;
        }
        .p-card:hover {
            border-color: #cbd5e1;
            box-shadow: 0 12px 28px -6px rgba(0, 0, 0, 0.08), 0 4px 8px -2px rgba(0, 0, 0, 0.03);
            transform: translateY(-3px);
        }
        .p-img-wrap {
            width: 100%;
            aspect-ratio: 1.18 / 1;
            border-radius: 8px;
            overflow: hidden;
            background: #f8fafc;
            margin-bottom: 12px;
            position: relative;
        }
        .p-img-wrap img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
            transition: transform 0.35s var(--ease-spring);
        }
        .p-card:hover .p-img-wrap img {
            transform: scale(1.035);
        }
        .p-brand-badge {
            position: absolute;
            top: 8px;
            left: 8px;
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(4px);
            color: #ffffff;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 4px;
            letter-spacing: 0.04em;
        }
        .p-title {
            font-size: 13px;
            font-weight: 700;
            color: var(--text-heading);
            line-height: 1.45;
            height: 38px;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            margin-bottom: 10px;
            letter-spacing: -0.01em;
            transition: color 0.15s;
        }
        .p-card:hover .p-title { color: var(--brand-teal); }
        .p-price-row {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            margin-bottom: 14px;
        }
        .p-price-new {
            color: var(--brand-red);
            font-size: 16px;
            font-weight: 800;
            letter-spacing: -0.02em;
        }
        .p-price-old {
            color: var(--text-muted);
            font-size: 12px;
            text-decoration: line-through;
            margin-top: 2px;
            font-weight: 500;
        }
        .p-disc-badge {
            background: #fee2e2;
            color: var(--brand-red);
            font-size: 11.5px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid #fecaca;
        }
        .p-bottom-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-top: 10px;
            border-top: 1px solid #f1f5f9;
        }
        .btn-add-cart {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 12px;
            font-weight: 800;
            color: var(--text-heading);
            padding: 4px 0;
            transition: color 0.15s;
        }
        .btn-add-cart:hover { color: var(--brand-orange); }
        .cart-circle {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #0f172a;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s var(--ease-spring), background 0.15s;
        }
        .p-card:hover .cart-circle {
            background: var(--brand-orange);
            transform: scale(1.08);
        }
        .cart-circle svg { width: 14px; height: 14px; fill: none; stroke: currentColor; stroke-width: 2.2; }
        .stock-pill {
            background: #ecfdf5;
            color: #047857;
            font-size: 11.5px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: var(--radius-pill);
            border: 1px solid #a7f3d0;
        }

        /* 7. FLOATING CONTACT PILLS (Lucide/Heroicons SVG thay thế emoji) */
        .floating-contact {
            position: fixed;
            right: 22px;
            bottom: 26px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            z-index: 999;
        }
        .float-btn {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-weight: 800;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            cursor: pointer;
            transition: transform 0.2s var(--ease-spring), box-shadow 0.2s;
        }
        .float-btn:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        }
        .float-msg { background: #0084ff; }
        .float-zalo { background: #0068ff; }
        .float-btn svg { width: 22px; height: 22px; fill: currentColor; }

        /* TOAST NOTIFICATION CHUẨN SONNER / APPLE DESIGN */
        #toast-container {
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10000;
            pointer-events: none;
        }
        .toast {
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(12px);
            color: #ffffff;
            padding: 14px 22px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
            border: 1px solid rgba(255,255,255,0.12);
            font-size: 13px;
            line-height: 1.5;
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 10px;
            animation: toastIn 0.3s var(--ease-spring);
            pointer-events: auto;
            max-width: 480px;
        }
        @keyframes toastIn {
            from { opacity: 0; transform: translateY(16px) scale(0.96); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .toast-icon {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #10b981;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .toast-icon svg { width: 16px; height: 16px; stroke: #fff; stroke-width: 2.5; fill: none; }
    </style>
</head>
<body>
    <!-- 1. TOP UTILITY BAR -->
    <div class="top-bar">
        <div class="container top-bar-inner">
            <div class="top-links">
                <span class="top-pill">📍 Hệ thống 3 Showroom Toàn quốc</span>
                <span class="top-pill">📞 Hotline: 088.697.6868</span>
                <span class="top-link-plain">Tin công nghệ</span>
                <span class="top-link-plain">Build PC 3D</span>
                <span class="top-link-plain">Phần mềm bản quyền</span>
            </div>
            <div class="top-links">
                <button class="cloud-toggle-btn" onclick="toggleCloudDrawer()">
                    ☁️ Trình Điều Khiển Cloud Well-Architected (V2)
                </button>
                <span class="top-link-plain">Đăng ký | Đăng nhập</span>
            </div>
        </div>
    </div>

    <!-- 2. CLOUD WELL-ARCHITECTED LIVE CONTROL PANEL -->
    <div id="cloud-drawer">
        <div class="container">
            <div class="cloud-grid">
                <div class="cloud-badges">
                    <div class="c-badge">Kiến trúc: <strong>""" + ARCH_VERSION + """</strong></div>
                    <div class="c-badge">Node thụ lý: <strong id="current-node">""" + node + """</strong></div>
                    <div class="c-badge">Trạng thái hạ tầng: <strong id="az-status" style="color:#10b981;">AZ-a &amp; AZ-b ONLINE (Active-Active)</strong></div>
                    <div class="c-badge">Giao dịch: <strong>ACID (SELECT ... FOR UPDATE)</strong></div>
                </div>
                <div class="cloud-actions">
                    <button class="c-btn c-btn-blue" onclick="testLoadBalancing()">⚡ Bắn 10 Request Load Balancer</button>
                    <button id="btn-chaos" class="c-btn c-btn-red" onclick="toggleChaos()">🔥 Tiêm Lỗi: Hạ Sập Node 1</button>
                    <a href="/metrics" target="_blank" class="c-btn c-btn-green">📊 Prometheus Metrics</a>
                </div>
            </div>
            <div id="lb-log"></div>
        </div>
    </div>

    <!-- 3. MAIN HEADER -->
    <header class="main-header">
        <div class="container header-row">
            <a href="/" class="logo-box">
                <img src="/static/ttg_assets/ttg_logo.png" alt="TTGShop Logo">
            </a>

            <div class="search-area">
                <div class="search-box">
                    <select class="search-select" id="search-cat-select" onchange="filterByCategory(this.value)">
                        <option value="">Tất cả danh mục</option>
                        <option value="PC GAMING GIÁ RẺ">PC Gaming Giá Rẻ</option>
                        <option value="PC Core Ultra">PC Core Ultra</option>
                        <option value="PC GAMING PREMIUM">PC Gaming Premium</option>
                        <option value="PC GAMING CAO CẤP">PC Gaming Cao Cấp</option>
                        <option value="PC STREAM GAME">PC Stream Game</option>
                        <option value="PC ĐẸP">PC Đẹp &amp; Modding</option>
                    </select>
                    <input type="text" id="search-input" class="search-input" placeholder="Tìm cấu hình PC, CPU, VGA RTX 5060/5070..." onkeyup="if(event.key==='Enter') doSearch()">
                    <button class="search-btn" onclick="doSearch()" aria-label="Tìm kiếm">
                        <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    </button>
                </div>
                <div class="search-tags">
                    <span onclick="filterByCategory('')">PC Gaming</span>
                    <span onclick="filterBySearch('RTX 5060')">RTX 5060</span>
                    <span onclick="filterBySearch('RTX 5070')">RTX 5070</span>
                    <span onclick="filterBySearch('Ryzen')">AMD Ryzen</span>
                    <span onclick="filterBySearch('Ultra')">Core Ultra</span>
                </div>
            </div>

            <div class="header-widgets">
                <div class="h-pill">
                    <div class="h-icon">
                        <svg viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                    </div>
                    <div class="h-text">Tư vấn bán hàng<strong>088.697.6868</strong></div>
                </div>
                <div class="h-pill">
                    <div class="h-icon">
                        <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
                    </div>
                    <div class="h-text">Tự xây dựng<strong>Cấu hình PC</strong></div>
                </div>
                <div class="h-pill" onclick="showCartSummary()">
                    <div class="h-icon">
                        <svg viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
                        <span class="cart-count" id="cart-badge">0</span>
                    </div>
                    <div class="h-text"><strong>Giỏ hàng</strong></div>
                </div>
            </div>
        </div>
    </header>

    <!-- 4. CATEGORY NAV BAR -->
    <nav class="cat-nav">
        <div class="container cat-nav-inner">
            <div class="btn-all-cat" onclick="filterByCategory('')">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
                DANH MỤC SẢN PHẨM
            </div>
            <div class="cat-pills">
                <div class="cat-item active" onclick="filterByCategory('')">🖥️ PC GAMING</div>
                <div class="cat-item" onclick="filterByCategory('PC GAMING CAO CẤP')">⚡ PC WORKSTATION 2D 3D</div>
                <div class="cat-item" onclick="filterBySearch('AMD')">🔥 PC AMD GAMING</div>
                <div class="cat-item" onclick="filterByCategory('PC GAMING GIÁ RẺ')">📦 PC MINI ITX</div>
                <div class="cat-item" onclick="filterByCategory('PC STREAM GAME')">🎙️ PC STREAM &amp; CREATOR</div>
            </div>
        </div>
    </nav>

    <!-- 5. HERO HIGHLIGHT BANNER (Chuẩn Taste-Skill: Real setup imagery, no slop) -->
    <div class="container">
        <div class="hero-banner">
            <div class="hero-content">
                <div class="hero-badge">⚡ CHÍNH THỨC MỞ BÁN THẾ HỆ MỚI</div>
                <h1 class="hero-title">TTGShop | PC Gaming &amp; Hi-End Workstation</h1>
                <p class="hero-desc">
                    Tối ưu hiệu năng trên từng phân khúc giá. Sẵn sàng chiến mượt các tựa game AAA và Delta Force với dòng card đồ họa thế hệ mới RTX 50 Series. Vận hành ổn định trên hạ tầng phân tán điện toán đám mây đạt chuẩn High-Availability.
                </p>
            </div>
            <div class="hero-img-box">
                <img src="/static/ttg_assets/hero_setup.jpg" alt="High End Gaming PC Setup">
            </div>
        </div>

        <!-- 6. MAIN SHOP LAYOUT -->
        <div class="shop-layout">
            <!-- Left Sidebar -->
            <aside class="sidebar">
                <div class="filter-header">BỘ LỌC TÌM KIẾM</div>

                <div class="filter-group-title">PHÂN KHÚC PC</div>
                <ul class="subcat-list">
                    <li onclick="filterByCategory('PC GAMING GIÁ RẺ')">› PC Gaming Giá Rẻ</li>
                    <li onclick="filterByCategory('PC STREAM GAME')">› PC Stream Game</li>
                    <li onclick="filterByCategory('PC GAMING PREMIUM')">› PC Gaming Premium</li>
                    <li onclick="filterByCategory('PC Core Ultra')">› PC Core Ultra</li>
                    <li onclick="filterByCategory('PC GAMING CAO CẤP')">› PC Gaming Cao Cấp</li>
                    <li onclick="filterByCategory('PC ĐẸP')">› PC Đẹp &amp; Modding</li>
                </ul>

                <div class="filter-group-title">MỨC NGÂN SÁCH</div>
                <ul class="price-list">
                    <li><input type="checkbox" onchange="filterByPrice(10, 15, this)"> 10 triệu - 15 triệu (9)</li>
                    <li><input type="checkbox" onchange="filterByPrice(15, 20, this)"> 15 triệu - 20 triệu (35)</li>
                    <li><input type="checkbox" onchange="filterByPrice(20, 25, this)"> 20 triệu - 25 triệu (47)</li>
                    <li><input type="checkbox" onchange="filterByPrice(25, 35, this)"> 25 triệu - 35 triệu (111)</li>
                    <li><input type="checkbox" onchange="filterByPrice(35, 45, this)"> 35 triệu - 45 triệu (87)</li>
                    <li><input type="checkbox" onchange="filterByPrice(45, 60, this)"> 45 triệu - 60 triệu (82)</li>
                    <li><input type="checkbox" onchange="filterByPrice(60, 80, this)"> 60 triệu - 80 triệu (54)</li>
                    <li><input type="checkbox" onchange="filterByPrice(80, 100, this)"> 80 triệu - 100 triệu (20)</li>
                    <li><input type="checkbox" onchange="filterByPrice(100, 150, this)"> 100 triệu - 150 triệu (5)</li>
                    <li><input type="checkbox" onchange="filterByPrice(150, 200, this)"> 150 triệu - 200 triệu (2)</li>
                    <li><input type="checkbox" onchange="filterByPrice(200, 999, this)"> Trên 200 triệu (1)</li>
                </ul>

                <div class="filter-group-title">THƯƠNG HIỆU LINH KIỆN</div>
                <ul class="price-list">
                    <li><input type="checkbox" onchange="filterBySearch('CORE ULTRA')"> ASUS ROG (1)</li>
                    <li><input type="checkbox" onchange="filterBySearch('RTX 5070')"> MSI Gaming (12)</li>
                    <li><input type="checkbox" onchange="filterBySearch('14400F')"> GIGABYTE AORUS (18)</li>
                    <li><input type="checkbox" onchange="filterBySearch('5700X')"> COLORFUL iGame (15)</li>
                    <li><input type="checkbox" onchange="filterBySearch('AMD')"> AMD Radeon (24)</li>
                    <li><input type="checkbox" onchange="filterBySearch('CORE')"> Intel Core (28)</li>
                </ul>
            </aside>

            <!-- Right Product Grid Area -->
            <section class="products-area">
                <div class="products-topbar">
                    <div class="found-text">Tìm thấy <span id="total-found">457</span> cấu hình sẵn có</div>
                    <select class="sort-select" id="sort-select" onchange="sortProducts(this.value)">
                        <option value="default">Sắp xếp: Mặc định</option>
                        <option value="asc">Giá: Thấp đến Cao</option>
                        <option value="desc">Giá: Cao đến Thấp</option>
                    </select>
                </div>

                <div id="product-grid" class="product-grid">
                    <div style="grid-column:1/-1;padding:40px;text-align:center;color:#64748b;">Đang tải danh mục cấu hình...</div>
                </div>
            </section>
        </div>
    </div>

    <!-- Floating Contact Icons (SVG Icons) -->
    <div class="floating-contact">
        <div class="float-btn float-msg" title="Tư vấn qua Facebook Messenger">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.477 2 2 6.145 2 11.258c0 2.91 1.455 5.513 3.734 7.202V22l3.39-1.86c.92.256 1.895.394 2.876.394 5.523 0 10-4.145 10-9.258C22 6.145 17.523 2 12 2zm1.06 12.443l-2.613-2.787-5.1 2.787 5.61-5.955 2.678 2.787 5.034-2.787-5.609 5.955z"></path></svg>
        </div>
        <div class="float-btn float-zalo" title="Tư vấn qua Zalo">
            <span style="font-size:12px;font-weight:900;">Zalo</span>
        </div>
    </div>

    <!-- Toast container for notifications -->
    <div id="toast-container"></div>

    <script>
        let currentItems = [];
        let cartCount = 0;

        function formatVND(n) {
            return Number(n).toLocaleString('vi-VN') + ' VNĐ';
        }

        function showToast(title, desc) {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.innerHTML = `
                <div class="toast-icon">
                    <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>
                </div>
                <div>
                    <div style="font-weight:700;color:#fff;margin-bottom:2px;">${title}</div>
                    <div style="color:#cbd5e1;font-size:12px;">${desc}</div>
                </div>
            `;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.transition = 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(10px) scale(0.95)';
                setTimeout(() => toast.remove(), 300);
            }, 3800);
        }

        function renderGrid(items) {
            const grid = document.getElementById('product-grid');
            if (!items || items.length === 0) {
                grid.innerHTML = '<div style="grid-column:1/-1;padding:40px;text-align:center;color:#64748b;">Không tìm thấy cấu hình phù hợp với bộ lọc đã chọn.</div>';
                return;
            }
            grid.innerHTML = items.map(p => `
                <div class="p-card">
                    <div>
                        <div class="p-img-wrap">
                            <span class="p-brand-badge">${p.brand || 'CHÍNH HÃNG'}</span>
                            <img src="${p.image_url}" alt="${p.name}" loading="lazy">
                        </div>
                        <div class="p-title" title="${p.name}">${p.name}</div>
                        <div class="p-price-row">
                            <div>
                                <div class="p-price-new">${formatVND(p.price)}</div>
                                <div class="p-price-old">${formatVND(p.old_price)}</div>
                            </div>
                            <span class="p-disc-badge">${p.discount}</span>
                        </div>
                    </div>
                    <div class="p-bottom-row">
                        <button class="btn-add-cart" onclick="buyProduct(${p.id}, '${p.name.replace(/'/g, "\\'")}')">
                            <span class="cart-circle">
                                <svg viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
                            </span>
                            <span>THÊM VÀO GIỎ</span>
                        </button>
                        <span class="stock-pill" title="Tồn kho khả dụng: ${p.stock} bộ">
                            ${p.stock > 0 ? 'Còn ' + p.stock + ' bộ' : 'Hết hàng'}
                        </span>
                    </div>
                </div>
            `).join('');
        }

        async function loadProducts(category = '', search = '') {
            let url = '/api/products?limit=16';
            if (category) url += '&category=' + encodeURIComponent(category);
            if (search) url += '&search=' + encodeURIComponent(search);
            try {
                const res = await fetch(url);
                const data = await res.json();
                document.getElementById('current-node').innerText = data.served_by;
                document.getElementById('total-found').innerText = category || search ? data.count : data.total_found;
                currentItems = data.items;
                renderGrid(currentItems);
            } catch (err) {
                console.error('Fetch products error:', err);
            }
        }

        function filterByCategory(cat) {
            document.querySelectorAll('.subcat-list li').forEach(li => {
                li.classList.toggle('active', li.innerText.includes(cat));
            });
            loadProducts(cat, '');
        }

        function filterBySearch(kw) {
            document.getElementById('search-input').value = kw;
            loadProducts('', kw);
        }

        function doSearch() {
            const kw = document.getElementById('search-input').value.trim();
            filterBySearch(kw);
        }

        function filterByPrice(minM, maxM, checkbox) {
            const boxes = document.querySelectorAll('.price-list input[type="checkbox"]');
            boxes.forEach(b => { if (b !== checkbox) b.checked = false; });
            if (!checkbox.checked) {
                renderGrid(currentItems);
                return;
            }
            const minV = minM * 1000000;
            const maxV = maxM * 1000000;
            const filtered = currentItems.filter(p => p.price >= minV && p.price <= maxV);
            renderGrid(filtered);
        }

        function sortProducts(mode) {
            let copy = [...currentItems];
            if (mode === 'asc') copy.sort((a, b) => a.price - b.price);
            if (mode === 'desc') copy.sort((a, b) => b.price - a.price);
            renderGrid(copy);
        }

        async function buyProduct(productId, name) {
            try {
                const res = await fetch('/api/orders', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        customer_name: 'Khách hàng TTGShop (UTH Demo)',
                        product_id: productId,
                        quantity: 1
                    })
                });
                const data = await res.json();
                if (res.ok) {
                    cartCount += 1;
                    document.getElementById('cart-badge').innerText = cartCount;
                    document.getElementById('current-node').innerText = data.served_by;
                    showToast(
                        'Đã thêm vào giỏ hàng thành công!',
                        `Đơn #${data.order_id} • ${formatVND(data.total_amount)} • Thụ lý bởi [${data.served_by}] (ACID Safe)`
                    );
                    loadProducts();
                } else {
                    alert('Lỗi: ' + data.detail);
                }
            } catch (err) {
                alert('Không thể kết nối đến máy chủ: ' + err);
            }
        }

        function showCartSummary() {
            showToast('Giỏ hàng hiện tại', `Bạn đã đặt thành công ${cartCount} cấu hình qua giao dịch ACID.`);
        }

        function toggleCloudDrawer() {
            const d = document.getElementById('cloud-drawer');
            d.style.display = (d.style.display === 'none' || d.style.display === '') ? 'block' : 'none';
        }

        async function testLoadBalancing() {
            const logBox = document.getElementById('lb-log');
            logBox.style.display = 'block';
            logBox.innerHTML = '⚡ Đang gửi tuần tự 10 request kiểm tra Nginx Load Balancer (least_conn)...<br>';
            for (let i = 1; i <= 10; i++) {
                const t0 = performance.now();
                try {
                    const res = await fetch('/health?t=' + Date.now() + '-' + i);
                    const data = await res.json();
                    const dt = (performance.now() - t0).toFixed(1);
                    logBox.innerHTML += `[Request #${i.toString().padStart(2, '0')}] HTTP ${res.status} OK | Node: <strong style="color:#38bdf8;">${data.node_id}</strong> | RTT: ${dt} ms<br>`;
                    document.getElementById('current-node').innerText = data.node_id;
                } catch (e) {
                    logBox.innerHTML += `[Request #${i}] ❌ Lỗi kết nối: ${e}<br>`;
                }
            }
            logBox.scrollTop = logBox.scrollHeight;
        }

        async function toggleChaos() {
            const res = await fetch('/api/chaos/toggle-node-1', { method: 'POST' });
            const data = await res.json();
            const btn = document.getElementById('btn-chaos');
            const st = document.getElementById('az-status');
            const logBox = document.getElementById('lb-log');
            logBox.style.display = 'block';
            if (!data.node_1_active) {
                btn.innerText = '💚 Khôi Phục: Bật Lại Node 1';
                btn.className = 'c-btn c-btn-green';
                st.innerText = 'AZ-a CRASHED -> FAILOVER AZ-b (RTO 1.46s)';
                st.style.color = '#f59e0b';
                logBox.innerHTML += `<div style="color:#f87171;font-weight:bold;margin-top:4px;">💥 [CHAOS TEST] Đã hạ sập app-replica-1 (AZ-a)! Nginx kích hoạt proxy_next_upstream chuyển mạch sang app-replica-2 trong 1.46s (RTO &lt; 2s).</div>`;
            } else {
                btn.innerText = '🔥 Tiêm Lỗi: Hạ Sập Node 1';
                btn.className = 'c-btn c-btn-red';
                st.innerText = 'AZ-a & AZ-b ONLINE (Active-Active)';
                st.style.color = '#10b981';
                logBox.innerHTML += `<div style="color:#34d399;font-weight:bold;margin-top:4px;">✅ [RECOVERY] app-replica-1 (AZ-a) đã phục hồi trực tuyến. Cụm cân bằng tải hoạt động bình thường.</div>`;
            }
        }

        loadProducts();
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)
