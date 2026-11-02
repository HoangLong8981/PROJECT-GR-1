# -*- coding: utf-8 -*-
"""
Trình khởi chạy Cụm Thực nghiệm Trực tiếp (1-Click Local Cluster Demo)
Chạy được ngay trên Windows mà KHÔNG cần bật Docker/WSL2, phục vụ demo trực tiếp trên trình duyệt tại:
  👉 http://localhost:8080
Bao gồm:
  - Load Balancer L7 (Cổng 8080): Cân bằng tải & Failover tự động < 1.5s
  - App Replica 1 (AZ-a) (Cổng 8001)
  - App Replica 2 (AZ-b) (Cổng 8002)
  - CSDL 500 sản phẩm chuẩn ACID
"""

import os
import sys
import time
import socket
import subprocess
import threading
import http.server
import urllib.request

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
APP_DIR = os.path.join(PROJECT_ROOT, "app")


class DemoLoadBalancer(http.server.BaseHTTPRequestHandler):
    backends = ["http://127.0.0.1:8001", "http://127.0.0.1:8002"]
    rr_idx = 0
    lock = threading.Lock()

    def log_message(self, fmt, *args):
        pass

    def _proxy(self, method: str):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else None

        with DemoLoadBalancer.lock:
            start = DemoLoadBalancer.rr_idx
            DemoLoadBalancer.rr_idx = (DemoLoadBalancer.rr_idx + 1) % len(self.backends)

        for i in range(len(self.backends)):
            backend = self.backends[(start + i) % len(self.backends)]
            url = f"{backend}{self.path}"
            try:
                req = urllib.request.Request(url, data=body, method=method)
                if "Content-Type" in self.headers:
                    req.add_header("Content-Type", self.headers["Content-Type"])
                with urllib.request.urlopen(req, timeout=1.5) as resp:
                    data = resp.read()
                    self.send_response(resp.status)
                    for k, v in resp.getheaders():
                        if k.lower() not in ("transfer-encoding", "server", "date"):
                            self.send_header(k, v)
                    self.send_header("X-Upstream-Node", backend)
                    self.end_headers()
                    self.wfile.write(data)
                    return
            except Exception:
                continue

        self.send_response(502)
        self.end_headers()
        self.wfile.write(b'{"detail":"Bad Gateway"}')

    def do_GET(self):
        self._proxy("GET")

    def do_POST(self):
        self._proxy("POST")


if __name__ == "__main__":
    print("=" * 72)
    print(" UTH CLOUD E-COMMERCE - KHỞI CHẠY CỤM DEMO WELL-ARCHITECTED (V2)")
    print("=" * 72)

    env1 = os.environ.copy()
    env1["NODE_ID"] = "app-replica-1 (AZ-a)"
    env1["DB_ENGINE"] = "sqlite"

    env2 = os.environ.copy()
    env2["NODE_ID"] = "app-replica-2 (AZ-b)"
    env2["DB_ENGINE"] = "sqlite"

    p1 = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8001", "--log-level", "warning"],
        cwd=APP_DIR,
        env=env1
    )
    p2 = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8002", "--log-level", "warning"],
        cwd=APP_DIR,
        env=env2
    )

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 8080), DemoLoadBalancer)
    print(" [+] App Replica 1 (AZ-a) đang chạy tại: http://127.0.0.1:8001")
    print(" [+] App Replica 2 (AZ-b) đang chạy tại: http://127.0.0.1:8002")
    print(" [+] Load Balancer L7 đang lắng nghe tại: http://localhost:8080")
    print(" [+] Prometheus Metrics tại:              http://localhost:8080/metrics")
    print(" -> Nhấn Ctrl+C để dừng cụm máy chủ.")
    print("=" * 72)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐang dừng cụm máy chủ...")
    finally:
        server.server_close()
        p1.terminate()
        p2.terminate()
