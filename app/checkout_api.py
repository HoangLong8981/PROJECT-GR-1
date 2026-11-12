# -*- coding: utf-8 -*-
"""
Shopee Mall Vietnam E-Commerce Well-Architected V2
Multi-Item ACID Checkout, Shopee Mall Brands, Hardware Comparison & Swarm Telemetry API
Owned by: Worker 2 (@shopee-backend)
"""

import os
import sys
import html
import time
import sqlite3
import threading
from collections import deque
from typing import List, Optional, Dict, Any

try:
    from psycopg2.extras import RealDictCursor
except ImportError:
    RealDictCursor = None

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, ConfigDict

router = APIRouter()

# In-memory ring buffer storing the last 30 ACID checkout & system telemetry events
SWARM_TELEMETRY_LOG: deque = deque(maxlen=30)
_telemetry_lock = threading.Lock()

# Supported Shopee promotional discount vouchers (VND)
PROMO_DISCOUNTS: Dict[str, float] = {
    "SHOPEE2026": 1_500_000.0,
    "SHOPEE500K": 500_000.0,
    "UTH2026": 1_000_000.0,
    "TTG500K": 500_000.0,
    "APPLE2026": 1_500_000.0,  # Retained for backward compatibility
}

PROMO_METADATA: List[Dict[str, Any]] = [
    {
        "code": "SHOPEE2026",
        "discount": 1_500_000.0,
        "label": "Giảm 1.500.000đ - Shopee Voucher Siêu Sale 2026",
        "min_order": 10_000_000.0,
        "badge": "VOUCHER HOT",
    },
    {
        "code": "SHOPEE500K",
        "discount": 500_000.0,
        "label": "Giảm 500.000đ - Voucher Điện Tử Shopee Mall",
        "min_order": 5_000_000.0,
        "badge": "MALL VOUCHER",
    },
    {
        "code": "UTH2026",
        "discount": 1_000_000.0,
        "label": "Giảm 1.000.000đ - UTH Cloud Well-Architected",
        "min_order": 5_000_000.0,
        "badge": "CLOUD ARCH",
    },
    {
        "code": "TTG500K",
        "discount": 500_000.0,
        "label": "Giảm 500.000đ - Ưu đãi thành viên TTGShop",
        "min_order": 3_000_000.0,
        "badge": "THÀNH VIÊN",
    },
    {
        "code": "APPLE2026",
        "discount": 1_500_000.0,
        "label": "Giảm 1.500.000đ - Apple Authorised Reseller",
        "min_order": 10_000_000.0,
        "badge": "AAR",
    },
]

# Supported payment methods for Shopee Mall Checkout
SUPPORTED_PAYMENT_METHODS: List[str] = [
    "Ví ShopeePay",
    "Apple Pay",
    "Chuyển khoản VietQR 24/7",
    "COD - Thanh toán khi nhận hàng",
    "Trả góp 0%",
]

PAYMENT_METHOD_ALIASES: Dict[str, str] = {
    "ví shopeepay": "Ví ShopeePay",
    "vi shopeepay": "Ví ShopeePay",
    "shopeepay": "Ví ShopeePay",
    "shopee pay": "Ví ShopeePay",
    "shopee_pay": "Ví ShopeePay",
    "apple pay": "Apple Pay",
    "applepay": "Apple Pay",
    "apple_pay": "Apple Pay",
    "vietqr": "Chuyển khoản VietQR 24/7",
    "vietqr 24/7": "Chuyển khoản VietQR 24/7",
    "chuyển khoản vietqr 24/7": "Chuyển khoản VietQR 24/7",
    "chuyen khoan vietqr 24/7": "Chuyển khoản VietQR 24/7",
    "chuyển khoản vietqr": "Chuyển khoản VietQR 24/7",
    "vietqr24/7": "Chuyển khoản VietQR 24/7",
    "cod": "COD - Thanh toán khi nhận hàng",
    "cod - thanh toán khi nhận hàng": "COD - Thanh toán khi nhận hàng",
    "cod - thanh toán khi nhận máy": "COD - Thanh toán khi nhận hàng",
    "thanh toán khi nhận hàng": "COD - Thanh toán khi nhận hàng",
    "trả góp 0%": "Trả góp 0%",
    "tra gop 0%": "Trả góp 0%",
    "trả góp": "Trả góp 0%",
    "trả góp 0% qua thẻ tín dụng": "Trả góp 0%",
}

# Shopee Mall Flagship Brands
SHOPEE_MALL_BRANDS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Samsung",
        "official_name": "Samsung Official Store",
        "slug": "samsung",
        "tagline": "Ưu đãi đến 50% • Voucher 1 Triệu",
        "badge": "Shopee Mall",
        "logo_text": "SAMSUNG",
        "logo_url": "/static/shopee_assets/brands/samsung.png",
        "category": "Điện thoại & Thiết bị thông minh",
        "products_count": 128,
        "rating": 4.9,
    },
    {
        "id": 2,
        "name": "Apple Authorised Reseller",
        "official_name": "Apple Flagship Store VN",
        "slug": "apple",
        "tagline": "Chính hãng 100% • Bảo hành 12T",
        "badge": "Shopee Mall",
        "logo_text": "Authorised Reseller Apple",
        "logo_url": "/static/shopee_assets/brands/apple.png",
        "category": "Máy tính bảng & Laptop Studio",
        "products_count": 95,
        "rating": 5.0,
    },
    {
        "id": 3,
        "name": "Oppo",
        "official_name": "OPPO Official Store",
        "slug": "oppo",
        "tagline": "Chuyên gia chân dung • Trả góp 0%",
        "badge": "Shopee Mall",
        "logo_text": "oppo",
        "logo_url": "/static/shopee_assets/brands/oppo.png",
        "category": "Smartphone & Phụ kiện",
        "products_count": 64,
        "rating": 4.9,
    },
    {
        "id": 4,
        "name": "ShopDunk",
        "official_name": "ShopDunk - Đại lý ủy quyền Apple",
        "slug": "shopdunk",
        "tagline": "Giao siêu tốc 2h • Thu cũ đổi mới",
        "badge": "Shopee Mall",
        "logo_text": "ShopDunk",
        "logo_url": "/static/shopee_assets/brands/shopdunk.png",
        "category": "Hệ sinh thái Apple & Gaming",
        "products_count": 82,
        "rating": 4.8,
    },
    {
        "id": 5,
        "name": "Coocaa",
        "official_name": "Coocaa TV Official",
        "slug": "coocaa",
        "tagline": "Smart Google TV • Giá hủy diệt",
        "badge": "Shopee Mall",
        "logo_text": "coocaa",
        "logo_url": "/static/shopee_assets/brands/coocaa.png",
        "category": "Tivi & Thiết bị nghe nhìn",
        "products_count": 45,
        "rating": 4.8,
    },
    {
        "id": 6,
        "name": "SoundMax",
        "official_name": "SoundMax Audio Official",
        "slug": "soundmax",
        "tagline": "Âm thanh sống động • Bảo hành 24T",
        "badge": "Shopee Mall",
        "logo_text": "SOUNDMAX",
        "logo_url": "/static/shopee_assets/brands/soundmax.png",
        "category": "Loa & Thiết bị âm thanh",
        "products_count": 52,
        "rating": 4.7,
    },
]

