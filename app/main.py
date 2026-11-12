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

try:
    from app.checkout_api import router as checkout_router
except ImportError:
    from checkout_api import router as checkout_router

try:
    from app.shopee_template import render_shopee_store_html
except ImportError:
    from shopee_template import render_shopee_store_html

try:
    from app.apple_template import render_apple_store_html
except ImportError:
    from apple_template import render_apple_store_html

app.include_router(checkout_router)


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
    return HTMLResponse(content=render_shopee_store_html(node=node, arch_version=ARCH_VERSION))


@app.get("/apple", response_class=HTMLResponse)
def apple_index_page(request: Request):
    node = getattr(request.state, "served_by", resolve_serving_node())
    return HTMLResponse(content=render_apple_store_html(node=node, arch_version=ARCH_VERSION))
