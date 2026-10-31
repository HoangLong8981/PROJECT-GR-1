import os
import time
import socket
from contextlib import asynccontextmanager
from typing import Optional

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# =============================================================================
# CẤU HÌNH MÔI TRƯỜNG (STATELESS CONFIGURATION - TWELVE-FACTOR APP)
# =============================================================================
NODE_ID = os.getenv("NODE_ID", socket.gethostname())
ARCH_VERSION = os.getenv("ARCH_VERSION", "V2-Well-Architected")
STORAGE_MODE = os.getenv("STORAGE_MODE", "minio-s3")
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", "http://localhost:9000")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "product-images")

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "ecommerce_db")
DB_USER = os.getenv("POSTGRES_USER", "ecom_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "ChangeMe_StrongPassword_2026!")
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "2"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "20"))

# =============================================================================
# CHỈ SỐ ĐO LƯỜNG PROMETHEUS (SLI TELEMETRY)
# =============================================================================
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

db_pool: Optional[pool.ThreadedConnectionPool] = None


def init_db_pool():
    global db_pool
    for attempt in range(10):
        try:
            db_pool = pool.ThreadedConnectionPool(
                minconn=DB_POOL_MIN,
                maxconn=DB_POOL_MAX,
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                connect_timeout=3
            )
            DB_HEALTH_GAUGE.labels(node_id=NODE_ID).set(1)
            return
        except Exception as e:
            print(f"[{NODE_ID}] Đang chờ kết nối PostgreSQL ({attempt + 1}/10): {e}")
            time.sleep(2)
    DB_HEALTH_GAUGE.labels(node_id=NODE_ID).set(0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_pool()
    yield
    if db_pool:
        db_pool.closeall()


app = FastAPI(
    title="UTH Cloud E-Commerce Well-Architected Prototype",
    version="2.0.0",
    lifespan=lifespan
)


# =============================================================================
# MIDDLEWARE GHI NHẬN ĐỘ TRỄ & HEADER MINH CHỨNG NODE XỬ LÝ
# =============================================================================
@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    path = request.url.path
    method = request.method

    try:
        response: Response = await call_next(request)
        status_code = response.status_code
    except Exception:
        status_code = 500
        raise
    finally:
        elapsed = time.perf_counter() - start_time
        if path not in ("/metrics", "/favicon.ico"):
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                http_status=str(status_code),
                node_id=NODE_ID
            ).inc()
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=path,
                node_id=NODE_ID
            ).observe(elapsed)

    response.headers["X-Served-By"] = NODE_ID
    response.headers["X-Arch-Version"] = ARCH_VERSION
    response.headers["X-Response-Time-Ms"] = f"{elapsed * 1000:.2f}"
    return response


# =============================================================================
# MODELS DỮ LIỆU
# =============================================================================
class OrderCreateRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=120, examples=["Nguyễn Văn A"])
    product_id: int = Field(..., gt=0, examples=[1])
    quantity: int = Field(default=1, gt=0, le=20, examples=[1])


# =============================================================================
# ENDPOINT KIỂM TRA SỨC KHỎE (HEALTH CHECK CHO LOAD BALANCER)
# =============================================================================
@app.get("/health")
def health_check():
    if not db_pool:
        DB_HEALTH_GAUGE.labels(node_id=NODE_ID).set(0)
        raise HTTPException(status_code=503, detail="Database pool not initialized")

    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
        DB_HEALTH_GAUGE.labels(node_id=NODE_ID).set(1)
        return {
            "status": "healthy",
            "node_id": NODE_ID,
            "architecture": ARCH_VERSION,
            "storage_mode": STORAGE_MODE,
            "database": "connected"
        }
    except Exception as e:
        DB_HEALTH_GAUGE.labels(node_id=NODE_ID).set(0)
        raise HTTPException(status_code=503, detail=f"Database healthcheck failed: {str(e)}")
    finally:
        if conn:
            db_pool.putconn(conn)


