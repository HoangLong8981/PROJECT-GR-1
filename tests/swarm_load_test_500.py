#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
🍎 TTGShop Apple Store Edition — Swarm Load Test & ACID Verifier (500 Reqs)
Owned by: Worker 3 (@load-qa)
File: tests/swarm_load_test_500.py
================================================================================

MỤC TIÊU KIỂM THỬ (TEST OBJECTIVES):
1. Mô phỏng đột biến lưu lượng Flash Sale gồm **500 concurrent requests**:
   - 400 requests đọc nhanh (Catalog `GET /api/products`, Chi tiết `GET /api/products/{id}`,
     So sánh cấu hình Apple Store `GET /api/lineup/compare`, Health `GET /health`,
     Đơn hàng gần nhất `GET /api/orders/recent`, Swarm Telemetry `GET /api/swarm/telemetry`).
   - 100 giao dịch đặt hàng ACID đồng thời (`POST /api/checkout` & `POST /api/orders`)
     trên 8 dòng Flagship PC Gaming (`TTG-PC-0001` .. `TTG-PC-0008`), kiểm thử mã giảm giá
     `APPLE2026` (-1.500.000đ), `UTH2026` (-1.000.000đ), `TTG500K` (-500.000đ) cùng
     phương thức thanh toán `Apple Pay` và `Chuyển khoản VietQR 24/7`.
2. Chạy độc lập (Out-of-the-Box) bằng thư viện chuẩn Python (`concurrent.futures.ThreadPoolExecutor`
   và `urllib.request`), KHÔNG yêu cầu cài đặt thêm gói pip bên ngoài.
3. Đo lường và in bảng báo cáo kỹ thuật song ngữ Việt - Anh:
   - Tổng số request (500), Tỷ lệ thành công (%), Số lỗi HTTP 5xx
   - Thông lượng (Throughput req/s), Độ trễ P50 / P95 / P99 (ms)
   - Phân bổ tải qua các nhánh `app-replica-1 (AZ-a)` và `app-replica-2 (AZ-b)`
   - Kiểm định toàn vẹn tồn kho ACID (ACID Stock Integrity Check):
     Xác minh `stock_before - successful_orders == stock_after` và đảm bảo
     KHÔNG bán âm kho (`Zero Overselling`, `min_stock >= 0`).

CÁCH CHẠY TRỰC TIẾP (STANDALONE PYTHON):
    python tests/swarm_load_test_500.py
    python tests/swarm_load_test_500.py --url http://localhost:8000 --workers 50
    python tests/swarm_load_test_500.py --show-profiles

================================================================================
OPTIONAL PROFILE 1: LOCUST LOAD PROFILE (`locustfile.py` — `pip install locust`)
    locust -f tests/swarm_load_test_500.py --headless -u 100 -r 25 -t 30s --host http://localhost:8000
--------------------------------------------------------------------------------
from locust import HttpUser, task, between
import random

class TTGShopFlashSaleUser(HttpUser):
    wait_time = between(0.05, 0.25)

    @task(5)
    def browse_catalog(self):
        self.client.get("/api/products?limit=12", name="GET /api/products")

    @task(2)
    def view_flagship_detail(self):
        pid = random.randint(1, 8)
        self.client.get(f"/api/products/{pid}", name="GET /api/products/{id}")

    @task(2)
    def compare_apple_lineup(self):
        self.client.get("/api/lineup/compare", name="GET /api/lineup/compare")

    @task(1)
    def check_health_and_recent_orders(self):
        self.client.get("/health", name="GET /health")
        self.client.get("/api/orders/recent?limit=10", name="GET /api/orders/recent")
        self.client.get("/api/swarm/telemetry", name="GET /api/swarm/telemetry")

    @task(2)
    def place_acid_checkout(self):
        pid = random.randint(1, 8)
        promo = random.choice(["APPLE2026", "UTH2026", "TTG500K"])
        payment = random.choice(["Apple Pay", "Chuyển khoản VietQR 24/7"])
        payload = {
            "customer_name": f"Locust_FlashSale_User_{random.randint(1000, 9999)}",
            "phone": "0909123456",
            "address": "268 Lý Thường Kiệt, Quận 10, TP.HCM",
            "payment_method": payment,
            "promo_code": promo,
            "items": [{"product_id": pid, "quantity": 1}],
        }
        self.client.post("/api/checkout", json=payload, name="POST /api/checkout")

================================================================================
OPTIONAL PROFILE 2: GRAFANA K6 FLASH SALE PROFILE (`k6_script.js` — `k6 run`)
--------------------------------------------------------------------------------
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    flash_sale_500_burst: {
      executor: 'shared-iterations',
      vus: 50,
      iterations: 500,
      maxDuration: '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(50)<50', 'p(95)<250', 'p(99)<500'],
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8000';
const PROMOS = ['APPLE2026', 'UTH2026', 'TTG500K'];
const PAYMENTS = ['Apple Pay', 'Chuyển khoản VietQR 24/7'];