# Structured hardware comparison specs for Flagship PCs (IDs 1..8)
FLAGSHIP_LINEUP_SPECS: List[Dict[str, Any]] = [
    {
        "id": 6,
        "product_id": 6,
        "sku": "TTG-PC-0006",
        "name": "PC TTG GAMING CORE ULTRA 7 270K PLUS - RTX 5070 12GB OC",
        "short_name": "Studio PC Pro Ultra 7",
        "tagline": "Hiệu năng đỉnh cao cho AI, dựng phim 8K và AAA Ray Tracing.",
        "badge": "MỚI • FLAGSHIP",
        "brand": "ASUS",
        "category": "PC Core Ultra",
        "price": 51_680_000.0,
        "old_price": 55_990_000.0,
        "discount": "-8%",
        "stock": 80,
        "image_url": "/static/ttg_assets/pc_6.png",
        "cpu": "Intel Core Ultra 7 270K Plus (20 nhân, 5.6GHz, NPU AI Boost)",
        "gpu": "ASUS ROG RTX 5070 12GB GDDR7 OC (DLSS 4 Multi-Frame)",
        "ram": "32GB DDR5 6400MHz Dual-Channel RGB",
        "ssd": "1TB NVMe PCIe Gen4 x4 (Đọc 7,200 MB/s)",
        "display_cooling": "Tản nước AIO 360mm LCD • Xuất 4 màn hình 4K/8K 240Hz",
        "cooling": "Tản nhiệt nước AIO 360mm ROG Ryujin ARGB",
        "display": "Hỗ trợ 4 màn hình 8K/4K 240Hz (DP 2.1 + HDMI 2.1b)",
        "psu_chassis": "850W 80 Plus Gold ATX 3.1 • Khung nhôm & kính Panoramic",
        "cloud_sla": "Multi-AZ Active-Active • RTO 1.46s • ACID SELECT FOR UPDATE",
        "warranty": "Bảo hành 36 tháng tận nơi • Hỗ trợ kỹ thuật 24/7",
    },
    {
        "id": 5,
        "product_id": 5,
        "sku": "TTG-PC-0005",
        "name": "PC TTG GAMING i5 14600KF - 16GB DDR4 - RTX 5070 12GB",
        "short_name": "Studio PC Pro RTX 5070",
        "tagline": "Sức mạnh đồ họa RTX 5070 12GB tối ưu cho Game thủ & Creator.",
        "badge": "MỚI • HI-END",
        "brand": "INTEL",
        "category": "PC GAMING CAO CẤP",
        "price": 44_480_000.0,
        "old_price": 48_990_000.0,
        "discount": "-9%",
        "stock": 95,
        "image_url": "/static/ttg_assets/pc_5.png",
        "cpu": "Intel Core i5-14600KF (14 nhân 20 luồng, Turbo 5.3GHz)",
        "gpu": "NVIDIA GeForce RTX 5070 12GB GDDR7 (Ray Tracing Gen 4)",
        "ram": "32GB DDR5/DDR4 High-Speed Dual-Channel",
        "ssd": "1TB NVMe PCIe Gen4 x4 (Đọc 7,000 MB/s)",
        "display_cooling": "Tản nước AIO 240mm ARGB • Xuất 4 màn hình 4K 240Hz",
        "cooling": "Tản nhiệt nước AIO 240mm Dual-Chamber ARGB",
        "display": "Hỗ trợ 4 màn hình 4K 240Hz (DP 2.1 + HDMI 2.1)",
        "psu_chassis": "750W 80 Plus Gold • Mid-Tower Airflow Studio",
        "cloud_sla": "Multi-AZ Active-Active • RTO 1.46s • ACID SELECT FOR UPDATE",
        "warranty": "Bảo hành chính hãng 36 tháng • 1 đổi 1 30 ngày",
    },
    {
        "id": 2,
        "product_id": 2,
        "sku": "TTG-PC-0002",
        "name": "PC TTG GAMING CORE ULTRA 5 250K PLUS - RTX 5060 8GB",
        "short_name": "Studio PC Air Ultra 5",
        "tagline": "Kiến trúc Core Ultra thế hệ mới, mát mẻ và tiết kiệm điện năng.",
        "badge": "MỚI • AI PC",
        "brand": "INTEL",
        "category": "PC Core Ultra",
        "price": 38_680_000.0,
        "old_price": 39_990_000.0,
        "discount": "-3%",
        "stock": 120,
        "image_url": "/static/ttg_assets/pc_2.png",
        "cpu": "Intel Core Ultra 5 250K Plus (14 nhân, 5.2GHz, NPU AI)",
        "gpu": "NVIDIA GeForce RTX 5060 8GB GDDR7 OC",
        "ram": "32GB DDR5 6000MHz Low-Latency",
        "ssd": "1TB NVMe PCIe Gen4 x4 SSD",
        "display_cooling": "Tản nước AIO 240mm • Hỗ trợ 3 màn hình 4K 165Hz",
        "cooling": "Tản nhiệt nước AIO 240mm Quiet Edition",
        "display": "Hỗ trợ 3 màn hình 4K 165Hz (DP 2.1 + HDMI 2.1)",
        "psu_chassis": "750W 80 Plus Bronze • Vỏ kính cường lực Panoramic",
        "cloud_sla": "Multi-AZ Active-Active • RTO 1.46s • ACID SELECT FOR UPDATE",
        "warranty": "Bảo hành chính hãng 36 tháng • Giao nhanh 2h",
    },
    {
        "id": 8,
        "product_id": 8,
        "sku": "TTG-PC-0008",
        "name": "PC TTG AMD GAMING RYZEN 5 7500X3D - RTX 5060 8GB",
        "short_name": "Gaming PC X3D Edition",
        "tagline": "Bộ nhớ đệm 3D V-Cache chuyên trị eSports FPS cao & Streaming.",
        "badge": "MỚI • 3D V-CACHE",
        "brand": "COLORFUL",
        "category": "PC ĐẸP",
        "price": 32_280_000.0,
        "old_price": 34_990_000.0,
        "discount": "-8%",
        "stock": 110,
        "image_url": "/static/ttg_assets/pc_8.png",
        "cpu": "AMD Ryzen 5 7500X3D (6 nhân 12 luồng, 96MB 3D V-Cache)",
        "gpu": "COLORFUL iGame RTX 5060 8GB GDDR7 Ultra W",
        "ram": "32GB DDR5 6000MHz AMD EXPO",
        "ssd": "1TB NVMe PCIe Gen4 x4 SSD",
        "display_cooling": "Tản khí Dual-Tower / AIO White • Xuất 3 màn hình 2K 360Hz",
        "cooling": "Tản nhiệt AIO 240mm White Snow Edition",
        "display": "Hỗ trợ 3 màn hình 2K 360Hz / 4K 144Hz",
        "psu_chassis": "700W 80 Plus • Case White Studio Panoramic",
        "cloud_sla": "Multi-AZ Active-Active • RTO 1.46s • ACID SELECT FOR UPDATE",
        "warranty": "Bảo hành chính hãng 36 tháng • Cân màu miễn phí",
    },
    {
        "id": 3,
        "product_id": 3,
        "sku": "TTG-PC-0003",
        "name": "PC TTG AMD GAMING PRO Ryzen 7 5700X - RTX 5060 8GB",
        "short_name": "Gaming PC Pro Ryzen 7",
        "tagline": "Cân bằng hoàn hảo giữa đa nhiệm 8 nhân và đồ họa RTX 5060.",
        "badge": "BÁN CHẠY",
        "brand": "AMD",
        "category": "PC GAMING PREMIUM",
        "price": 25_480_000.0,
        "old_price": 27_990_000.0,
        "discount": "-9%",
        "stock": 135,
        "image_url": "/static/ttg_assets/pc_3.png",
        "cpu": "AMD Ryzen 7 5700X (8 nhân 16 luồng, Boost 4.6GHz)",
        "gpu": "NVIDIA GeForce RTX 5060 8GB GDDR7",
        "ram": "16GB DDR4 3600MHz Dual-Channel (Nâng cấp 64GB)",
        "ssd": "512GB NVMe PCIe Gen4 x4 SSD",
        "display_cooling": "Tản khí 6 ống đồng ARGB • Xuất 3 màn hình 2K 240Hz",
        "cooling": "Tản nhiệt khí 6 ống đồng Tower ARGB",
        "display": "Hỗ trợ 3 màn hình 2K 240Hz / 4K 120Hz",
        "psu_chassis": "650W 80 Plus • Vỏ kính cường lực 4 Fan ARGB",
        "cloud_sla": "Multi-AZ Active-Active • RTO 1.46s • ACID SELECT FOR UPDATE",
        "warranty": "Bảo hành chính hãng 36 tháng",
    },
    {
        "id": 7,
        "product_id": 7,
        "sku": "TTG-PC-0007",
        "name": "PC TTG ULTRA GAMING I5 14400F - RTX 5050 8GB",
        "short_name": "Studio Stream i5 14400F",
        "tagline": "Khởi đầu mượt mà cho Streamer, chỉnh sửa ảnh và Gaming 1080p/2K.",
        "badge": "STREAMING",
        "brand": "INTEL",
        "category": "PC STREAM GAME",
        "price": 22_980_000.0,
        "old_price": 25_990_000.0,
        "discount": "-12%",
        "stock": 160,
        "image_url": "/static/ttg_assets/pc_7.png",
        "cpu": "Intel Core i5-14400F (10 nhân 16 luồng, Turbo 4.7GHz)",
        "gpu": "NVIDIA GeForce RTX 5050 8GB GDDR6 (NVENC AV1)",
        "ram": "16GB DDR4 3200MHz Dual-Channel",
        "ssd": "512GB NVMe PCIe Gen4 SSD",
        "display_cooling": "Tản khí 4 ống đồng • Xuất 3 màn hình FullHD/2K 180Hz",
        "cooling": "Tản nhiệt khí 4 ống đồng Silent PWM",
        "display": "Hỗ trợ 3 màn hình 2K 180Hz",
        "psu_chassis": "650W 80 Plus • Mid-Tower Mesh Airflow",
        "cloud_sla": "Multi-AZ Active-Active • RTO 1.46s • ACID SELECT FOR UPDATE",
        "warranty": "Bảo hành chính hãng 36 tháng",
    },
    {
        "id": 4,
        "product_id": 4,
        "sku": "TTG-PC-0004",
        "name": "PC TTG AMD GAMING PRO Ryzen 7 5700X - RTX 5050 8GB OC",
        "short_name": "Gaming Pro R7 5700X",
        "tagline": "8 nhân xử lý đa tác vụ cùng GPU RTX 5050 OC tối ưu chi phí.",
        "badge": "ƯU ĐÃI -15%",
        "brand": "AMD",
        "category": "PC STREAM GAME",
        "price": 22_280_000.0,
        "old_price": 25_990_000.0,
        "discount": "-15%",
        "stock": 140,
        "image_url": "/static/ttg_assets/pc_4.png",
        "cpu": "AMD Ryzen 7 5700X (8 nhân 16 luồng, 36MB Cache)",
        "gpu": "NVIDIA GeForce RTX 5050 8GB OC Dual-Fan",
        "ram": "16GB DDR4 3600MHz Dual-Channel",
        "ssd": "512GB NVMe PCIe Gen4 SSD",
        "display_cooling": "Tản khí CR-1000 ARGB • Xuất 3 màn hình 2K 165Hz",
        "cooling": "Tản nhiệt khí Tower ARGB PWM",
        "display": "Hỗ trợ 3 màn hình 2K 165Hz",
        "psu_chassis": "650W 80 Plus • Vỏ kính cường lực 3 Fan RGB",
        "cloud_sla": "Multi-AZ Active-Active • RTO 1.46s • ACID SELECT FOR UPDATE",
        "warranty": "Bảo hành chính hãng 36 tháng",
    },
    {
        "id": 1,
        "product_id": 1,
        "sku": "TTG-PC-0001",
        "name": "PC TTG AMD Ryzen 5 5500 - RTX 5050 8GB OC",
        "short_name": "Gaming SE Ryzen 5",
        "tagline": "Cấu hình quốc dân giá tốt nhất dòng RTX 50 Series.",
        "badge": "TIẾT KIỆM -18%",
        "brand": "AMD",
        "category": "PC GAMING GIÁ RẺ",
        "price": 20_480_000.0,
        "old_price": 24_990_000.0,
        "discount": "-18%",
        "stock": 150,
        "image_url": "/static/ttg_assets/pc_1.png",
        "cpu": "AMD Ryzen 5 5500 (6 nhân 12 luồng, Boost 4.2GHz)",
        "gpu": "NVIDIA GeForce RTX 5050 8GB OC GDDR6",
        "ram": "16GB DDR4 3200MHz Dual-Channel",
        "ssd": "512GB NVMe PCIe M.2 SSD",
        "display_cooling": "Tản khí Wraith Stealth / Tower • Xuất 2 màn hình 180Hz",
        "cooling": "Tản nhiệt khí tiêu chuẩn + 3 Fan Case",
        "display": "Hỗ trợ 2 màn hình FullHD/2K 180Hz",
        "psu_chassis": "600W Công suất thực • Case Gaming Compact",
        "cloud_sla": "Multi-AZ Active-Active • RTO 1.46s • ACID SELECT FOR UPDATE",
        "warranty": "Bảo hành chính hãng 36 tháng",
    },
]