# =============================================================================
# ENDPOINT DANH SÁCH SẢN PHẨM & CHI TIẾT SẢN PHẨM (READ WORKLOAD)
# =============================================================================
@app.get("/api/products")
def list_products(limit: int = 12, category: Optional[str] = None):
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database unavailable")

    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if category:
                cur.execute(
                    "SELECT id, sku, name, category, price, stock, image_key "
                    "FROM products WHERE category = %s ORDER BY id LIMIT %s;",
                    (category, limit)
                )
            else:
                cur.execute(
                    "SELECT id, sku, name, category, price, stock, image_key "
                    "FROM products ORDER BY id LIMIT %s;",
                    (limit,)
                )
            rows = cur.fetchall()

        products = []
        for r in rows:
            item = dict(r)
            item["price"] = float(item["price"])
            item["image_url"] = f"{MINIO_PUBLIC_URL}/{MINIO_BUCKET}/{item['image_key']}"
            products.append(item)

        return {
            "served_by": NODE_ID,
            "architecture": ARCH_VERSION,
            "storage_mode": STORAGE_MODE,
            "count": len(products),
            "items": products
        }
    finally:
        if conn:
            db_pool.putconn(conn)


@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database unavailable")

    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, sku, name, category, price, stock, image_key "
                "FROM products WHERE id = %s;",
                (product_id,)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
            item = dict(row)
            item["price"] = float(item["price"])
            item["image_url"] = f"{MINIO_PUBLIC_URL}/{MINIO_BUCKET}/{item['image_key']}"
            return {
                "served_by": NODE_ID,
                "architecture": ARCH_VERSION,
                "product": item
            }
    finally:
        if conn:
            db_pool.putconn(conn)


# =============================================================================
# ENDPOINT ĐẶT HÀNG GIAO DỊCH ACID (WRITE WORKLOAD)
# =============================================================================
@app.post("/api/orders", status_code=201)
def create_order(payload: OrderCreateRequest):
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database unavailable")

    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Khóa dòng sản phẩm để đảm bảo tính nhất quán ACID khi Flash Sale
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

            cur.execute(
                "UPDATE products SET stock = stock - %s WHERE id = %s;",
                (payload.quantity, payload.product_id)
            )
            cur.execute(
                "INSERT INTO orders (customer_name, product_id, quantity, total_amount, served_by_node) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at;",
                (payload.customer_name, payload.product_id, payload.quantity, total_amount, NODE_ID)
            )
            order_row = cur.fetchone()
            conn.commit()

        ORDERS_CREATED.labels(node_id=NODE_ID).inc()
        return {
            "message": "Đặt hàng thành công",
            "order_id": order_row["id"],
            "customer_name": payload.customer_name,
            "product_name": product["name"],
            "quantity": payload.quantity,
            "total_amount": total_amount,
            "served_by": NODE_ID,
            "architecture": ARCH_VERSION,
            "created_at": str(order_row["created_at"])
        }
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi giao dịch đặt hàng: {str(e)}")
    finally:
        if conn:
            db_pool.putconn(conn)