export default function () {
  if (__ITER % 5 === 0) {
    const pid = (__ITER % 8) + 1;
    const payload = JSON.stringify({
      customer_name: `k6_Buyer_${__VU}_${__ITER}`,
      phone: '0909888777',
      address: 'TP. Hồ Chí Minh',
      payment_method: PAYMENTS[__ITER % PAYMENTS.length],
      promo_code: PROMOS[__ITER % PROMOS.length],
      items: [{ product_id: pid, quantity: 1 }],
    });
    const res = http.post(`${BASE_URL}/api/checkout`, payload, {
      headers: { 'Content-Type': 'application/json' },
    });
    check(res, { 'ACID Checkout 201/400': (r) => r.status === 201 || r.status === 400 });
  } else if (__ITER % 5 === 1) {
    const res = http.get(`${BASE_URL}/api/lineup/compare`);
    check(res, { 'Lineup Compare 200 OK': (r) => r.status === 200 });
  } else {
    const res = http.get(`${BASE_URL}/api/products?limit=12`);
    check(res, { 'Catalog 200 OK': (r) => r.status === 200 });
  }
}
================================================================================
"""

import argparse
import collections
import concurrent.futures
import json
import math
import os
import random
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# Đảm bảo console Windows hiển thị chuẩn tiếng Việt UTF-8 và biểu tượng 🐝
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


DEFAULT_BASE_URL = os.getenv("TARGET_URL", "http://localhost:8000")
TOTAL_REQUESTS_DEFAULT = 500
READ_REQUESTS_DEFAULT = 400
WRITE_REQUESTS_DEFAULT = 100
DEFAULT_WORKERS = 50
FLAGSHIP_PRODUCT_IDS = [1, 2, 3, 4, 5, 6, 7, 8]

PAYMENT_METHODS = [
    "Apple Pay",
    "Chuyển khoản VietQR 24/7",
    "COD - Thanh toán khi nhận máy",
    "Trả góp 0% qua thẻ tín dụng",
]
PROMO_CODES = ["APPLE2026", "UTH2026", "TTG500K", ""]


LOCUST_PROFILE_SNIPPET = """# Locust Profile (locustfile.py — chạy với: locust -f tests/swarm_load_test_500.py --host http://localhost:8000)
from locust import HttpUser, task, between
import random

class TTGShopSwarmUser(HttpUser):
    wait_time = between(0.05, 0.2)

    @task(4)
    def read_catalog_and_compare(self):
        self.client.get("/api/products?limit=12", name="GET /api/products")
        self.client.get(f"/api/products/{random.randint(1, 8)}", name="GET /api/products/{id}")
        self.client.get("/api/lineup/compare", name="GET /api/lineup/compare")
        self.client.get("/api/orders/recent?limit=10", name="GET /api/orders/recent")
        self.client.get("/health", name="GET /health")

    @task(1)
    def write_acid_checkout(self):
        pid = random.randint(1, 8)
        promo = random.choice(["APPLE2026", "UTH2026", "TTG500K"])
        payment = random.choice(["Apple Pay", "Chuyển khoản VietQR 24/7"])
        self.client.post("/api/checkout", json={
            "customer_name": f"SwarmLocust_{random.randint(100,999)}",
            "phone": "0909123456",
            "address": "TP.HCM",
            "payment_method": payment,
            "promo_code": promo,
            "items": [{"product_id": pid, "quantity": 1}]
        }, name="POST /api/checkout")