_fallback_sqlite_lock = threading.Lock()
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_SQLITE_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(_APP_DIR, "ecommerce_local.db"))


def _seed_initial_telemetry() -> None:
    now_str = time.strftime("%H:%M:%S")
    iso_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    initial_events = [
        {
            "timestamp": now_str,
            "iso_time": iso_str,
            "bee": "shopee-ui",
            "bee_name": "Shopee Mall UI",
            "event_type": "SHOPEE_UI_READY",
            "message": "Khởi tạo giao diện Shopee Mall Vietnam (Header Cam, Flash Sale, Mall Ribbon & Giỏ hàng).",
            "served_by": "app-replica-1 (AZ-a)",
            "db_lock_mode": "ACID SELECT ... FOR UPDATE",
        },
        {
            "timestamp": now_str,
            "iso_time": iso_str,
            "bee": "shopee-backend",
            "bee_name": "ACID Checkout Engine",
            "event_type": "DB_LOCK_READY",
            "message": "Sẵn sàng khóa dòng ACID (SELECT ... FOR UPDATE / BEGIN IMMEDIATE) & voucher SHOPEE2026/SHOPEE500K.",
            "served_by": "app-replica-1 (AZ-a)",
            "db_lock_mode": "ACID SELECT ... FOR UPDATE",
        },
        {
            "timestamp": now_str,
            "iso_time": iso_str,
            "bee": "shopee-qa",
            "bee_name": "Load QA 500 Probes",
            "event_type": "LOAD_PROBES_STANDBY",
            "message": "Sẵn sàng kịch bản 500 concurrent requests Shopee Flash Sale (Zero Overselling).",
            "served_by": "app-replica-2 (AZ-b)",
            "db_lock_mode": "ACID SELECT ... FOR UPDATE",
        },
        {
            "timestamp": now_str,
            "iso_time": iso_str,
            "bee": "shopee-reviewer",
            "bee_name": "Security Shield",
            "event_type": "SECURITY_SHIELD_ACTIVE",
            "message": "Đã bật kiểm tra XSS Sanitization, SQL Parameter Binding & Non-Root UID 10001.",
            "served_by": "app-replica-2 (AZ-b)",
            "db_lock_mode": "ACID SELECT ... FOR UPDATE",
        },
    ]
    with _telemetry_lock:
        if not SWARM_TELEMETRY_LOG:
            for ev in initial_events:
                SWARM_TELEMETRY_LOG.append(ev)


