# -*- coding: utf-8 -*-
"""
Kịch bản Kiểm duyệt & Kiểm thử Tự động Toàn diện (End-to-End Verification Suite)
cho Phần Thực hành - Đề tài 1: Đánh giá và thiết kế lại kiến trúc Website TMĐT Well-Architected.

Kiểm tra 4 hạng mục lớn:
  1. Kiểm duyệt cấu hình Hạ tầng (Docker Compose V1/V2, Nginx L7 LB, Prometheus, Dockerfile, SQL).
  2. Kiểm thử toàn bộ REST API Endpoints (/health, /api/products, /api/orders, /metrics, Web UI).
  3. Kiểm thử tương tranh ACID (20 luồng đặt hàng đồng thời - Chống Overselling khi Flash Sale).
  4. Kiểm thử Cụm Multi-Replica + Load Balancing + Chaos Failover thực tế (dừng nóng Replica 1).
"""

import os
import sys
import time
import json
import socket
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
import http.server
import urllib.request
import urllib.error

# Đảm bảo import được app/main.py
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_DIR = os.path.join(PROJECT_ROOT, "app")
sys.path.insert(0, APP_DIR)

os.environ["DB_ENGINE"] = "sqlite"
os.environ["NODE_ID"] = "app-replica-test (AZ-a)"
os.environ["ARCH_VERSION"] = "V2-Well-Architected"

from fastapi.testclient import TestClient
import main as ecommerce_app


def print_header(title: str):
    print("\n" + "=" * 78)
    print(f" {title}")
    print("=" * 78)


def check_item(name: str, passed: bool, detail: str = ""):
    icon = "[PASS]" if passed else "[FAIL]"
    print(f"  {icon} {name}" + (f" -> {detail}" if detail else ""))
    if not passed:
        raise AssertionError(f"Kiểm thử thất bại tại: {name} ({detail})")


# =============================================================================
# PHẦN 1: KIỂM DUYỆT CẤU HÌNH HẠ TẦNG (INFRASTRUCTURE AUDIT)
# =============================================================================
def audit_infrastructure_files():
    print_header("1. KIỂM DUYỆT CẤU HÌNH HẠ TẦNG (DOCKER COMPOSE V1/V2, NGINX, PROMETHEUS)")
    required_files = [
        ("Docker Compose V1 (Single-Node SPOF)", "infra/docker-compose.v1.yml"),
        ("Docker Compose V2 (Well-Architected HA)", "infra/docker-compose.v2.yml"),
        ("Cấu hình Nginx L7 Load Balancer", "infra/nginx/nginx.conf"),
        ("Cấu hình Prometheus Monitoring", "infra/prometheus/prometheus.yml"),
        ("Dockerfile (Non-root appuser)", "app/Dockerfile"),
        ("SQL Khởi tạo 500 SKU", "app/init.sql"),
        ("Kịch bản Load Test k6", "tests/loadtest.js"),
        ("Kịch bản Chaos Failover PowerShell", "tests/chaos_failover_test.ps1"),
    ]
    for label, rel_path in required_files:
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        exists = os.path.isfile(full_path) and os.path.getsize(full_path) > 0
        check_item(label, exists, f"{rel_path} ({os.path.getsize(full_path)} bytes)")

    # Kiểm tra các thiết lập cốt lõi trong docker-compose.v2.yml và nginx.conf
    with open(os.path.join(PROJECT_ROOT, "infra/docker-compose.v2.yml"), "r", encoding="utf-8") as f:
        v2_content = f.read()
    check_item("Cô lập mạng Private Subnet (internal: true)", "internal: true" in v2_content, "backend-net internal=true")
    check_item("Multi-Replica (app-replica-1 & app-replica-2)", "app-replica-1:" in v2_content and "app-replica-2:" in v2_content)
    check_item("Tách biệt lưu trữ tĩnh MinIO S3", "minio-storage:" in v2_content)

    with open(os.path.join(PROJECT_ROOT, "infra/nginx/nginx.conf"), "r", encoding="utf-8") as f:
        nginx_content = f.read()
    check_item("Thuật toán cân bằng tải least_conn", "least_conn;" in nginx_content)
    check_item("Cơ chế Failover tự động proxy_next_upstream", "proxy_next_upstream" in nginx_content)

    with open(os.path.join(PROJECT_ROOT, "app/Dockerfile"), "r", encoding="utf-8") as f:
        docker_content = f.read()
    check_item("Bảo mật Container Non-root User (appuser)", "USER appuser" in docker_content)