"""

K6_PROFILE_SNIPPET = """// Grafana k6 Profile (k6_script.js — chạy với: k6 run -e TARGET_URL=http://localhost:8000 k6_script.js)
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    flash_sale_500: {
      executor: 'shared-iterations',
      vus: 50,
      iterations: 500,
      maxDuration: '30s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<250'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8000';
const PROMOS = ['APPLE2026', 'UTH2026', 'TTG500K'];
const PAYMENTS = ['Apple Pay', 'Chuyển khoản VietQR 24/7'];

export default function () {
  if (__ITER % 5 === 0) {
    const pid = (__ITER % 8) + 1;
    const payload = JSON.stringify({
      customer_name: `k6_Buyer_${__VU}_${__ITER}`,
      phone: '0909888777',
      address: 'TP. Hồ Chí Minh',
      payment_method: PAYMENTS[__ITER % PAYMENTS.length],
      promo_code: PROMOS[__ITER % PROMOS.length],
      items: [{ product_id: pid, quantity: 1 }],
    });
    const res = http.post(`${BASE_URL}/api/checkout`, payload, {
      headers: { 'Content-Type': 'application/json' },
    });
    check(res, { 'ACID Checkout 201/400': (r) => r.status === 201 || r.status === 400 });
  } else if (__ITER % 5 === 1) {
    const res = http.get(`${BASE_URL}/api/lineup/compare`);
    check(res, { 'Lineup Compare 200 OK': (r) => r.status === 200 });
  } else {
    const res = http.get(`${BASE_URL}/api/products?limit=12`);
    check(res, { 'Catalog 200 OK': (r) => r.status === 200 });
  }
}
"""


def percentile(sorted_values: List[float], pct: float) -> float:
    """Tính phân vị (P50, P95, P99) chính xác từ danh sách đã sắp xếp."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (pct / 100.0) * (len(sorted_values) - 1)
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    if lower == upper:
        return float(sorted_values[lower])
    weight = rank - lower
    return float(sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight)


def http_json_request(
    url: str,
    method: str = "GET",
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = 15.0,
    max_retries_on_socket_err: int = 2,
) -> Tuple[int, Dict[str, Any], Dict[str, str], float, Optional[str]]:
    """
    Thực hiện HTTP request bằng `urllib.request` chuẩn Python.
    Trả về: (status_code, json_body, headers_dict, latency_ms, error_message)
    """
    data_bytes = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "TTGShop-Swarm-QA-Bee/2.1 (500-Concurrent-Verifier)",
        "Connection": "close",
    }
    if payload is not None:
        data_bytes = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"

    # Tránh độ trễ 2000ms do Windows ưu tiên thử IPv6 [::1] trước khi fallback về IPv4 127.0.0.1
    effective_url = url.replace("://localhost:", "://127.0.0.1:").replace("://localhost/", "://127.0.0.1/")

    last_err: Optional[str] = None
    for attempt in range(max_retries_on_socket_err + 1):
        t0 = time.perf_counter()
        req = urllib.request.Request(url=effective_url, data=data_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_body = resp.read().decode("utf-8", errors="replace")
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                status_code = int(resp.getcode() or 200)
                resp_headers = {k.lower(): v for k, v in resp.info().items()}
                try:
                    parsed = json.loads(raw_body) if raw_body else {}
                except Exception:
                    parsed = {"raw": raw_body[:200]}
                return status_code, parsed, resp_headers, elapsed_ms, None

        except urllib.error.HTTPError as http_err:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            status_code = int(http_err.code)
            resp_headers = {k.lower(): v for k, v in (http_err.headers.items() if http_err.headers else [])}
            try:
                err_raw = http_err.read().decode("utf-8", errors="replace")
                parsed = json.loads(err_raw) if err_raw else {}
            except Exception:
                parsed = {}
            return status_code, parsed, resp_headers, elapsed_ms, f"HTTP {status_code}"

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            last_err = str(exc)
            if attempt < max_retries_on_socket_err:
                time.sleep(0.02 * (attempt + 1))
                continue
            return 0, {}, {}, elapsed_ms, last_err

    return 0, {}, {}, 0.0, last_err


def fetch_flagship_stocks(base_url: str) -> Dict[int, Dict[str, Any]]:
    """
    Lấy thông tin tồn kho thực tế của 8 sản phẩm Flagship PC (ID 1..8)
    từ `/api/products?limit=20` (hoặc `/api/products/{id}`).
    """
    stocks: Dict[int, Dict[str, Any]] = {}
    status, data, _, _, err = http_json_request(f"{base_url}/api/products?limit=20", method="GET", timeout=10.0)
    if status == 200 and isinstance(data, dict) and "items" in data:
        for item in data.get("items", []):
            pid = int(item.get("id", 0))
            if pid in FLAGSHIP_PRODUCT_IDS:
                stocks[pid] = {
                    "id": pid,
                    "sku": item.get("sku", f"TTG-PC-{pid:04d}"),
                    "name": item.get("name", f"Flagship PC #{pid}"),
                    "price": float(item.get("price", 0.0)),
                    "stock": int(item.get("stock", 0)),
                }

    # Fallback truy vấn lẻ nếu thiếu bất kỳ sản phẩm nào trong 1..8
    for pid in FLAGSHIP_PRODUCT_IDS:
        if pid not in stocks:
            s_code, p_data, _, _, _ = http_json_request(f"{base_url}/api/products/{pid}", method="GET", timeout=8.0)
            if s_code == 200 and isinstance(p_data, dict) and "product" in p_data:
                prod = p_data["product"]
                stocks[pid] = {
                    "id": pid,
                    "sku": prod.get("sku", f"TTG-PC-{pid:04d}"),
                    "name": prod.get("name", f"Flagship PC #{pid}"),
                    "price": float(prod.get("price", 0.0)),
                    "stock": int(prod.get("stock", 0)),
                }
    return stocks


def probe_swarm_endpoints(base_url: str) -> Dict[str, bool]:
    """
    Kiểm tra xem các endpoint mới của `checkout_api.py` (bao gồm `/api/lineup/compare`)
    đã được gắn vào `main.py` chưa.
    """
    capabilities = {
        "health_ok": False,
        "telemetry_mounted": False,
        "recent_orders_mounted": False,
        "lineup_compare_mounted": False,
        "checkout_mounted": False,
    }
    s_health, _, _, _, _ = http_json_request(f"{base_url}/health", method="GET", timeout=5.0)
    capabilities["health_ok"] = s_health == 200

    s_tel, _, _, _, _ = http_json_request(f"{base_url}/api/swarm/telemetry", method="GET", timeout=5.0)
    capabilities["telemetry_mounted"] = s_tel == 200

    s_rec, _, _, _, _ = http_json_request(f"{base_url}/api/orders/recent?limit=5", method="GET", timeout=5.0)
    capabilities["recent_orders_mounted"] = s_rec == 200

    s_cmp, _, _, _, _ = http_json_request(f"{base_url}/api/lineup/compare", method="GET", timeout=5.0)
    capabilities["lineup_compare_mounted"] = s_cmp == 200

    # Kiểm tra OpenAPI schema để biết `/api/checkout` đã được đăng ký chưa mà không tạo đơn nháp
    s_oa, oa_data, _, _, _ = http_json_request(f"{base_url}/openapi.json", method="GET", timeout=5.0)
    if s_oa == 200 and isinstance(oa_data, dict):
        paths = oa_data.get("paths", {})
        capabilities["checkout_mounted"] = "/api/checkout" in paths
        if "/api/lineup/compare" in paths:
            capabilities["lineup_compare_mounted"] = True
    else:
        capabilities["checkout_mounted"] = capabilities["telemetry_mounted"]

    return capabilities


def allocate_order_targets(
    stocks_before: Dict[int, Dict[str, Any]],
    num_orders: int,
) -> List[int]:
    """
    Phân bổ `num_orders` (100) giao dịch đặt hàng trên 8 cấu hình Flagship PC (ID 1..8)
    sao cho ưu tiên các máy còn tồn kho dồi dào, đồng thời phủ đều cả 8 mẫu Flagship PC.
    """
    sim_remaining = {pid: max(0, int(info.get("stock", 0))) for pid, info in stocks_before.items()}
    for pid in FLAGSHIP_PRODUCT_IDS:
        sim_remaining.setdefault(pid, 100)

    allocated: List[int] = []
    idx = 0
    while len(allocated) < num_orders:
        available_pids = [pid for pid in FLAGSHIP_PRODUCT_IDS if sim_remaining.get(pid, 0) > 0]
        if available_pids:
            chosen_pid = available_pids[idx % len(available_pids)]
            sim_remaining[chosen_pid] -= 1
            allocated.append(chosen_pid)
        else:
            # Nếu tổng tồn kho ban đầu của cả 8 máy < 100, các request vượt ngưỡng sẽ kiểm thử ACID Rollback (HTTP 400)
            chosen_pid = FLAGSHIP_PRODUCT_IDS[idx % len(FLAGSHIP_PRODUCT_IDS)]
            allocated.append(chosen_pid)
        idx += 1
    return allocated


def build_500_workload_tasks(
    base_url: str,
    read_count: int,
    write_count: int,
    stocks_before: Dict[int, Dict[str, Any]],
    capabilities: Dict[str, bool],
) -> List[Dict[str, Any]]:
    """
    Xây dựng danh sách 500 tác vụ kiểm thử tải (400 Read + 100 Write ACID),
    xáo trộn ngẫu nhiên theo hạt giống cố định để mô phỏng đúng lưu lượng Flash Sale đồng thời.
    """
    tasks: List[Dict[str, Any]] = []

    # 1. Xây dựng 400 tác vụ READ (Catalog, Product Detail, Lineup Compare, Health, Recent Orders, Swarm Telemetry)
    for i in range(read_count):
        if capabilities.get("telemetry_mounted") and capabilities.get("recent_orders_mounted"):
            mod = i % 20
            if mod < 8:
                # 40% của 400 = 160 requests: GET /api/products?limit=12
                tasks.append({
                    "task_id": f"READ-{i+1:03d}",
                    "kind": "READ",
                    "endpoint_label": "GET /api/products",
                    "method": "GET",
                    "url": f"{base_url}/api/products?limit=12",
                    "fallback_url": None,
                    "payload": None,
                    "product_id": None,
                    "quantity": 0,
                })
            elif mod < 13:
                # 25% của 400 = 100 requests: GET /api/products/{id}
                pid = FLAGSHIP_PRODUCT_IDS[i % len(FLAGSHIP_PRODUCT_IDS)]
                tasks.append({
                    "task_id": f"READ-{i+1:03d}",
                    "kind": "READ",
                    "endpoint_label": "GET /api/products/{id}",
                    "method": "GET",
                    "url": f"{base_url}/api/products/{pid}",
                    "fallback_url": None,
                    "payload": None,
                    "product_id": pid,
                    "quantity": 0,
                })
            elif mod < 16:
                # 15% của 400 = 60 requests: GET /api/lineup/compare (Apple Store Hardware Comparison)
                tasks.append({
                    "task_id": f"READ-{i+1:03d}",
                    "kind": "READ",
                    "endpoint_label": "GET /api/lineup/compare",
                    "method": "GET",
                    "url": f"{base_url}/api/lineup/compare",
                    "fallback_url": f"{base_url}/api/products?limit=8",
                    "payload": None,
                    "product_id": None,
                    "quantity": 0,
                })
            elif mod < 18:
                # 10% của 400 = 40 requests: GET /health
                tasks.append({
                    "task_id": f"READ-{i+1:03d}",
                    "kind": "READ",
                    "endpoint_label": "GET /health",
                    "method": "GET",
                    "url": f"{base_url}/health",
                    "fallback_url": None,
                    "payload": None,
                    "product_id": None,
                    "quantity": 0,
                })
            elif mod == 18:
                # 5% của 400 = 20 requests: GET /api/orders/recent
                tasks.append({
                    "task_id": f"READ-{i+1:03d}",
                    "kind": "READ",
                    "endpoint_label": "GET /api/orders/recent",
                    "method": "GET",
                    "url": f"{base_url}/api/orders/recent?limit=10",
                    "fallback_url": None,
                    "payload": None,
                    "product_id": None,
                    "quantity": 0,
                })
            else:
                # 5% của 400 = 20 requests: GET /api/swarm/telemetry
                tasks.append({
                    "task_id": f"READ-{i+1:03d}",
                    "kind": "READ",
                    "endpoint_label": "GET /api/swarm/telemetry",
                    "method": "GET",
                    "url": f"{base_url}/api/swarm/telemetry",
                    "fallback_url": None,
                    "payload": None,
                    "product_id": None,
                    "quantity": 0,
                })
        else:
            mod = i % 20
            if mod < 11:
                tasks.append({
                    "task_id": f"READ-{i+1:03d}",
                    "kind": "READ",
                    "endpoint_label": "GET /api/products",
                    "method": "GET",
                    "url": f"{base_url}/api/products?limit=12",
                    "fallback_url": None,
                    "payload": None,
                    "product_id": None,
                    "quantity": 0,
                })
            elif mod < 16:
                pid = FLAGSHIP_PRODUCT_IDS[i % len(FLAGSHIP_PRODUCT_IDS)]
                tasks.append({
                    "task_id": f"READ-{i+1:03d}",
                    "kind": "READ",
                    "endpoint_label": "GET /api/products/{id}",
                    "method": "GET",
                    "url": f"{base_url}/api/products/{pid}",
                    "fallback_url": None,
                    "payload": None,
                    "product_id": pid,
                    "quantity": 0,
                })
            else:
                tasks.append({
                    "task_id": f"READ-{i+1:03d}",
                    "kind": "READ",
                    "endpoint_label": "GET /health",
                    "method": "GET",
                    "url": f"{base_url}/health",
                    "fallback_url": None,
                    "payload": None,
                    "product_id": None,
                    "quantity": 0,
                })

    # 2. Xây dựng 100 tác vụ WRITE ACID (POST /api/checkout & POST /api/orders trên Flagship PCs)
    # Kiểm thử mã giảm giá APPLE2026 (-1,500,000đ), UTH2026 (-1,000,000đ), TTG500K (-500,000đ)
    # và các phương thức Apple Pay, Chuyển khoản VietQR 24/7, COD, Trả góp 0%.
    order_pids = allocate_order_targets(stocks_before, write_count)
    use_checkout_api = capabilities.get("checkout_mounted", True)

    for j, pid in enumerate(order_pids):
        customer_name = f"Khách hàng FlashSale #{j+1:03d}"
        # Nếu `/api/checkout` đã sẵn sàng, phân bổ 80% qua `/api/checkout` và 20% qua `/api/orders`
        if use_checkout_api and (j % 5 < 4):
            promo = PROMO_CODES[j % len(PROMO_CODES)]
            payment = PAYMENT_METHODS[(j // 2) % len(PAYMENT_METHODS)]
            tasks.append({
                "task_id": f"ORDER-{j+1:03d}",
                "kind": "WRITE",
                "endpoint_label": "POST /api/checkout",
                "method": "POST",
                "url": f"{base_url}/api/checkout",
                "fallback_url": f"{base_url}/api/orders",
                "payload": {
                    "customer_name": customer_name,
                    "phone": f"0909{100000 + j:06d}",
                    "address": f"Số {j+1} Lý Thường Kiệt, Quận 10, TP. Hồ Chí Minh",
                    "payment_method": payment,
                    "promo_code": promo,
                    "items": [{"product_id": pid, "quantity": 1}],
                },
                "fallback_payload": {
                    "customer_name": customer_name,
                    "product_id": pid,
                    "quantity": 1,
                },
                "product_id": pid,
                "quantity": 1,
            })
        else:
            tasks.append({
                "task_id": f"ORDER-{j+1:03d}",
                "kind": "WRITE",
                "endpoint_label": "POST /api/orders",
                "method": "POST",
                "url": f"{base_url}/api/orders",
                "fallback_url": None,
                "payload": {
                    "customer_name": customer_name,
                    "product_id": pid,
                    "quantity": 1,
                },
                "fallback_payload": None,
                "product_id": pid,
                "quantity": 1,
            })

    # Xáo trộn ngẫu nhiên 500 request để mô phỏng tải đồng thời thực tế (Read + Write xen kẽ)
    rng = random.Random(20261111)
    rng.shuffle(tasks)
    return tasks


def execute_single_task(task: Dict[str, Any], timeout: float = 15.0) -> Dict[str, Any]:
    """Thực thi 1 request trong ThreadPoolExecutor và trích xuất đầy đủ telemetry."""
    status, body, headers, latency_ms, err = http_json_request(
        url=task["url"],
        method=task["method"],
        payload=task["payload"],
        timeout=timeout,
    )
    endpoint_label = task["endpoint_label"]

    # Tự động fallback cho READ nếu `/api/lineup/compare` chưa được mount trên server cũ
    if (
        task["kind"] == "READ"
        and status == 404
        and task.get("fallback_url")
    ):
        status, body, headers, fb_latency_ms, err = http_json_request(
            url=task["fallback_url"],
            method="GET",
            payload=None,
            timeout=timeout,
        )
        latency_ms += fb_latency_ms
        endpoint_label = "GET /api/products (fallback)"

    # Tự động fallback sang POST /api/orders nếu POST /api/checkout trả về 404 (chưa mount router)
    if (
        task["kind"] == "WRITE"
        and status == 404
        and task.get("fallback_url")
        and task.get("fallback_payload")
    ):
        status, body, headers, fb_latency_ms, err = http_json_request(
            url=task["fallback_url"],
            method="POST",
            payload=task["fallback_payload"],
            timeout=timeout,
        )
        latency_ms += fb_latency_ms
        endpoint_label = "POST /api/orders (fallback)"

    # Xác định Node Replica xử lý request từ Header `X-Served-By` hoặc JSON body
    served_by = headers.get("x-served-by")
    if not served_by and isinstance(body, dict):
        served_by = body.get("served_by") or body.get("node_id")
    if not served_by:
        served_by = "unknown-node"

    # Phân loại kết quả
    is_http_5xx = status >= 500 or status == 0
    is_order_committed = task["kind"] == "WRITE" and status in (200, 201)
    is_acid_rollback = task["kind"] == "WRITE" and status == 400

    if task["kind"] == "READ":
        is_success = status == 200
    else:
        # Với giao dịch đặt hàng ACID: 201 Created là đặt thành công;
        # 400 Bad Request khi hết hàng là ACID Rollback hợp lệ (chống bán âm kho thành công).
        is_success = status in (200, 201, 400)

    return {
        "task_id": task["task_id"],
        "kind": task["kind"],
        "endpoint_label": endpoint_label,
        "status": status,
        "latency_ms": latency_ms,
        "served_by": str(served_by),
        "product_id": task["product_id"],
        "quantity": task["quantity"] if is_order_committed else 0,
        "is_success": is_success,
        "is_order_committed": is_order_committed,
        "is_acid_rollback": is_acid_rollback,
        "is_http_5xx": is_http_5xx,
        "error": err,
    }


def format_bar(ratio: float, width: int = 24) -> str:
    filled = max(0, min(width, int(round(ratio * width))))
    return "█" * filled + "░" * (width - filled)


def run_benchmark(
    base_url: str,
    total_requests: int = TOTAL_REQUESTS_DEFAULT,
    read_requests: int = READ_REQUESTS_DEFAULT,
    write_requests: int = WRITE_REQUESTS_DEFAULT,
    workers: int = DEFAULT_WORKERS,
    timeout: float = 15.0,
) -> Dict[str, Any]:
    base_url = base_url.rstrip("/")

    print("=" * 92)
    print("🍎 TTGSHOP APPLE STORE EDITION — KIỂM THỬ TẢI ĐỒNG THỜI & TOÀN VẸN ACID (500 REQUESTS)")
    print("=" * 92)
    print(f"  • Mục tiêu (Target URL)       : {base_url}")
    print(f"  • Tổng quy mô Flash Sale      : {total_requests} concurrent requests ({read_requests} READ + {write_requests} WRITE ACID)")
    print(f"  • Luồng thực thi (Workers)    : {workers} luồng song song (ThreadPoolExecutor)")

    # Bước 1: Kiểm tra kết nối & thăm dò endpoint
    capabilities = probe_swarm_endpoints(base_url)
    if not capabilities["health_ok"]:
        print("\n[!] CẢNH BÁO: Không thể kết nối tới máy chủ tại", base_url)
        print("    Vui lòng khởi chạy ứng dụng trước: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)

    mode_desc = (
        "APPLE STORE + SWARM API (/api/checkout + /api/lineup/compare + /api/orders/recent + /api/swarm/telemetry)"
        if capabilities["checkout_mounted"]
        else "CORE API (/api/orders + /api/products + /health)"
    )
    print(f"  • Chế độ Endpoint phát hiện   : {mode_desc}")

    # Bước 2: Chụp ảnh tồn kho TRƯỚC kiểm thử (Stock Before)
    stocks_before_map = fetch_flagship_stocks(base_url)
    total_stock_before = sum(item["stock"] for item in stocks_before_map.values())
    print(f"  • Tổng tồn kho Flagship trước : {total_stock_before:,} máy (trên {len(stocks_before_map)} mã Flagship PC #1..#8)")
    print("-" * 92)

    # Bước 3: Khởi tạo 500 tác vụ và bắn đồng loạt qua ThreadPoolExecutor
    tasks = build_500_workload_tasks(
        base_url=base_url,
        read_count=read_requests,
        write_count=write_requests,
        stocks_before=stocks_before_map,
        capabilities=capabilities,
    )

    print(f"🚀 Đang bắn đồng loạt {len(tasks)} requests vào {base_url} ...")
    results: List[Dict[str, Any]] = []
    progress_lock = threading.Lock()
    completed_counter = 0

    wall_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_task = {executor.submit(execute_single_task, t, timeout): t for t in tasks}
        for future in concurrent.futures.as_completed(future_to_task):
            res = future.result()
            results.append(res)
            with progress_lock:
                completed_counter += 1
                if completed_counter % 100 == 0 or completed_counter == len(tasks):
                    elapsed_so_far = time.perf_counter() - wall_start
                    print(
                        f"   ✓ Đã hoàn tất {completed_counter:>3}/{len(tasks)} requests "
                        f"({(completed_counter / len(tasks)) * 100:5.1f}%) — {elapsed_so_far:.2f}s"
                    )
    wall_duration_s = max(0.001, time.perf_counter() - wall_start)

    # Bước 4: Chụp ảnh tồn kho SAU kiểm thử (Stock After)
    stocks_after_map = fetch_flagship_stocks(base_url)
    total_stock_after = sum(item["stock"] for item in stocks_after_map.values())

    # Bước 5: Tổng hợp số liệu thống kê
    total_executed = len(results)
    success_count = sum(1 for r in results if r["is_success"])
    http_5xx_count = sum(1 for r in results if r["is_http_5xx"])
    success_rate_pct = (success_count / total_executed * 100.0) if total_executed else 0.0
    throughput_rps = total_executed / wall_duration_s

    all_latencies = sorted(r["latency_ms"] for r in results)
    read_latencies = sorted(r["latency_ms"] for r in results if r["kind"] == "READ")
    write_latencies = sorted(r["latency_ms"] for r in results if r["kind"] == "WRITE")

    p50_ms = percentile(all_latencies, 50.0)
    p95_ms = percentile(all_latencies, 95.0)
    p99_ms = percentile(all_latencies, 99.0)
    avg_ms = statistics.mean(all_latencies) if all_latencies else 0.0
    min_ms = all_latencies[0] if all_latencies else 0.0
    max_ms = all_latencies[-1] if all_latencies else 0.0

    # Phân bổ tải theo Node Replica
    node_counts: Dict[str, int] = collections.Counter(r["served_by"] for r in results)
    replica_1_count = sum(cnt for node, cnt in node_counts.items() if "app-replica-1" in node)
    replica_2_count = sum(cnt for node, cnt in node_counts.items() if "app-replica-2" in node)

    # Kiểm định ACID Stock Integrity
    successful_orders = sum(r["quantity"] for r in results if r["is_order_committed"])
    acid_rollbacks = sum(1 for r in results if r["is_acid_rollback"])
    orders_by_pid: Dict[int, int] = collections.Counter()
    for r in results:
        if r["is_order_committed"] and r["product_id"] in FLAGSHIP_PRODUCT_IDS:
            orders_by_pid[int(r["product_id"])] += int(r["quantity"])

    expected_stock_after = total_stock_before - successful_orders
    stock_equation_holds = expected_stock_after == total_stock_after
    min_stock_after = min((item["stock"] for item in stocks_after_map.values()), default=0)
    zero_overselling_holds = min_stock_after >= 0

    per_product_audit: List[Dict[str, Any]] = []
    all_pids_consistent = True
    for pid in FLAGSHIP_PRODUCT_IDS:
        s_before = stocks_before_map.get(pid, {}).get("stock", 0)
        s_after = stocks_after_map.get(pid, {}).get("stock", 0)
        sold = orders_by_pid.get(pid, 0)
        expected_p = s_before - sold
        pid_ok = (expected_p == s_after) and (s_after >= 0)
        if not pid_ok:
            all_pids_consistent = False
        per_product_audit.append({
            "product_id": pid,
            "sku": stocks_before_map.get(pid, {}).get("sku", f"TTG-PC-{pid:04d}"),
            "name": stocks_before_map.get(pid, {}).get("name", f"Flagship PC #{pid}"),
            "stock_before": s_before,
            "successful_orders": sold,
            "expected_stock_after": expected_p,
            "stock_after": s_after,
            "acid_valid": pid_ok,
        })

    acid_overall_pass = stock_equation_holds and zero_overselling_holds and all_pids_consistent

    # Thống kê theo từng Endpoint
    endpoint_stats: Dict[str, List[Dict[str, Any]]] = collections.defaultdict(list)
    for r in results:
        endpoint_stats[r["endpoint_label"]].append(r)

    # Bước 6: In bảng báo cáo chuẩn kỹ thuật tiếng Việt + Technical Benchmark
    print("\n" + "=" * 92)
    print("📊 BẢNG 1: TỔNG HỢP KẾT QUẢ KIỂM THỬ TẢI 500 CONCURRENT REQUESTS (BENCHMARK SUMMARY)")
    print("=" * 92)
    print(f"  ┌────────────────────────────────────────────────────┬───────────────────────────────────┐")
    print(f"  │ Chỉ số đo lường (Benchmark Metric)                 │ Giá trị thực nghiệm (Measured)    │")
    print(f"  ├────────────────────────────────────────────────────┼───────────────────────────────────┤")
    print(f"  │ 1. Tổng số Request (Total Requests)                │ {total_executed:>6} requests (400 R + 100 W)   │")
    print(f"  │ 2. Tỷ lệ thành công (Success Rate %)               │ {success_rate_pct:>6.2f}% ({success_count}/{total_executed} hợp lệ)          │")
    print(f"  │ 3. Số lỗi máy chủ HTTP 5xx (HTTP 5xx Count)        │ {http_5xx_count:>6} lỗi (Zero Server Crash)    │")
    print(f"  │ 4. Thời gian hoàn tất (Total Wall Time)            │ {wall_duration_s:>6.3f} giây                       │")
    print(f"  │ 5. Thông lượng xử lý (Throughput)                  │ {throughput_rps:>6.2f} req/s                      │")
    print(f"  │ 6. Độ trễ trung vị P50 (Latency P50 / Median)      │ {p50_ms:>6.2f} ms                         │")
    print(f"  │ 7. Độ trễ phân vị P95 (Latency P95)                │ {p95_ms:>6.2f} ms                         │")
    print(f"  │ 8. Độ trễ phân vị P99 (Latency P99)                │ {p99_ms:>6.2f} ms                         │")
    print(f"  │ 9. Độ trễ Trung bình / Min / Max (Avg / Min / Max) │ {avg_ms:>5.1f} / {min_ms:>4.1f} / {max_ms:>6.1f} ms         │")
    print(f"  └────────────────────────────────────────────────────┴───────────────────────────────────┘")

    print("\n" + "=" * 92)
    print("⚖️ BẢNG 2: PHÂN BỔ TẢI QUA CÁC NHÁNH REPLICA (MULTI-AZ LOAD BALANCING DISTRIBUTION)")
    print("=" * 92)
    print(f"  ┌──────────────────────────────┬────────────┬────────────┬───────────────────────────────┐")
    print(f"  │ Nhánh xử lý (Serving Node)   │ Số Request │ Tỷ lệ (%)  │ Biểu đồ phân tải (Load Bar)   │")
    print(f"  ├──────────────────────────────┼────────────┼────────────┼───────────────────────────────┤")
    for node_name, cnt in sorted(node_counts.items()):
        ratio = cnt / total_executed if total_executed else 0.0
        bar = format_bar(ratio, width=24)
        print(f"  │ {node_name:<28} │ {cnt:>10} │ {ratio*100:>8.2f}%  │ {bar:<29} │")
    print(f"  └──────────────────────────────┴────────────┴────────────┴───────────────────────────────┘")
    print(
        f"  👉 Đối chiếu Multi-AZ: app-replica-1 (AZ-a) = {replica_1_count} reqs ({replica_1_count/total_executed*100:.1f}%) | "
        f"app-replica-2 (AZ-b) = {replica_2_count} reqs ({replica_2_count/total_executed*100:.1f}%)"
    )

    print("\n" + "=" * 92)
    print("🔒 BẢNG 3: KIỂM ĐỊNH TOÀN VẸN TỒN KHO ACID (ACID STOCK INTEGRITY & ZERO OVERSELLING)")
    print("=" * 92)
    print(f"  ┌────────┬──────────────┬────────────────────────────────────┬──────────┬──────────┬──────────┬──────────┐")
    print(f"  │ ID     │ Mã SKU       │ Tên cấu hình Flagship PC           │ Tồn đầu  │ Đã bán   │ Kỳ vọng  │ Tồn cuối │")
    print(f"  ├────────┼──────────────┼────────────────────────────────────┼──────────┼──────────┼──────────┼──────────┤")
    for row in per_product_audit:
        short_name = row["name"][:34]
        print(
            f"  │ #{row['product_id']:<5} │ {row['sku']:<12} │ {short_name:<34} │ "
            f"{row['stock_before']:>8} │ {row['successful_orders']:>8} │ "
            f"{row['expected_stock_after']:>8} │ {row['stock_after']:>8} │"
        )
    print(f"  ├────────┴──────────────┴────────────────────────────────────┼──────────┼──────────┼──────────┼──────────┤")
    print(
        f"  │ TỔNG CỘNG TOÀN BỘ 8 MẪU FLAGSHIP PC                        │ "
        f"{total_stock_before:>8} │ {successful_orders:>8} │ "
        f"{expected_stock_after:>8} │ {total_stock_after:>8} │"
    )
    print(f"  └────────────────────────────────────────────────────────────┴──────────┴──────────┴──────────┴──────────┘")

    acid_badge = "✅ PASS (ĐẠT CHUẨN ACID 100%)" if acid_overall_pass else "❌ FAIL (SAI LỆCH TỒN KHO)"
    oversell_badge = "✅ ZERO OVERSELLING (Không âm kho)" if zero_overselling_holds else "❌ OVERSELLING DETECTED"
    print(f"  • Phương trình bảo toàn tồn kho : stock_before ({total_stock_before}) - successful_orders ({successful_orders}) == stock_after ({total_stock_after})")
    print(f"  • Số giao dịch ACID Rollback    : {acid_rollbacks} (HTTP 400 khi hết hàng - bảo vệ an toàn tồn kho)")
    print(f"  • Tồn kho thấp nhất ghi nhận    : {min_stock_after} máy (>= 0) -> {oversell_badge}")
    print(f"  • Kết luận toàn vẹn dữ liệu     : {acid_badge}")

    print("\n" + "=" * 92)
    print("📡 BẢNG 4: CHI TIẾT ĐỘ TRỄ THEO TỪNG ENDPOINT (PER-ENDPOINT LATENCY BREAKDOWN)")
    print("=" * 92)
    print(f"  ┌───────────────────────────────┬────────┬──────────┬──────────┬──────────┬──────────┬──────────┐")
    print(f"  │ Endpoint                      │ Số lượng│ HTTP 2xx │ HTTP 4xx │ HTTP 5xx │ P50 (ms) │ P95 (ms) │")
    print(f"  ├───────────────────────────────┼────────┼──────────┼──────────┼──────────┼──────────┼──────────┤")
    for ep_label, ep_rows in sorted(endpoint_stats.items()):
        ep_lats = sorted(r["latency_ms"] for r in ep_rows)
        c_2xx = sum(1 for r in ep_rows if 200 <= r["status"] < 300)
        c_4xx = sum(1 for r in ep_rows if 400 <= r["status"] < 500)
        c_5xx = sum(1 for r in ep_rows if r["status"] >= 500 or r["status"] == 0)
        ep_p50 = percentile(ep_lats, 50.0)
        ep_p95 = percentile(ep_lats, 95.0)
        print(
            f"  │ {ep_label:<29} │ {len(ep_rows):>6} │ {c_2xx:>8} │ {c_4xx:>8} │ "
            f"{c_5xx:>8} │ {ep_p50:>8.2f} │ {ep_p95:>8.2f} │"
        )
    print(f"  └───────────────────────────────┴────────┴──────────┴──────────┴──────────┴──────────┴──────────┘")
    print("=" * 92)

    summary_payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target_url": base_url,
        "total_requests": total_executed,
        "read_requests": read_requests,
        "write_requests": write_requests,
        "workers": workers,
        "wall_time_seconds": round(wall_duration_s, 4),
        "throughput_rps": round(throughput_rps, 2),
        "success_count": success_count,
        "success_rate_pct": round(success_rate_pct, 2),
        "http_5xx_count": http_5xx_count,
        "latency_ms": {
            "min": round(min_ms, 2),
            "avg": round(avg_ms, 2),
            "p50": round(p50_ms, 2),
            "p95": round(p95_ms, 2),
            "p99": round(p99_ms, 2),
            "max": round(max_ms, 2),
            "read_p50": round(percentile(read_latencies, 50.0), 2),
            "read_p95": round(percentile(read_latencies, 95.0), 2),
            "write_p50": round(percentile(write_latencies, 50.0), 2),
            "write_p95": round(percentile(write_latencies, 95.0), 2),
        },
        "load_distribution": dict(node_counts),
        "replica_1_count": replica_1_count,
        "replica_2_count": replica_2_count,
        "acid_stock_integrity": {
            "stock_before": total_stock_before,
            "successful_orders": successful_orders,
            "acid_rollbacks": acid_rollbacks,
            "expected_stock_after": expected_stock_after,
            "stock_after": total_stock_after,
            "equation_verified": stock_equation_holds,
            "min_stock_after": min_stock_after,
            "zero_overselling": zero_overselling_holds,
            "overall_pass": acid_overall_pass,
            "per_product": per_product_audit,
        },
    }

    # Lưu báo cáo JSON vào `tests/data/swarm_load_test_500_summary.json`
    try:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        out_path = os.path.join(data_dir, "swarm_load_test_500_summary.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary_payload, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã xuất dữ liệu chuẩn JSON tại: {out_path}")
    except Exception:
        pass

    return summary_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="🐝 TTGShop Well-Architected V2 — Kịch bản kiểm thử tải 500 Concurrent Requests & ACID Stock Verifier"
    )
    parser.add_argument(
        "--url",
        "--base-url",
        dest="url",
        default=DEFAULT_BASE_URL,
        help=f"Địa chỉ máy chủ mục tiêu (mặc định: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=TOTAL_REQUESTS_DEFAULT,
        help="Tổng số concurrent requests (mặc định: 500)",
    )
    parser.add_argument(
        "--reads",
        type=int,
        default=READ_REQUESTS_DEFAULT,
        help="Số lượng request đọc Catalog/Health/Telemetry (mặc định: 400)",
    )
    parser.add_argument(
        "--writes",
        type=int,
        default=WRITE_REQUESTS_DEFAULT,
        help="Số lượng giao dịch đặt hàng ACID trên Flagship PC (mặc định: 100)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="Số luồng ThreadPoolExecutor đồng thời (mặc định: 50)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Timeout mỗi HTTP request tính bằng giây (mặc định: 15.0)",
    )
    parser.add_argument(
        "--show-profiles",
        action="store_true",
        help="Hiển thị cấu hình Locust & Grafana k6 tương đương rồi thoát",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.show_profiles:
        print("=" * 80)
        print("🐝 LOCUST & K6 LOAD PROFILES (OPTIONAL REFERENCE)")
        print("=" * 80)
        print(LOCUST_PROFILE_SNIPPET)
        print("-" * 80)
        print(K6_PROFILE_SNIPPET)
        return 0

    read_cnt = args.reads
    write_cnt = args.writes
    if args.requests != (read_cnt + write_cnt):
        write_cnt = max(1, int(round(args.requests * 0.2)))
        read_cnt = max(1, args.requests - write_cnt)

    summary = run_benchmark(
        base_url=args.url,
        total_requests=read_cnt + write_cnt,
        read_requests=read_cnt,
        write_requests=write_cnt,
        workers=args.workers,
        timeout=args.timeout,
    )

    # Trả về exit code 0 nếu không có lỗi 5xx và bảo toàn tồn kho ACID đạt 100%
    if summary["http_5xx_count"] == 0 and summary["acid_stock_integrity"]["overall_pass"]:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