_seed_initial_telemetry()


def _get_main_module():
    """ Dynamically resolve the active main module regardless of how uvicorn was invoked. """
    for mod_name in ("app.main", "main", "__main__"):
        mod = sys.modules.get(mod_name)
        if mod is not None and hasattr(mod, "SQLITE_DB_PATH") and hasattr(mod, "resolve_serving_node"):
            return mod
    try:
        from app import main as mod  # type: ignore
        return mod
    except ImportError:
        try:
            import main as mod  # type: ignore
            return mod
        except ImportError:
            return None


def _get_runtime_context(request: Request) -> Dict[str, Any]:
    mod = _get_main_module()
    if mod is not None:
        if getattr(mod, "active_db_mode", "uninitialized") == "uninitialized" and hasattr(mod, "init_db_pool"):
            mod.init_db_pool()
        node = getattr(request.state, "served_by", None) or mod.resolve_serving_node()
        return {
            "mod": mod,
            "node": node,
            "arch_version": getattr(mod, "ARCH_VERSION", "V2-Well-Architected"),
            "active_db_mode": getattr(mod, "active_db_mode", "sqlite"),
            "db_pool": getattr(mod, "db_pool", None),
            "sqlite_lock": getattr(mod, "sqlite_lock", _fallback_sqlite_lock),
            "sqlite_db_path": getattr(mod, "SQLITE_DB_PATH", _DEFAULT_SQLITE_PATH),
            "orders_counter": getattr(mod, "ORDERS_CREATED", None),
        }
    node = getattr(request.state, "served_by", None) or os.getenv("NODE_ID", "app-replica-1 (AZ-a)")
    return {
        "mod": None,
        "node": node,
        "arch_version": os.getenv("ARCH_VERSION", "V2-Well-Architected"),
        "active_db_mode": "sqlite",
        "db_pool": None,
        "sqlite_lock": _fallback_sqlite_lock,
        "sqlite_db_path": _DEFAULT_SQLITE_PATH,
        "orders_counter": None,
    }


