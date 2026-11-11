# -*- coding: utf-8 -*-
"""
TTGShop PC Gaming - Well-Architected Interactive Demo Server
Tác giả: Lô Nguyễn Hoàng Long (019206004121 - Trưởng nhóm 05)
GVHD: TS. Lê Quốc Tuấn - Trường ĐH Giao thông Vận tải TP.HCM (UTH)
"""
import os
import sys
import threading
import time
import webbrowser
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from main import app  # noqa: E402


def open_browser_later(url: str):
    time.sleep(1.5)
    try:
        webbrowser.open(url)
    except Exception:
        pass


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    url = f"http://localhost:{port}"
    print("=" * 72)
    print("🚀 TTGSHOP PC GAMING - WELL-ARCHITECTED CLOUD DEMO SERVER (V2)")
    print(f"👉 Trang chủ cửa hàng PC Gaming : {url}")
    print(f"👉 Slide thuyết trình 16:9      : {url}/slides")
    print(f"👉 Prometheus Metrics           : {url}/metrics")
    print(f"👉 Healthcheck & Load Balancer  : {url}/health")
    print("=" * 72)
    threading.Thread(target=open_browser_later, args=(url,), daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