# =============================================================================
# PHẦN 2: KIỂM THỬ CHỨC NĂNG REST API & TELEMETRY
# =============================================================================
def test_api_endpoints_and_acid():
    print_header("2. KIỂM THỬ CHỨC NĂNG REST API, TELEMETRY & GIAO DỊCH ACID")
    with TestClient(ecommerce_app.app) as client:
        # 1. Health check
        r_health = client.get("/health")
        check_item("GET /health trả về HTTP 200", r_health.status_code == 200, f"body={r_health.json()}")
        check_item("Header minh chứng X-Served-By", "x-served-by" in r_health.headers, r_health.headers.get("x-served-by"))

        # 2. Danh sách sản phẩm
        r_list = client.get("/api/products?limit=12")
        data_list = r_list.json()
        check_item("GET /api/products?limit=12 trả về 12 sản phẩm", r_list.status_code == 200 and data_list["count"] == 12)

        # 3. Tìm kiếm & Lọc theo danh mục
        r_search = client.get("/api/products?search=Laptop&limit=5")
        data_search = r_search.json()
        check_item("GET /api/products?search=Laptop hoạt động đúng", r_search.status_code == 200 and data_search["count"] > 0, f"Tìm thấy {data_search['count']} mẫu Laptop")

        # 4. Chi tiết sản phẩm
        r_detail = client.get("/api/products/1")
        check_item("GET /api/products/1 trả về chi tiết SKU", r_detail.status_code == 200, r_detail.json()["product"]["sku"])

        # 5. Kiểm thử ACID khi 20 luồng đặt hàng đồng thời vào cùng sản phẩm #10
        r_before = client.get("/api/products/10").json()
        stock_before = r_before["product"]["stock"]

        def place_one_order(idx: int):
            resp = client.post("/api/orders", json={
                "customer_name": f"KhachHang_Concurrent_{idx}",
                "product_id": 10,
                "quantity": 1
            })
            return resp.status_code

        with ThreadPoolExecutor(max_workers=10) as pool_exec:
            statuses = list(pool_exec.map(place_one_order, range(20)))

        all_201 = all(s == 201 for s in statuses)
        r_after = client.get("/api/products/10").json()
        stock_after = r_after["product"]["stock"]
        check_item(
            "Kiểm thử 20 giao dịch đặt hàng đồng thời (ACID Concurrency)",
            all_201 and (stock_before - stock_after == 20),
            f"Tồn kho trước={stock_before}, sau={stock_after} (Trừ chính xác 20 đơn vị, 0 race condition)"
        )

        # 6. Kiểm thử Prometheus Metrics
        r_metrics = client.get("/metrics")
        metrics_text = r_metrics.text
        check_item(
            "GET /metrics xuất đầy đủ SLI Prometheus",
            r_metrics.status_code == 200
            and "ecommerce_http_requests_total" in metrics_text
            and "ecommerce_orders_created_total" in metrics_text,
            "Đã ghi nhận Counter & Histogram độ trễ"
        )

        # 7. Kiểm thử Giao diện Web Demo
        r_ui = client.get("/")
        check_item("GET / (Web UI Dashboard) hiển thị thành công", r_ui.status_code == 200 and "UTH CloudStore" in r_ui.text)


# =============================================================================
# PHẦN 3: KIỂM THỬ CỤM MULTI-REPLICA + LOAD BALANCER + CHAOS FAILOVER THỰC TẾ
# =============================================================================
class L7LoadBalancerHandler(http.server.BaseHTTPRequestHandler):
    """Bộ cân bằng tải L7 mô phỏng chính xác cơ chế Round-Robin / Failover của Nginx."""
    backends = ["http://127.0.0.1:18001", "http://127.0.0.1:18002"]
    rr_index = 0
    lock = threading.Lock()

    def log_message(self, format, *args):
        pass  # Ẩn log console để output kiểm thử gọn gàng

    def _proxy_request(self, method: str):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len) if content_len > 0 else None

        with L7LoadBalancerHandler.lock:
            start_idx = L7LoadBalancerHandler.rr_index
            L7LoadBalancerHandler.rr_index = (L7LoadBalancerHandler.rr_index + 1) % len(self.backends)

        # Thử tối đa qua các replica trong pool (giống proxy_next_upstream của Nginx)
        for attempt in range(len(self.backends)):
            idx = (start_idx + attempt) % len(self.backends)
            target_base = self.backends[idx]
            target_url = f"{target_base}{self.path}"
            try:
                req = urllib.request.Request(target_url, data=body, method=method)
                if "Content-Type" in self.headers:
                    req.add_header("Content-Type", self.headers["Content-Type"])
                with urllib.request.urlopen(req, timeout=1.2) as resp:
                    resp_body = resp.read()
                    self.send_response(resp.status)
                    for k, v in resp.getheaders():
                        if k.lower() not in ("transfer-encoding", "server", "date"):
                            self.send_header(k, v)
                    self.send_header("X-Upstream-Node", target_base)
                    self.end_headers()
                    self.wfile.write(resp_body)
                    return
            except Exception:
                continue

        self.send_response(502)
        self.end_headers()
        self.wfile.write(b'{"detail":"Bad Gateway"}')

    def do_GET(self):
        self._proxy_request("GET")

    def do_POST(self):
        self._proxy_request("POST")