def _sanitize_text(val: Optional[str], default: str = "", max_len: int = 250) -> str:
    if not val:
        return default
    cleaned = html.escape(str(val).strip(), quote=True)
    return cleaned[:max_len] if cleaned else default


def _normalize_payment_method(raw_payment: Optional[str]) -> str:
    cleaned = _sanitize_text(raw_payment, default="Ví ShopeePay", max_len=120)
    lowered = cleaned.lower().strip()
    if lowered in PAYMENT_METHOD_ALIASES:
        return PAYMENT_METHOD_ALIASES[lowered]
    for method in SUPPORTED_PAYMENT_METHODS:
        if method.lower() == lowered:
            return method
    return cleaned


class CheckoutItemInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_id: Optional[int] = Field(default=None, gt=0)
    id: Optional[int] = Field(default=None, gt=0)
    quantity: int = Field(default=1, gt=0, le=50)

    @property
    def resolved_product_id(self) -> int:
        pid = self.product_id if self.product_id is not None else self.id
        if not pid or pid <= 0:
            raise HTTPException(status_code=400, detail="Mã sản phẩm (product_id) không hợp lệ")
        return int(pid)


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    customer_name: str = Field(default="Khách hàng Shopee Mall", min_length=1, max_length=120)
    phone: Optional[str] = Field(default="0909123456", max_length=30)
    address: Optional[str] = Field(default="TP. Hồ Chí Minh", max_length=300)
    payment_method: Optional[str] = Field(default="Ví ShopeePay", max_length=120)
    promo_code: Optional[str] = Field(default="", max_length=50)
    discount_code: Optional[str] = Field(default="", max_length=50)
    items: Optional[List[CheckoutItemInput]] = Field(default=None)
    # Single-item fallback fields for callers posting {product_id, quantity} directly
    product_id: Optional[int] = Field(default=None, gt=0)
    quantity: Optional[int] = Field(default=1, gt=0, le=50)