# =============================================================================
# ENDPOINT XUẤT METRICS PROMETHEUS
# =============================================================================
@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# =============================================================================
# GIAO DIỆN WEB TRỰC QUAN PHỤC VỤ DEMO & KIỂM CHỨNG CÂN BẰNG TẢI / FAILOVER
# =============================================================================
@app.get("/", response_class=HTMLResponse)
def index_page():
    html_content = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>UTH Cloud E-Commerce - Well-Architected Demo</title>
        <style>
            :root {{
                --primary: #003366;
                --secondary: #006699;
                --success: #15803d;
                --bg: #f8fafc;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                background: var(--bg);
                color: #1e293b;
            }}
            header {{
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                color: white;
                padding: 20px 32px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            .badge {{
                background: rgba(255,255,255,0.18);
                border: 1px solid rgba(255,255,255,0.4);
                padding: 8px 14px;
                border-radius: 8px;
                font-size: 14px;
            }}
            .container {{
                max-width: 1150px;
                margin: 24px auto;
                padding: 0 20px;
            }}
            .panel {{
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 24px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                border-left: 5px solid var(--secondary);
            }}
            .btn {{
                background: var(--primary);
                color: white;
                border: none;
                padding: 10px 18px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
            }}
            .btn:hover {{ opacity: 0.92; }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 18px;
            }}
            .card {{
                background: white;
                border-radius: 10px;
                padding: 18px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                border: 1px solid #e2e8f0;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}
            .price {{
                color: #b91c1c;
                font-size: 18px;
                font-weight: bold;
                margin: 8px 0;
            }}
            #lb-log {{
                margin-top: 12px;
                font-family: monospace;
                background: #0f172a;
                color: #38bdf8;
                padding: 12px;
                border-radius: 6px;
                max-height: 160px;
                overflow-y: auto;
                display: none;
            }}
        </style>
    </head>
    <body>
        <header>
            <div>
                <h2 style="margin:0;">☁️ UTH CloudStore — Đề tài 1: Well-Architected Framework</h2>
                <small>Kiến trúc Website Thương mại điện tử 3 tầng có Cân bằng tải & Chịu lỗi</small>
            </div>
            <div class="badge">
                <div><strong>Phiên bản:</strong> {ARCH_VERSION}</div>
                <div><strong>Node phản hồi:</strong> <span id="current-node">{NODE_ID}</span></div>
                <div><strong>Lưu trữ ảnh:</strong> {STORAGE_MODE}</div>
            </div>
        </header>

        <div class="container">
            <div class="panel">
                <h3 style="margin-top:0;">🔍 Bảng điều khiển Kiểm chứng Cân bằng tải & Chuyển đổi dự phòng (Failover)</h3>
                <p>Nhấn nút bên dưới để gửi liên tiếp 10 yêu cầu vào hệ thống và quan sát Load Balancer phân phối tải qua các bản sao (Replicas), hoặc thử tắt 1 container để kiểm chứng tính sẵn sàng cao:</p>
                <button class="btn" onclick="testLoadBalancing()">⚡ Bắn 10 Request kiểm tra Load Balancer</button>
                <div id="lb-log"></div>
            </div>

            <h3>🛒 Danh mục Sản phẩm Thương mại điện tử (Từ PostgreSQL & Object Storage)</h3>
            <div id="product-grid" class="grid">Đang tải dữ liệu sản phẩm...</div>
        </div>

        <script>
            async function loadProducts() {{
                const res = await fetch('/api/products?limit=8');
                const data = await res.json();
                document.getElementById('current-node').innerText = data.served_by;
                const grid = document.getElementById('product-grid');
                grid.innerHTML = data.items.map(p => `
                    <div class="card">
                        <div>
                            <small style="color:#64748b;">${{p.sku}} | ${{p.category}}</small>
                            <h4 style="margin:6px 0;">${{p.name}}</h4>
                            <div class="price">${{p.price.toLocaleString('vi-VN')}} VNĐ</div>
                            <small>Tồn kho: <strong>${{p.stock}}</strong></small>
                        </div>
                        <button class="btn" style="margin-top:12px;" onclick="buyProduct(${{p.id}}, '${{p.name}}')">
                            Mua ngay (Tạo đơn ACID)
                        </button>
                    </div>
                `).join('');
            }}

            async function buyProduct(productId, name) {{
                const res = await fetch('/api/orders', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        customer_name: 'Sinh viên UTH Demo',
                        product_id: productId,
                        quantity: 1
                    }})
                }});
                const data = await res.json();
                if (res.ok) {{
                    alert(`✅ Đặt hàng thành công!\\nMã đơn: #${{data.order_id}}\\nSản phẩm: ${{name}}\\nXử lý bởi Node: ${{data.served_by}}`);
                    loadProducts();
                }} else {{
                    alert(`❌ Lỗi: ${{data.detail}}`);
                }}
            }}

            async function testLoadBalancing() {{
                const logBox = document.getElementById('lb-log');
                logBox.style.display = 'block';
                logBox.innerHTML = 'Đang gửi 10 request liên tiếp tới /health...<br>';
                for (let i = 1; i <= 10; i++) {{
                    const t0 = performance.now();
                    try {{
                        const res = await fetch('/health?t=' + Date.now());
                        const data = await res.json();
                        const dt = (performance.now() - t0).toFixed(1);
                        logBox.innerHTML += `[Request #${{i}}] Status: ${{res.status}} | Node: <b>${{data.node_id}}</b> | Độ trễ: ${{dt}} ms<br>`;
                    }} catch (e) {{
                        logBox.innerHTML += `[Request #${{i}}] ❌ LỖI KẾT NỐI: ${{e}}<br>`;
                    }}
                }}
            }}

            loadProducts();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