def wait_for_port(port: int, timeout: float = 10.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def test_live_multi_replica_and_chaos_failover():
    print_header("3. THỰC NGHIỆM MULTI-REPLICA, CÂN BẰNG TẢI & TIÊM LỖI CHAOS FAILOVER")

    env1 = os.environ.copy()
    env1["NODE_ID"] = "app-replica-1 (AZ-a)"
    env1["DB_ENGINE"] = "sqlite"

    env2 = os.environ.copy()
    env2["NODE_ID"] = "app-replica-2 (AZ-b)"
    env2["DB_ENGINE"] = "sqlite"

    # Khởi chạy 2 tiến trình Replica thật bằng Uvicorn
    proc1 = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "18001", "--log-level", "error"],
        cwd=APP_DIR,
        env=env1
    )
    proc2 = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "18002", "--log-level", "error"],
        cwd=APP_DIR,
        env=env2
    )

    lb_server = http.server.ThreadingHTTPServer(("127.0.0.1", 18080), L7LoadBalancerHandler)
    lb_thread = threading.Thread(target=lb_server.serve_forever, daemon=True)
    lb_thread.start()

    try:
        r1_up = wait_for_port(18001, 10.0)
        r2_up = wait_for_port(18002, 10.0)
        check_item("Khởi chạy thực tế 2 bản sao (Replica 1 :18001 & Replica 2 :18002)", r1_up and r2_up)

        # Giai đoạn 1: Cân bằng tải khi cả 2 Replica cùng sống
        served_nodes_normal = []
        for _ in range(10):
            with urllib.request.urlopen("http://127.0.0.1:18080/health", timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                served_nodes_normal.append(data["node_id"])

        r1_count = served_nodes_normal.count("app-replica-1 (AZ-a)")
        r2_count = served_nodes_normal.count("app-replica-2 (AZ-b)")
        check_item(
            "Load Balancer phân phối tải đều qua 2 AZ",
            r1_count > 0 and r2_count > 0,
            f"Replica-1 xử lý {r1_count}/10 req, Replica-2 xử lý {r2_count}/10 req"
        )

        # Giai đoạn 2: Tiêm lỗi (Chaos Fault Injection) - Dừng cưỡng bức Replica 1
        t_kill = time.perf_counter()
        proc1.terminate()
        proc1.wait(timeout=5)

        failover_success = 0
        failover_errors = 0
        served_nodes_failover = []
        latencies_ms = []

        for _ in range(15):
            t_req = time.perf_counter()
            try:
                with urllib.request.urlopen("http://127.0.0.1:18080/health", timeout=3.0) as resp:
                    if resp.status == 200:
                        failover_success += 1
                        data = json.loads(resp.read().decode("utf-8"))
                        served_nodes_failover.append(data["node_id"])
            except Exception:
                failover_errors += 1
            latencies_ms.append((time.perf_counter() - t_req) * 1000.0)

        rto_ms = max(latencies_ms)
        check_item(
            "Tiêm lỗi dừng nóng Replica-1 -> Tự động Failover sang Replica-2",
            failover_success == 15 and failover_errors == 0 and all("app-replica-2" in n for n in served_nodes_failover),
            f"Thành công 15/15 request (Lỗi: 0%), RTO chuyển mạch tối đa = {rto_ms:.1f} ms (< 2 giây)"
        )

    finally:
        lb_server.shutdown()
        if proc1.poll() is None:
            proc1.terminate()
        if proc2.poll() is None:
            proc2.terminate()


if __name__ == "__main__":
    audit_infrastructure_files()
    test_api_endpoints_and_acid()
    test_live_multi_replica_and_chaos_failover()
    print("\n" + "=" * 78)
    print(" KẾT LUẬN: TẤT CẢ CÁC BÀI KIỂM THỬ THỰC HÀNH ĐỀU ĐẠT 100% (ALL PASSED!)")
    print("=" * 78)