@router.post("/api/checkout", status_code=201)
def checkout_cart(payload: CheckoutRequest, request: Request):
    """
    Executes an atomic multi-item ACID checkout transaction for Shopee Mall:
    - PostgreSQL: `SELECT id, name, price, stock FROM products WHERE id = %s FOR UPDATE`
    - SQLite: `BEGIN IMMEDIATE` inside `sqlite_lock`
    - Locks rows in deterministic ascending `product_id` order to prevent deadlocks.
    - Validates stock for all items; rolls back the entire transaction if any item has insufficient stock.
    - Applies Shopee promo vouchers (`SHOPEE2026` -> -1,500,000 VND; `SHOPEE500K` -> -500,000 VND;
      `UTH2026` -> -1,000,000 VND; `TTG500K` -> -500,000 VND; `APPLE2026` -> -1,500,000 VND).
    - Supports payment methods: `Ví ShopeePay`, `Apple Pay`, `Chuyển khoản VietQR 24/7`,
      `COD - Thanh toán khi nhận hàng`, `Trả góp 0%`.
    - Inserts into `orders`, decrements `products.stock`, and logs telemetry to `SWARM_TELEMETRY_LOG`.
    """
    ctx = _get_runtime_context(request)
    node = ctx["node"]
    arch_version = ctx["arch_version"]
    db_mode = ctx["active_db_mode"]
    db_pool = ctx["db_pool"]
    sqlite_lock = ctx["sqlite_lock"]
    sqlite_db_path = ctx["sqlite_db_path"]
    orders_counter = ctx["orders_counter"]

    raw_items: List[CheckoutItemInput] = []
    if payload.items:
        raw_items = list(payload.items)
    elif payload.product_id is not None:
        raw_items = [CheckoutItemInput(product_id=payload.product_id, quantity=payload.quantity or 1)]

    if not raw_items:
        raise HTTPException(status_code=400, detail="Giỏ hàng trống, vui lòng chọn ít nhất 1 sản phẩm")

    clean_customer = _sanitize_text(payload.customer_name, default="Khách hàng Shopee Mall", max_len=120)
    clean_phone = _sanitize_text(payload.phone, default="0909123456", max_len=30)
    clean_address = _sanitize_text(payload.address, default="TP. Hồ Chí Minh", max_len=250)
    clean_payment = _normalize_payment_method(payload.payment_method)
    raw_promo = (payload.promo_code or payload.discount_code or "").strip().upper()
    clean_promo = _sanitize_text(raw_promo, default="", max_len=30).upper()

    # Aggregate requested quantities by product_id while preserving item order
    requested_totals: Dict[int, int] = {}
    normalized_items: List[Dict[str, int]] = []
    for item in raw_items:
        pid = item.resolved_product_id
        qty = int(item.quantity)
        requested_totals[pid] = requested_totals.get(pid, 0) + qty
        normalized_items.append({"product_id": pid, "quantity": qty})

    # Sort product_ids ascending to guarantee deterministic lock acquisition and prevent deadlock
    sorted_pids = sorted(requested_totals.keys())
    order_ids: List[int] = []
    items_processed: List[Dict[str, Any]] = []
    total_amount = 0.0
    discount_applied = 0.0
    final_amount = 0.0

    if db_mode == "postgres" and db_pool is not None:
        conn = db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                locked_products: Dict[int, Dict[str, Any]] = {}
                for pid in sorted_pids:
                    cur.execute(
                        "SELECT id, name, price, stock FROM products WHERE id = %s FOR UPDATE;",
                        (pid,)
                    )
                    prod = cur.fetchone()
                    if not prod:
                        conn.rollback()
                        raise HTTPException(status_code=404, detail=f"Sản phẩm #{pid} không tồn tại")
                    locked_products[pid] = dict(prod)

                # Validate stock sufficiency across all items
                for pid, req_qty in requested_totals.items():
                    prod = locked_products[pid]
                    if int(prod["stock"]) < req_qty:
                        conn.rollback()
                        raise HTTPException(
                            status_code=400,
                            detail=f"Sản phẩm '{prod['name']}' đã hết hoặc không đủ tồn kho (còn {prod['stock']}, yêu cầu {req_qty})"
                        )

                # Compute totals
                for entry in normalized_items:
                    pid = entry["product_id"]
                    qty = entry["quantity"]
                    prod = locked_products[pid]
                    total_amount += float(prod["price"]) * qty

                if clean_promo in PROMO_DISCOUNTS:
                    discount_applied = min(PROMO_DISCOUNTS[clean_promo], total_amount)
                final_amount = max(0.0, total_amount - discount_applied)

                # Update stock and record orders
                for entry in normalized_items:
                    pid = entry["product_id"]
                    qty = entry["quantity"]
                    prod = locked_products[pid]
                    unit_price = float(prod["price"])
                    line_total = unit_price * qty

                    cur.execute(
                        "UPDATE products SET stock = stock - %s WHERE id = %s;",
                        (qty, pid)
                    )
                    prod["stock"] = int(prod["stock"]) - qty

                    cur.execute(
                        "INSERT INTO orders (customer_name, product_id, quantity, total_amount, served_by_node) "
                        "VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at;",
                        (clean_customer, pid, qty, line_total, node)
                    )
                    order_row = cur.fetchone()
                    oid = int(order_row["id"])
                    order_ids.append(oid)
                    items_processed.append({
                        "order_id": oid,
                        "product_id": pid,
                        "product_name": prod["name"],
                        "name": prod["name"],
                        "quantity": qty,
                        "unit_price": unit_price,
                        "price": unit_price,
                        "line_total": line_total,
                        "remaining_stock": int(prod["stock"]),
                    })

                conn.commit()
        except HTTPException:
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Lỗi giao dịch ACID PostgreSQL: {str(e)}")
        finally:
            db_pool.putconn(conn)
    else:
        with sqlite_lock:
            conn = sqlite3.connect(sqlite_db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("BEGIN IMMEDIATE;")
                cur = conn.cursor()

                locked_products = {}
                for pid in sorted_pids:
                    cur.execute(
                        "SELECT id, name, price, stock FROM products WHERE id = ?;",
                        (pid,)
                    )
                    row = cur.fetchone()
                    if not row:
                        conn.rollback()
                        raise HTTPException(status_code=404, detail=f"Sản phẩm #{pid} không tồn tại")
                    locked_products[pid] = dict(row)

                # Validate stock sufficiency across all items
                for pid, req_qty in requested_totals.items():
                    prod = locked_products[pid]
                    if int(prod["stock"]) < req_qty:
                        conn.rollback()
                        raise HTTPException(
                            status_code=400,
                            detail=f"Sản phẩm '{prod['name']}' đã hết hoặc không đủ tồn kho (còn {prod['stock']}, yêu cầu {req_qty})"
                        )

                # Compute totals
                for entry in normalized_items:
                    pid = entry["product_id"]
                    qty = entry["quantity"]
                    prod = locked_products[pid]
                    total_amount += float(prod["price"]) * qty

                if clean_promo in PROMO_DISCOUNTS:
                    discount_applied = min(PROMO_DISCOUNTS[clean_promo], total_amount)
                final_amount = max(0.0, total_amount - discount_applied)

                # Update stock and record orders
                for entry in normalized_items:
                    pid = entry["product_id"]
                    qty = entry["quantity"]
                    prod = locked_products[pid]
                    unit_price = float(prod["price"])
                    line_total = unit_price * qty

                    cur.execute(
                        "UPDATE products SET stock = stock - ? WHERE id = ?;",
                        (qty, pid)
                    )
                    prod["stock"] = int(prod["stock"]) - qty

                    cur.execute(
                        "INSERT INTO orders (customer_name, product_id, quantity, total_amount, served_by_node) "
                        "VALUES (?, ?, ?, ?, ?);",
                        (clean_customer, pid, qty, line_total, node)
                    )
                    oid = int(cur.lastrowid)
                    order_ids.append(oid)
                    items_processed.append({
                        "order_id": oid,
                        "product_id": pid,
                        "product_name": prod["name"],
                        "name": prod["name"],
                        "quantity": qty,
                        "unit_price": unit_price,
                        "price": unit_price,
                        "line_total": line_total,
                        "remaining_stock": int(prod["stock"]),
                    })

                conn.commit()
            except HTTPException:
                raise
            except Exception as e:
                conn.rollback()
                raise HTTPException(status_code=500, detail=f"Lỗi giao dịch ACID SQLite: {str(e)}")
            finally:
                conn.close()

    if orders_counter is not None:
        try:
            orders_counter.labels(node_id=node).inc(len(order_ids))
        except Exception:
            pass

    applied_promo = clean_promo if clean_promo in PROMO_DISCOUNTS else ""
    event_entry = {
        "timestamp": time.strftime("%H:%M:%S"),
        "iso_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "bee": "shopee-backend",
        "bee_name": "ACID Checkout Engine",
        "event_type": "ACID_CHECKOUT_COMMIT",
        "message": (
            f"[SHOPEE ACID COMMIT] Đơn #{','.join(str(i) for i in order_ids)} • "
            f"{clean_customer} • {clean_payment} • {int(final_amount):,} VNĐ • Node: {node}"
        ),
        "order_ids": order_ids,
        "customer_name": clean_customer,
        "items_count": len(items_processed),
        "total_amount": total_amount,
        "discount_applied": discount_applied,
        "final_amount": final_amount,
        "promo_code": applied_promo,
        "payment_method": clean_payment,
        "served_by": node,
        "db_lock_mode": "ACID SELECT ... FOR UPDATE" if db_mode == "postgres" else "ACID BEGIN IMMEDIATE",
    }
    with _telemetry_lock:
        SWARM_TELEMETRY_LOG.append(event_entry)

    first_remaining = items_processed[0]["remaining_stock"] if items_processed else 0
    first_product_name = items_processed[0]["product_name"] if items_processed else ""

    return {
        "status": "success",
        "message": "Đặt hàng thành công qua giao dịch ACID Shopee Mall!",
        "order_ids": order_ids,
        "order_id": order_ids[0] if order_ids else None,
        "customer_name": clean_customer,
        "phone": clean_phone,
        "address": clean_address,
        "payment_method": clean_payment,
        "promo_code": applied_promo,
        "total_amount": total_amount,
        "discount_applied": discount_applied,
        "final_amount": final_amount,
        "remaining_stock": first_remaining,
        "product_name": first_product_name,
        "served_by": node,
        "architecture": arch_version,
        "db_lock_mode": "ACID SELECT ... FOR UPDATE" if db_mode == "postgres" else "ACID BEGIN IMMEDIATE",
        "items_processed": items_processed,
    }


@router.get("/api/shopee/mall-brands")
def get_shopee_mall_brands(request: Request):
    """
    Returns the official Shopee Mall flagship brand partners
    (Samsung, Apple Authorised Reseller, Oppo, ShopDunk, Coocaa, SoundMax)
    along with active Shopee promo vouchers and supported payment methods.
    """
    ctx = _get_runtime_context(request)
    node = ctx["node"]
    arch_version = ctx["arch_version"]

    return {
        "status": "ok",
        "title": "Shopee Mall - Thương Hiệu Chính Hãng 100%",
        "subtitle": "Miễn phí vận chuyển • 7 ngày trả hàng miễn phí • 100% hàng chính hãng",
        "served_by": node,
        "architecture": arch_version,
        "count": len(SHOPEE_MALL_BRANDS),
        "brands": SHOPEE_MALL_BRANDS,
        "mall_brands": SHOPEE_MALL_BRANDS,
        "items": SHOPEE_MALL_BRANDS,
        "promo_vouchers": PROMO_METADATA,
        "promo_discounts": PROMO_DISCOUNTS,
        "supported_payment_methods": SUPPORTED_PAYMENT_METHODS,
    }


@router.get("/api/lineup/compare")
def compare_flagship_lineup(request: Request, limit: int = 8):
    """
    Returns structured comparison specs for the flagship PC lineup
    (CPU, GPU, RAM, SSD, Display/Cooling, Cloud SLA, Price, Live Stock, Image URL).
    Maintained for backward compatibility and comparison drawers.
    """
    safe_limit = max(1, min(int(limit), 8))
    ctx = _get_runtime_context(request)
    node = ctx["node"]
    arch_version = ctx["arch_version"]
    db_mode = ctx["active_db_mode"]
    db_pool = ctx["db_pool"]
    sqlite_db_path = ctx["sqlite_db_path"]

    # Fetch live stock & price from database for flagship product IDs 1..8
    live_db_map: Dict[int, Dict[str, Any]] = {}
    try:
        if db_mode == "postgres" and db_pool is not None:
            conn = db_pool.getconn()
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT id, sku, name, category, price, stock, image_key "
                        "FROM products WHERE id <= 8 ORDER BY id;"
                    )
                    for r in cur.fetchall():
                        row_d = dict(r)
                        live_db_map[int(row_d["id"])] = row_d
            finally:
                db_pool.putconn(conn)
        else:
            conn = sqlite3.connect(sqlite_db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, sku, name, category, price, stock, image_key "
                    "FROM products WHERE id <= 8 ORDER BY id;"
                )
                for r in cur.fetchall():
                    row_d = dict(r)
                    live_db_map[int(row_d["id"])] = row_d
            finally:
                conn.close()
    except Exception:
        pass

    comparison_models: List[Dict[str, Any]] = []
    for base_spec in FLAGSHIP_LINEUP_SPECS[:safe_limit]:
        item = dict(base_spec)
        pid = int(item["id"])
        if pid in live_db_map:
            db_row = live_db_map[pid]
            item["name"] = db_row.get("name") or item["name"]
            item["sku"] = db_row.get("sku") or item["sku"]
            item["category"] = db_row.get("category") or item["category"]
            item["price"] = float(db_row.get("price", item["price"]))
            item["stock"] = int(db_row.get("stock", item["stock"]))
            img_key = str(db_row.get("image_key", ""))
            if img_key.startswith("/static/"):
                item["image_url"] = img_key

        monthly = int(round(item["price"] / 24.0, -3))
        item["monthly_installment"] = f"Từ {monthly:,}đ/tháng với trả góp 0%".replace(",", ".")
        item["specs"] = {
            "cpu": item["cpu"],
            "gpu": item["gpu"],
            "ram": item["ram"],
            "ssd": item["ssd"],
            "display_cooling": item["display_cooling"],
            "cooling": item["cooling"],
            "display": item["display"],
            "psu_chassis": item["psu_chassis"],
            "cloud_sla": item["cloud_sla"],
            "warranty": item["warranty"],
        }
        comparison_models.append(item)

    spec_categories = [
        {"key": "cpu", "label": "Vi xử lý (CPU & AI Boost)"},
        {"key": "gpu", "label": "Đồ họa (GPU RTX 50 Series)"},
        {"key": "ram", "label": "Bộ nhớ RAM DDR5 High-Speed"},
        {"key": "ssd", "label": "Lưu trữ Flash NVMe Gen4 SSD"},
        {"key": "display_cooling", "label": "Màn hình hỗ trợ & Tản nhiệt"},
        {"key": "psu_chassis", "label": "Nguồn & Khung vỏ Case Panoramic"},
        {"key": "cloud_sla", "label": "Hạ tầng Cloud & Bảo toàn kho ACID"},
        {"key": "warranty", "label": "Bảo hành & Hỗ trợ kỹ thuật 24/7"},
    ]

    return {
        "status": "ok",
        "title": "So sánh các phiên bản PC Gaming & Shopee Mall.",
        "subtitle": "Khám phá cấu hình phù hợp nhất với nhu cầu đồ họa, AI và eSports của bạn.",
        "served_by": node,
        "architecture": arch_version,
        "database_engine": db_mode,
        "db_lock_mode": "ACID SELECT ... FOR UPDATE" if db_mode == "postgres" else "ACID BEGIN IMMEDIATE",
        "count": len(comparison_models),
        "items": comparison_models,
        "lineup": comparison_models,
        "models": comparison_models,
        "featured_4": comparison_models[:4],
        "spec_categories": spec_categories,
        "promo_codes": PROMO_METADATA,
        "payment_methods": SUPPORTED_PAYMENT_METHODS,
    }


@router.get("/api/orders/recent")
def get_recent_orders(request: Request, limit: int = 10):
    """
    Returns the most recent orders from the `orders` table + total orders count.
    """
    safe_limit = max(1, min(int(limit), 50))
    ctx = _get_runtime_context(request)
    node = ctx["node"]
    arch_version = ctx["arch_version"]
    db_mode = ctx["active_db_mode"]
    db_pool = ctx["db_pool"]
    sqlite_db_path = ctx["sqlite_db_path"]

    recent_orders: List[Dict[str, Any]] = []
    total_orders = 0

    if db_mode == "postgres" and db_pool is not None:
        conn = db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM orders;")
                total_orders = int(cur.fetchone()["cnt"])
                cur.execute(
                    """
                    SELECT o.id, o.customer_name, o.product_id,
                           COALESCE(p.name, 'PC Gaming TTG #' || o.product_id::text) AS product_name,
                           o.quantity, o.total_amount, o.served_by_node, o.created_at
                    FROM orders o
                    LEFT JOIN products p ON o.product_id = p.id
                    ORDER BY o.id DESC
                    LIMIT %s;
                    """,
                    (safe_limit,)
                )
                for r in cur.fetchall():
                    row_dict = dict(r)
                    row_dict["total_amount"] = float(row_dict["total_amount"])
                    row_dict["created_at"] = str(row_dict.get("created_at", ""))
                    recent_orders.append(row_dict)
        finally:
            db_pool.putconn(conn)
    else:
        conn = sqlite3.connect(sqlite_db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            total_orders = int(cur.execute("SELECT COUNT(*) FROM orders;").fetchone()[0])
            cur.execute(
                """
                SELECT o.id, o.customer_name, o.product_id,
                       COALESCE(p.name, 'PC Gaming TTG #' || o.product_id) AS product_name,
                       o.quantity, o.total_amount, o.served_by_node, o.created_at
                FROM orders o
                LEFT JOIN products p ON o.product_id = p.id
                ORDER BY o.id DESC
                LIMIT ?;
                """,
                (safe_limit,)
            )
            for r in cur.fetchall():
                row_dict = dict(r)
                row_dict["total_amount"] = float(row_dict["total_amount"])
                row_dict["created_at"] = str(row_dict.get("created_at", ""))
                recent_orders.append(row_dict)
        finally:
            conn.close()

    return {
        "status": "ok",
        "served_by": node,
        "architecture": arch_version,
        "total_orders": total_orders,
        "count": len(recent_orders),
        "orders": recent_orders,
        "recent_orders": recent_orders,
    }


@router.get("/api/swarm/telemetry")
def get_swarm_telemetry(request: Request):
    """
    Returns live backend metrics, Shopee vouchers, and recent ACID checkout logs.
    """
    ctx = _get_runtime_context(request)
    node = ctx["node"]
    arch_version = ctx["arch_version"]
    db_mode = ctx["active_db_mode"]
    db_pool = ctx["db_pool"]
    sqlite_db_path = ctx["sqlite_db_path"]

    total_orders = 0
    total_stock = 0

    try:
        if db_mode == "postgres" and db_pool is not None:
            conn = db_pool.getconn()
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT COUNT(*) AS cnt FROM orders;")
                    total_orders = int(cur.fetchone()["cnt"])
                    cur.execute("SELECT COALESCE(SUM(stock), 0) AS stk FROM products;")
                    total_stock = int(cur.fetchone()["stk"])
            finally:
                db_pool.putconn(conn)
        else:
            conn = sqlite3.connect(sqlite_db_path, timeout=30.0)
            try:
                cur = conn.cursor()
                total_orders = int(cur.execute("SELECT COUNT(*) FROM orders;").fetchone()[0])
                total_stock = int(cur.execute("SELECT COALESCE(SUM(stock), 0) FROM products;").fetchone()[0])
            finally:
                conn.close()
    except Exception:
        pass

    with _telemetry_lock:
        events_snapshot = list(reversed(SWARM_TELEMETRY_LOG))

    return {
        "status": "ok",
        "active_bees": 4,
        "db_lock_mode": "ACID SELECT ... FOR UPDATE" if db_mode == "postgres" else "ACID BEGIN IMMEDIATE",
        "database_engine": db_mode,
        "served_by": node,
        "architecture": arch_version,
        "total_orders": total_orders,
        "total_stock_remaining": total_stock,
        "promo_discounts": PROMO_DISCOUNTS,
        "promo_vouchers": PROMO_METADATA,
        "supported_payment_methods": SUPPORTED_PAYMENT_METHODS,
        "recent_events": events_snapshot,
        "bees": [
            {
                "id": "shopee-ui",
                "name": "Shopee Mall UI",
                "color": "#ee4d2d",
                "status": "ACTIVE",
                "task": "Shopee Orange Header, Flash Sale, Mall Ribbon & Cart Drawer",
            },
            {
                "id": "shopee-backend",
                "name": "ACID Checkout Engine",
                "color": "#10b981",
                "status": "ACTIVE",
                "task": "Khóa dòng ACID (SELECT ... FOR UPDATE) & Mã Shopee Voucher",
            },
            {
                "id": "shopee-qa",
                "name": "Load QA 500 Probes",
                "color": "#f59e0b",
                "status": "ACTIVE",
                "task": "Kiểm thử tải 500 requests & kiểm định không bán âm kho",
            },
            {
                "id": "shopee-reviewer",
                "name": "Security & Code Reviewer",
                "color": "#a855f7",
                "status": "ACTIVE",
                "task": "Thẩm định bảo mật XSS, SQLi, ACID integrity & Non-Root UID 10001",
            },
        ],
    }
