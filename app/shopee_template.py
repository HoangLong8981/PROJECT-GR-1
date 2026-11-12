# -*- coding: utf-8 -*-
"""
Shopee Vietnam (shopee.vn) E-Commerce Storefront HTML Template
Owned by: Worker 1 (@shopee-ui)
Replicates the authentic Shopee Vietnam web interface:
- Signature Shopee Orange theme (#ee4d2d, #f53d2d, #ff6533)
- Top Bar (Kênh Người Bán, Tải ứng dụng, Kết nối, Thông báo 9+, Hỗ Trợ, Tiếng Việt, vqp5u19dtu)
- Main Header with Shopee Bag Logo, Category Dropdown, Search Input, Suggestion Tags, Cart Badge
- Cloud Well-Architected V2 Live Drawer (#cloud-drawer, Multi-AZ, Load Balancer & Chaos Test)
- Hero Banner Carousel (Edifier BẬT NHẠC HAY BẬT CHẤT NGAY, Voucher 20%, BH 15 tháng, Freeship)
- Quick Access Service Icons
- SHOPEE MALL Brand Ribbon (Samsung, Apple Authorised Reseller, Oppo, ShopDunk, Coocaa, SoundMax)
- Flash Sale Section with Countdown Timer
- Gợi Ý Hôm Nay Tabs & Dynamic Shopee Product Cards (Mall/Yêu thích tag, -18% GIẢM, Freeship Xtra, Đã bán 1.2k)
- Floating Chat Widget (Bottom-Right corner)
- Shopee Cart & ACID Checkout Modal (#shopee-checkout-modal, SHOPEE2026, ShopeePay, Apple Pay, VietQR)
"""

import html


def render_shopee_store_html(
    node: str = "app-replica-1 (AZ-a)",
    arch_version: str = "V2-Well-Architected",
) -> str:
    """Render the complete Shopee Vietnam PC Gaming & Electronics storefront HTML."""
    safe_node = html.escape(str(node or "app-replica-1 (AZ-a)"), quote=True)
    safe_arch = html.escape(str(arch_version or "V2-Well-Architected"), quote=True)

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shopee Việt Nam | Mua Và Bán Trên Ứng Dụng Di Động Hoặc Website</title>
    <link rel="icon" type="image/x-icon" href="https://deo.shopeemobile.com/shopee/shopee-pcmall-live-sg/assets/icon_favicon_1_32.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/shopee_store.css">
</head>
<body class="shopee-body">
    <!-- ===================================================================
         1. SHOPEE TOP BAR & MAIN HEADER (ORANGE GRADIENT)
         =================================================================== -->
    <header class="shopee-header-wrap">
        <!-- Top Navigation Bar -->
        <div class="shopee-topbar">
            <div class="shopee-container shopee-topbar-inner">
                <!-- Left Links -->
                <div class="shopee-topbar-left">
                    <a href="#" class="shopee-topbar-link">Kênh Người Bán</a>
                    <span class="shopee-topbar-sep">|</span>
                    <div class="shopee-topbar-app-wrap">
                        <a href="#" class="shopee-topbar-link">Tải ứng dụng</a>
                        <!-- QR Code Popover -->
                        <div class="shopee-qr-popover">
                            <div class="shopee-qr-box">
                                <svg class="shopee-qr-svg" viewBox="0 0 100 100">
                                    <rect x="0" y="0" width="100" height="100" fill="#fff"/>
                                    <path d="M10 10h30v30h-30z M15 15h20v20h-20z M20 20h10v10h-10z M60 10h30v30h-30z M65 15h20v20h-20z M70 20h10v10h-10z M10 60h30v30h-30z M15 65h20v20h-20z M20 70h10v10h-10z M45 15h10v10h-10z M45 35h10v10h-10z M15 45h10v10h-10z M35 45h10v10h-10z M55 45h10v10h-10z M75 45h10v10h-10z M60 60h10v10h-10z M80 60h10v10h-10z M45 70h10v10h-10z M65 80h10v10h-10z M80 80h10v10h-10z" fill="#ee4d2d"/>
                                </svg>
                                <div class="shopee-qr-badges">
                                    <span class="shopee-store-badge">App Store</span>
                                    <span class="shopee-store-badge">Google Play</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <span class="shopee-topbar-sep">|</span>
                    <span class="shopee-topbar-text">Kết nối</span>
                    <a href="https://facebook.com" target="_blank" rel="noopener" class="shopee-social-icon" aria-label="Facebook">
                        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M14 13.5h2.5l1-4H14v-2c0-1.03 0-2 2-2h1.5V2.14c-.326-.043-1.52-.14-2.73-.14-2.8 0-4.77 1.71-4.77 4.9v2.6H7v4h3v10.5h4V13.5z"/></svg>
                    </a>
                    <a href="https://instagram.com" target="_blank" rel="noopener" class="shopee-social-icon" aria-label="Instagram">
                        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
                    </a>
                </div>

                <!-- Right Links -->
                <div class="shopee-topbar-right">
                    <!-- Notification -->
                    <div class="shopee-topbar-item has-dropdown">
                        <span class="shopee-topbar-link">
                            <svg class="shopee-tb-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2zm-2 1H8v-6c0-2.48 1.51-4.5 4-4.5s4 2.02 4 4.5v6z"/></svg>
                            <span>Thông Báo</span>
                            <span class="shopee-badge-num">9+</span>
                        </span>
                        <div class="shopee-notif-dropdown">
                            <div class="shopee-notif-header">Thông Báo Mới Nhận</div>
                            <div class="shopee-notif-list">
                                <div class="shopee-notif-item unread">
                                    <div class="shopee-notif-dot"></div>
                                    <div class="shopee-notif-content">
                                        <div class="shopee-notif-title">🔥 Siêu Sale PC RTX 50 Series - Voucher 1.5 Triệu!</div>
                                        <div class="shopee-notif-desc">Nhập mã <strong>SHOPEE2026</strong> giảm ngay 1.500.000₫ cho dàn PC Core Ultra và RTX 5070.</div>
                                        <div class="shopee-notif-time">5 phút trước</div>
                                    </div>
                                </div>
                                <div class="shopee-notif-item">
                                    <div class="shopee-notif-dot" style="opacity:0;"></div>
                                    <div class="shopee-notif-content">
                                        <div class="shopee-notif-title">⚡ Hạ tầng Cloud Well-Architected V2 Online</div>
                                        <div class="shopee-notif-desc">Hệ thống cân bằng tải Active-Active AZ-a &amp; AZ-b sẵn sàng phục vụ 500 CCU.</div>
                                        <div class="shopee-notif-time">Hôm nay 08:30</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Help -->
                    <a href="#help" class="shopee-topbar-link">
                        <svg class="shopee-tb-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 16h-2v-2h2v2zm1.07-7.75l-.9.92C12.45 11.9 12 12.5 12 14h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H7c0-2.76 2.24-5 5-5s5 2.24 5 5c0 .88-.36 1.68-.93 2.25z"/></svg>
                        <span>Hỗ Trợ</span>
                    </a>

                    <!-- Language Switcher -->
                    <div class="shopee-topbar-item has-dropdown">
                        <span class="shopee-topbar-link">
                            <svg class="shopee-tb-icon" viewBox="0 0 24 24"><path fill="currentColor" d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zm6.93 6h-2.95c-.32-1.25-.78-2.45-1.38-3.56 1.84.63 3.37 1.91 4.33 3.56zM12 4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 1.91-3.96zM4.26 14C4.1 13.36 4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 1.32-.14 2 0 .68.06 1.34.14 2H4.26zm.82 2h2.95c.32 1.25.78 2.45 1.38 3.56-1.84-.63-3.37-1.9-4.33-3.56zm2.95-8H5.08c.96-1.66 2.49-2.93 4.33-3.56C8.81 5.55 8.35 6.75 8.03 8zM12 19.96c-.83-1.2-1.48-2.53-1.91-3.96h3.82c-.43 1.43-1.08 2.76-1.91 3.96zM14.34 14H9.66c-.09-.66-.16-1.32-.16-2 0-.68.07-1.35.16-2h4.68c.09.65.16 1.32.16 2 0 .68-.07 1.34-.16 2zm.25 5.56c.6-1.11 1.06-2.31 1.38-3.56h2.95c-.96 1.65-2.49 2.93-4.33 3.56zM16.36 14c.08-.66.14-1.32.14-2 0-.68-.06-1.34-.14-2h3.38c.16.64.26 1.31.26 2s-.1 1.36-.26 2h-3.38z"/></svg>
                            <span>Tiếng Việt</span>
                            <svg class="shopee-caret" viewBox="0 0 10 6"><path fill="currentColor" d="M0 0l5 6 5-6z"/></svg>
                        </span>
                    </div>

                    <!-- User Profile -->
                    <div class="shopee-topbar-item has-dropdown">
                        <span class="shopee-topbar-link shopee-user-profile">
                            <span class="shopee-user-avatar">V</span>
                            <span class="shopee-username">vqp5u19dtu</span>
                            <svg class="shopee-caret" viewBox="0 0 10 6"><path fill="currentColor" d="M0 0l5 6 5-6z"/></svg>
                        </span>
                        <div class="shopee-user-dropdown">
                            <a href="#" class="shopee-user-menu-item">Tài khoản của tôi</a>
                            <a href="#" class="shopee-user-menu-item" onclick="showCartSummary(); return false;">Đơn Mua &amp; Giỏ Hàng</a>
                            <a href="#" class="shopee-user-menu-item" onclick="toggleCloudDrawer(); return false;">☁️ Bảng Điều Khiển Cloud V2</a>
                            <a href="#" class="shopee-user-menu-item">Đăng xuất</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Header Bar -->
        <div class="shopee-main-header">
            <div class="shopee-container shopee-header-inner">
                <!-- Shopee Bag Logo -->
                <a href="/" class="shopee-logo-link" aria-label="Shopee Vietnam Trang chủ">
                    <div class="shopee-logo-icon">
                        <svg viewBox="0 0 40 40" class="shopee-bag-svg">
                            <!-- Shopee Bag outline & handle -->
                            <path fill="#ffffff" d="M20 4a6.5 6.5 0 0 0-6.5 6.5V13H7a3 3 0 0 0-3 3l1.8 19A3 3 0 0 0 8.8 38h22.4a3 3 0 0 0 3-3L36 16a3 3 0 0 0-3-3h-6.5v-2.5A6.5 6.5 0 0 0 20 4zm-4 6.5a4 4 0 0 1 8 0V13h-8v-2.5z"/>
                            <!-- Letter S inside Bag -->
                            <path fill="#ee4d2d" d="M21.5 21.2c-1.8-.4-2.8-.8-2.8-1.7 0-.9.8-1.5 2.2-1.5 1.5 0 2.5.6 2.7 1.6h2.2c-.3-2.1-1.9-3.2-4.8-3.2-2.8 0-4.6 1.4-4.6 3.4 0 2.2 1.7 2.8 3.8 3.3 2 .5 2.6 1 2.6 1.8 0 1-1.1 1.6-2.5 1.6-1.8 0-2.9-.8-3.1-2H13c.2 2.3 2 3.6 5.3 3.6 3.1 0 4.9-1.5 4.9-3.6 0-2-1.4-2.7-3.7-3.2z"/>
                        </svg>
                    </div>
                    <div class="shopee-logo-text-wrap">
                        <span class="shopee-logo-title">Shopee</span>
                        <span class="shopee-logo-sub">Tech &amp; PC Gaming Mall</span>
                    </div>
                </a>

                <!-- Big Search Box & Suggestions -->
                <div class="shopee-search-area">
                    <div class="shopee-searchbox">
                        <!-- Dropdown category selector -->
                        <div class="shopee-search-scope" id="search-scope-btn" onclick="toggleSearchScopeDropdown()">
                            <span id="search-scope-label">Trong Thiết Bị Điện Tử</span>
                            <svg viewBox="0 0 10 6" class="shopee-scope-caret"><path fill="#555" d="M0 0l5 6 5-6z"/></svg>
                            <div class="shopee-scope-dropdown" id="search-scope-dropdown">
                                <div class="shopee-scope-item active" onclick="setSearchScope('Trong Thiết Bị Điện Tử', this)">Trong Thiết Bị Điện Tử</div>
                                <div class="shopee-scope-item" onclick="setSearchScope('Trong Shopee Mall', this)">Trong Shopee Mall</div>
                                <div class="shopee-scope-item" onclick="setSearchScope('Trong Toàn Sàn', this)">Trong Toàn Sàn</div>
                            </div>
                        </div>

                        <!-- Search input field -->
                        <input type="text"
                               id="search-input"
                               class="shopee-search-input"
                               placeholder="RTX 5060 gaming, PC đồ họa, linh kiện chính hãng..."
                               autocomplete="off"
                               onkeyup="if(event.key==='Enter') doShopeeSearch()">

                        <!-- Search orange button -->
                        <button type="button" class="shopee-search-btn" onclick="doShopeeSearch()" aria-label="Tìm kiếm">
                            <svg viewBox="0 0 24 24" class="shopee-search-glass"><circle cx="11" cy="11" r="7" stroke="#fff" stroke-width="2.5" fill="none"/><line x1="16.5" y1="16.5" x2="22" y2="22" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/></svg>
                        </button>
                    </div>

                    <!-- Search Suggestion Tags -->
                    <div class="shopee-search-tags" id="search-tags-list">
                        <span class="shopee-tag" onclick="quickSearchTag('Rtx 5060')">Rtx 5060</span>
                        <span class="shopee-tag" onclick="quickSearchTag('Techno Spark 40')">Techno Spark 40</span>
                        <span class="shopee-tag" onclick="quickSearchTag('Techno Spark 50 Pro')">Techno Spark 50 Pro</span>
                        <span class="shopee-tag" onclick="quickSearchTag('Váy Không Lót')">Váy Không Lót</span>
                        <span class="shopee-tag" onclick="quickSearchTag('Đèn Led Chân M5')">Đèn Led Chân M5</span>
                        <span class="shopee-tag" onclick="quickSearchTag('Techno Spark 40 Pro Plus')">Techno Spark 40 Pro Plus</span>
                        <span class="shopee-tag" onclick="quickSearchTag('Áo Manchester United')">Áo Manchester United</span>
                    </div>
                </div>

                <!-- Right Header Actions (Cart Badge & Cloud Drawer Toggle) -->
                <div class="shopee-header-actions">
                    <!-- Cart Icon with Badge (#cart-badge) -->
                    <div class="shopee-cart-wrap" onclick="showCartSummary()" title="Xem giỏ hàng &amp; thanh toán ACID">
                        <div class="shopee-cart-icon-btn">
                            <svg viewBox="0 0 24 24" class="shopee-cart-svg">
                                <path fill="#ffffff" d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/>
                            </svg>
                            <span class="shopee-cart-badge" id="cart-badge">0</span>
                        </div>
                    </div>

                    <!-- Cloud Well-Architected V2 Live Drawer Toggle Pill -->
                    <button type="button" class="shopee-cloud-pill" onclick="toggleCloudDrawer()" title="Mở bảng điều khiển Cloud Well-Architected V2">
                        <span class="shopee-cloud-dot"></span>
                        <span>☁️ Cloud V2</span>
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- ===================================================================
         2. CLOUD WELL-ARCHITECTED V2 LIVE DRAWER (#cloud-drawer)
         Preserved for evaluation: Multi-AZ status, Load Balancer & Chaos Injection
         =================================================================== -->
    <div id="cloud-drawer" class="shopee-cloud-drawer" style="display:none;">
        <div class="shopee-container">
            <div class="cloud-panel-header">
                <div class="cloud-panel-title">
                    <span class="cloud-pill-badge">HẠ TẦNG CLOUD V2</span>
                    <strong>AWS / Hybrid Multi-AZ High Availability Cluster</strong>
                </div>
                <button type="button" class="cloud-close-btn" onclick="toggleCloudDrawer()">✕</button>
            </div>
            <div class="cloud-grid">
                <div class="cloud-badges">
                    <div class="c-badge">Kiến trúc: <strong>{safe_arch}</strong></div>
                    <div class="c-badge">Node thụ lý: <strong id="current-node">{safe_node}</strong></div>
                    <div class="c-badge">Trạng thái hạ tầng: <strong id="az-status" style="color:#26aa99;">AZ-a &amp; AZ-b ONLINE (Active-Active)</strong></div>
                    <div class="c-badge">Giao dịch: <strong>ACID (SELECT ... FOR UPDATE)</strong></div>
                </div>
                <div class="cloud-actions">
                    <button type="button" class="c-btn c-btn-blue" onclick="testLoadBalancing()">⚡ Bắn 10 Request Load Balancer</button>
                    <button type="button" id="btn-chaos" class="c-btn c-btn-red" onclick="toggleChaos()">🔥 Tiêm Lỗi: Hạ Sập Node 1</button>
                    <a href="/metrics" target="_blank" class="c-btn c-btn-green">📊 Prometheus Metrics</a>
                </div>
            </div>
            <div id="lb-log" class="cloud-lb-log" style="display:none;"></div>
        </div>
    </div>

    <main class="shopee-main-content">
        <!-- ===================================================================
             3. HERO BANNER CAROUSEL & SUB-BANNERS AREA
             =================================================================== -->
        <section class="shopee-hero-section">
            <div class="shopee-container shopee-hero-grid">
                <!-- Main Carousel (2/3 width) -->
                <div class="shopee-carousel-wrap" id="shopee-carousel">
                    <div class="shopee-carousel-track" id="carousel-track">
                        <!-- Slide 1: EDIFIER (Per Screenshot requirements) -->
                        <div class="shopee-slide active">
                            <div class="shopee-slide-bg slide-edifier">
                                <div class="shopee-slide-content">
                                    <div class="shopee-slide-tag-mall">SHOPEE MALL</div>
                                    <div class="shopee-slide-brand">EDIFIER OFFICIAL STORE</div>
                                    <h2 class="shopee-slide-headline">BẬT NHẠC HAY<br>BẬT CHẤT NGAY</h2>
                                    <div class="shopee-slide-perks">
                                        <span class="shopee-perk-badge">🔥 Voucher đến 20%</span>
                                        <span class="shopee-perk-badge">🛡️ Bảo hành 15 tháng</span>
                                        <span class="shopee-perk-badge">🚚 Miễn phí vận chuyển</span>
                                    </div>
                                    <div class="shopee-slide-action">
                                        <button type="button" class="shopee-btn-slide" onclick="filterBySearch('Edifier', true)">Mua Ngay &gt;</button>
                                    </div>
                                </div>
                                <div class="shopee-slide-image-box">
                                    <img src="/static/ttg_assets/hero_setup.jpg" alt="Edifier &amp; PC Gaming Studio" class="shopee-slide-img">
                                </div>
                            </div>
                        </div>

                        <!-- Slide 2: RTX 50 Series -->
                        <div class="shopee-slide">
                            <div class="shopee-slide-bg slide-rtx">
                                <div class="shopee-slide-content">
                                    <div class="shopee-slide-tag-mall">SIÊU SALE CÔNG NGHỆ</div>
                                    <div class="shopee-slide-brand">NVIDIA GEFORCE RTX 50 SERIES</div>
                                    <h2 class="shopee-slide-headline">ĐỈNH CAO ĐỒ HỌA<br>GIẢM ĐẾN 1.500.000₫</h2>
                                    <div class="shopee-slide-perks">
                                        <span class="shopee-perk-badge">🎟️ Mã SHOPEE2026</span>
                                        <span class="shopee-perk-badge">⚡ Trả góp 0%</span>
                                        <span class="shopee-perk-badge">🔒 Khóa kho ACID</span>
                                    </div>
                                    <div class="shopee-slide-action">
                                        <button type="button" class="shopee-btn-slide" onclick="filterBySearch('RTX 50', true)">Săn Deal Ngay &gt;</button>
                                    </div>
                                </div>
                                <div class="shopee-slide-image-box">
                                    <img src="/static/ttg_assets/pc_6.png" alt="PC Gaming Core Ultra RTX 5070" class="shopee-slide-img-contain">
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Carousel Controls -->
                    <button type="button" class="shopee-car-btn prev" onclick="moveCarousel(-1)" aria-label="Slide trước">&#10094;</button>
                    <button type="button" class="shopee-car-btn next" onclick="moveCarousel(1)" aria-label="Slide kế tiếp">&#10095;</button>

                    <!-- Carousel Dots -->
                    <div class="shopee-car-dots" id="carousel-dots">
                        <span class="shopee-car-dot active" onclick="jumpCarousel(0)"></span>
                        <span class="shopee-car-dot" onclick="jumpCarousel(1)"></span>
                    </div>
                </div>

                <!-- Right Sub-banners (1/3 width stacked) -->
                <div class="shopee-subbanners">
                    <div class="shopee-subbanner-item subbanner-top" onclick="quickApplyPromo('SHOPEE2026')">
                        <div class="subbanner-badge">VOUCHER XTRA</div>
                        <div class="subbanner-title">MÃ GIẢM 1.500.000₫</div>
                        <div class="subbanner-desc">Nhập mã <strong>SHOPEE2026</strong> cho mọi đơn PC Gaming</div>
                        <div class="subbanner-code">SHOPEE2026</div>
                    </div>
                    <div class="shopee-subbanner-item subbanner-bottom" onclick="filterByCategory('PC GAMING GIÁ RẺ')">
                        <div class="subbanner-badge" style="background:#26aa99;">FREESHIP XTRA</div>
                        <div class="subbanner-title">ĐỒNG GIÁ FLASH SALE</div>
                        <div class="subbanner-desc">Chỉ từ 20.480.000₫ • Giao nhanh 2H nội thành</div>
                        <div class="subbanner-cta">Xem ngay &gt;</div>
                    </div>
                </div>
            </div>

            <!-- Shopee Quick Services Ribbon (8 Circular Shortcuts) -->
            <div class="shopee-container">
                <div class="shopee-services-bar">
                    <div class="shopee-service-item" onclick="scrollToSection('flash-sale-section')">
                        <div class="shopee-service-icon icon-flash">⚡</div>
                        <span class="shopee-service-name">Khung Giờ Săn Sale</span>
                    </div>
                    <div class="shopee-service-item" onclick="filterByCategory('')">
                        <div class="shopee-service-icon icon-freeship">🚚</div>
                        <span class="shopee-service-name">Miễn Phí Vận Chuyển</span>
                    </div>
                    <div class="shopee-service-item" onclick="quickApplyPromo('SHOPEE2026')">
                        <div class="shopee-service-icon icon-voucher">🎟️</div>
                        <span class="shopee-service-name">Mã Giảm Giá</span>
                    </div>
                    <div class="shopee-service-item" onclick="scrollToSection('mall-section')">
                        <div class="shopee-service-icon icon-mall">👑</div>
                        <span class="shopee-service-name">Shopee Mall</span>
                    </div>
                    <div class="shopee-service-item" onclick="filterByCategory('PC Core Ultra')">
                        <div class="shopee-service-icon icon-tech">💻</div>
                        <span class="shopee-service-name">Tech Ultra V2</span>
                    </div>
                    <div class="shopee-service-item" onclick="quickApplyPromo('UTH2026')">
                        <div class="shopee-service-icon icon-coin">💰</div>
                        <span class="shopee-service-name">Săn Xu 100K</span>
                    </div>
                    <div class="shopee-service-item" onclick="filterByCategory('PC GAMING PREMIUM')">
                        <div class="shopee-service-icon icon-card">💳</div>
                        <span class="shopee-service-name">Trả Góp 0%</span>
                    </div>
                    <div class="shopee-service-item" onclick="toggleCloudDrawer()">
                        <div class="shopee-service-icon icon-cloud">☁️</div>
                        <span class="shopee-service-name">Kiến Trúc Cloud</span>
                    </div>
                </div>
            </div>
        </section>

        <!-- ===================================================================
             4. SHOPEE MALL BRAND RIBBON (Samsung, Apple, Oppo, ShopDunk, Coocaa, SoundMax)
             =================================================================== -->
        <section class="shopee-mall-section" id="mall-section">
            <div class="shopee-container">
                <div class="shopee-mall-card">
                    <!-- Mall Header -->
                    <div class="shopee-mall-header">
                        <div class="shopee-mall-header-left">
                            <span class="shopee-mall-title-badge">SHOPEE MALL</span>
                            <span class="shopee-mall-feature">
                                <svg class="mall-check-svg" viewBox="0 0 24 24"><path fill="#d0011b" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                                Trả Hàng Miễn Phí 15 Ngày
                            </span>
                            <span class="shopee-mall-feature">
                                <svg class="mall-check-svg" viewBox="0 0 24 24"><path fill="#d0011b" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                                Hàng Chính Hãng 100%
                            </span>
                            <span class="shopee-mall-feature">
                                <svg class="mall-check-svg" viewBox="0 0 24 24"><path fill="#d0011b" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                                Miễn Phí Vận Chuyển
                            </span>
                        </div>
                        <a href="#mall" class="shopee-mall-see-all" onclick="filterByCategory(''); return false;">
                            Xem Tất Cả <span class="see-all-arrow">&gt;</span>
                        </a>
                    </div>

                    <!-- Mall Brand Logos Row -->
                    <div class="shopee-mall-brands-row" id="shopee-mall-brands">
                        <!-- Brand 1: Samsung -->
                        <div class="shopee-brand-col" onclick="filterBySearch('Samsung')">
                            <div class="shopee-brand-logo-box">
                                <span class="shopee-brand-text samsung-text">SAMSUNG</span>
                            </div>
                            <div class="shopee-brand-promo">Ưu đãi đến 40%</div>
                        </div>

                        <!-- Brand 2: Apple Authorised Reseller -->
                        <div class="shopee-brand-col" onclick="filterBySearch('Apple')">
                            <div class="shopee-brand-logo-box">
                                <span class="shopee-brand-text apple-text"> Apple Reseller</span>
                            </div>
                            <div class="shopee-brand-promo">Chính Hãng VN</div>
                        </div>

                        <!-- Brand 3: OPPO -->
                        <div class="shopee-brand-col" onclick="filterBySearch('OPPO')">
                            <div class="shopee-brand-logo-box">
                                <span class="shopee-brand-text oppo-text">oppo</span>
                            </div>
                            <div class="shopee-brand-promo">Flagship Store</div>
                        </div>

                        <!-- Brand 4: ShopDunk -->
                        <div class="shopee-brand-col" onclick="filterBySearch('ShopDunk')">
                            <div class="shopee-brand-logo-box">
                                <span class="shopee-brand-text shopdunk-text">ShopDunk</span>
                            </div>
                            <div class="shopee-brand-promo">Đại lý uỷ quyền</div>
                        </div>

                        <!-- Brand 5: Coocaa -->
                        <div class="shopee-brand-col" onclick="filterBySearch('Coocaa')">
                            <div class="shopee-brand-logo-box">
                                <span class="shopee-brand-text coocaa-text">coocaa</span>
                            </div>
                            <div class="shopee-brand-promo">Smart TV 4K</div>
                        </div>

                        <!-- Brand 6: SoundMax -->
                        <div class="shopee-brand-col" onclick="filterBySearch('SoundMax')">
                            <div class="shopee-brand-logo-box">
                                <span class="shopee-brand-text soundmax-text">SOUNDMAX</span>
                            </div>
                            <div class="shopee-brand-promo">Âm thanh Hi-Fi</div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- ===================================================================
             5. FLASH SALE SECTION WITH COUNTDOWN TIMER
             =================================================================== -->
        <section class="shopee-flash-sale-section" id="flash-sale-section">
            <div class="shopee-container">
                <div class="shopee-fs-card">
                    <!-- Flash Sale Bar Header -->
                    <div class="shopee-fs-header">
                        <div class="shopee-fs-title-box">
                            <span class="shopee-fs-icon">⚡</span>
                            <span class="shopee-fs-title">F L A S H &nbsp; S A L E</span>
                            <!-- Countdown Timer -->
                            <div class="shopee-fs-timer">
                                <span class="fs-timer-digit" id="fs-hours">02</span>
                                <span class="fs-timer-colon">:</span>
                                <span class="fs-timer-digit" id="fs-mins">45</span>
                                <span class="fs-timer-colon">:</span>
                                <span class="fs-timer-digit" id="fs-secs">18</span>
                            </div>
                        </div>
                        <a href="#flash-sale" class="shopee-fs-more" onclick="filterByCategory('PC GAMING GIÁ RẺ'); return false;">
                            Xem tất cả &gt;
                        </a>
                    </div>

                    <!-- Flash Sale Items Row -->
                    <div class="shopee-fs-items-row" id="flash-sale-items">
                        <!-- Loaded dynamically or rendered with top deals -->
                    </div>
                </div>
            </div>
        </section>

        <!-- ===================================================================
             6. GỢI Ý HÔM NAY / SẢN PHẨM & DYNAMIC SHOPEE PRODUCT GRID
             =================================================================== -->
        <section class="shopee-recommend-section" id="recommend-section">
            <div class="shopee-container">
                <!-- Sticky Tabs Bar -->
                <div class="shopee-tabs-bar">
                    <button type="button" class="shopee-tab-btn active" data-tab="recommend" onclick="selectShopeeTab('recommend', this)">
                        GỢI Ý HÔM NAY
                    </button>
                    <button type="button" class="shopee-tab-btn" data-tab="pc-gaming" onclick="selectShopeeTab('pc-gaming', this)">
                        PC GAMING &amp; THIẾT BỊ ĐIỆN TỬ
                    </button>
                    <button type="button" class="shopee-tab-btn" data-tab="flash-sale" onclick="selectShopeeTab('flash-sale', this)">
                        FLASH SALE
                    </button>
                    <button type="button" class="shopee-tab-btn" data-tab="mall" onclick="selectShopeeTab('mall', this)">
                        SHOPEE MALL CHÍNH HÃNG
                    </button>
                </div>

                <!-- Sub-filter Category Pills & Sort Toolbar -->
                <div class="shopee-filter-toolbar">
                    <div class="shopee-cat-pills" role="tablist">
                        <button type="button" class="shopee-cat-pill active" data-cat="" onclick="filterByCategory('', this)">Tất cả</button>
                        <button type="button" class="shopee-cat-pill" data-cat="PC Core Ultra" onclick="filterByCategory('PC Core Ultra', this)">PC Core Ultra</button>
                        <button type="button" class="shopee-cat-pill" data-cat="PC GAMING PREMIUM" onclick="filterByCategory('PC GAMING PREMIUM', this)">PC Gaming Pro</button>
                        <button type="button" class="shopee-cat-pill" data-cat="PC GAMING CAO CẤP" onclick="filterByCategory('PC GAMING CAO CẤP', this)">PC Gaming Cao Cấp</button>
                        <button type="button" class="shopee-cat-pill" data-cat="PC STREAM GAME" onclick="filterByCategory('PC STREAM GAME', this)">PC Stream Game</button>
                        <button type="button" class="shopee-cat-pill" data-cat="PC GAMING GIÁ RẺ" onclick="filterByCategory('PC GAMING GIÁ RẺ', this)">PC Gaming Giá Rẻ</button>
                        <button type="button" class="shopee-cat-pill" data-cat="PC ĐẸP" onclick="filterByCategory('PC ĐẸP', this)">PC Đẹp</button>
                    </div>

                    <div class="shopee-sort-bar">
                        <span class="shopee-sort-label">Sắp xếp theo:</span>
                        <button type="button" class="shopee-sort-btn active" data-sort="pop" onclick="sortShopeeProducts('pop', this)">Phổ biến</button>
                        <button type="button" class="shopee-sort-btn" data-sort="new" onclick="sortShopeeProducts('new', this)">Mới nhất</button>
                        <button type="button" class="shopee-sort-btn" data-sort="sold" onclick="sortShopeeProducts('sold', this)">Bán chạy</button>
                        <select class="shopee-sort-select" onchange="sortShopeeProducts(this.value, this)">
                            <option value="default">Giá</option>
                            <option value="asc">Giá: Thấp đến Cao</option>
                            <option value="desc">Giá: Cao đến Thấp</option>
                        </select>
                        <div class="shopee-count-badge">Tổng <strong id="total-found">457</strong> sản phẩm</div>
                    </div>
                </div>

                <!-- Product Grid (#product-grid) -->
                <div id="product-grid" class="shopee-product-grid">
                    <div class="shopee-grid-loading">Đang tải danh sách sản phẩm Shopee Mall...</div>
                </div>

                <!-- Load More Button -->
                <div class="shopee-load-more-box">
                    <button type="button" class="shopee-btn-load-more" onclick="loadMoreProducts()">
                        Xem thêm sản phẩm gợi ý
                    </button>
                </div>
            </div>
        </section>
    </main>

    <!-- ===================================================================
         7. SHOPEE FOOTER & LOGISTICS / PAYMENT PARTNERS
         =================================================================== -->
    <footer class="shopee-footer">
        <div class="shopee-container shopee-footer-inner">
            <div class="shopee-footer-cols">
                <div class="shopee-footer-col">
                    <h4 class="shopee-footer-heading">CHĂM SÓC KHÁCH HÀNG</h4>
                    <ul class="shopee-footer-links">
                        <li><a href="#">Trung Tâm Trợ Giúp</a></li>
                        <li><a href="#">Shopee Blog</a></li>
                        <li><a href="#">Shopee Mall</a></li>
                        <li><a href="#">Hướng Dẫn Mua Hàng</a></li>
                        <li><a href="#">Thanh Toán An Toàn ACID</a></li>
                        <li><a href="#">Trả Hàng &amp; Hoàn Tiền</a></li>
                    </ul>
                </div>

                <div class="shopee-footer-col">
                    <h4 class="shopee-footer-heading">VỀ SHOPEE TECH</h4>
                    <ul class="shopee-footer-links">
                        <li><a href="#">Giới Thiệu Shopee Việt Nam</a></li>
                        <li><a href="#">Tuyển Dụng</a></li>
                        <li><a href="#">Điều Khoản Shopee</a></li>
                        <li><a href="#">Chính Sách Bảo Mật</a></li>
                        <li><a href="#">Chính Hãng 100%</a></li>
                        <li><a href="#">Flash Sale Khung Giờ</a></li>
                    </ul>
                </div>

                <div class="shopee-footer-col">
                    <h4 class="shopee-footer-heading">THANH TOÁN</h4>
                    <div class="shopee-partner-badges">
                        <span class="pay-badge shopeepay">ShopeePay</span>
                        <span class="pay-badge applepay">Apple Pay</span>
                        <span class="pay-badge vietqr">VietQR 24/7</span>
                        <span class="pay-badge cod">COD</span>
                        <span class="pay-badge visa">VISA</span>
                        <span class="pay-badge master">Mastercard</span>
                    </div>
                    <h4 class="shopee-footer-heading" style="margin-top:16px;">ĐƠN VỊ VẬN CHUYỂN</h4>
                    <div class="shopee-partner-badges">
                        <span class="ship-badge spx">SPX Express</span>
                        <span class="ship-badge ghn">Giao Hàng Nhanh</span>
                        <span class="ship-badge viettel">Viettel Post</span>
                        <span class="ship-badge jnt">J&amp;T Express</span>
                    </div>
                </div>

                <div class="shopee-footer-col">
                    <h4 class="shopee-footer-heading">THEO DÕI CHÚNG TÔI</h4>
                    <ul class="shopee-footer-links">
                        <li><a href="#">Facebook: Shopee Vietnam</a></li>
                        <li><a href="#">Instagram: @Shopee_VN</a></li>
                        <li><a href="#">LinkedIn: Shopee Tech</a></li>
                    </ul>
                    <h4 class="shopee-footer-heading" style="margin-top:14px;">TẢI ỨNG DỤNG SHOPEE</h4>
                    <div class="shopee-download-box">
                        <div class="shopee-qr-mini">QR Code</div>
                        <div class="shopee-app-links">
                            <span>App Store</span>
                            <span>Google Play</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="shopee-footer-bottom">
                <div class="shopee-footer-copy">
                    <span>© 2026 Shopee. Tất cả các quyền được bảo lưu.</span>
                    <span>Quốc gia &amp; Khu vực: Singapore | Indonesia | Thái Lan | Malaysia | <strong>Việt Nam</strong> | Philippines | Brazil</span>
                </div>
                <div class="shopee-footer-arch-meta">
                    Kiến trúc: <strong>{safe_arch}</strong> • Node thụ lý: <strong id="footer-node">{safe_node}</strong> • ACID Row-Lock Engine • Multi-AZ Active-Active
                </div>
            </div>
        </div>
    </footer>

    <!-- ===================================================================
         8. SHOPEE FLOATING CHAT WIDGET & BACK TO TOP
         =================================================================== -->
    <div class="shopee-floating-actions">
        <!-- Back to Top Button -->
        <button type="button" class="shopee-back-top-btn" id="shopee-back-top" onclick="scrollShopeeToTop()" title="Lên đầu trang">
            ▲
        </button>

        <!-- Floating Chat Button (Bottom-Right corner) -->
        <div class="shopee-chat-widget" id="shopee-chat-widget">
            <button type="button" class="shopee-chat-trigger" onclick="toggleShopeeChat()" aria-label="Mở cửa sổ chat">
                <svg viewBox="0 0 24 24" class="shopee-chat-bubble-svg"><path fill="#ffffff" d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 9h12v2H6V9zm8 5H6v-2h8v2zm4-6H6V6h12v2z"/></svg>
                <span class="shopee-chat-text">Chat</span>
                <span class="shopee-chat-unread">1</span>
            </button>

            <!-- Chat Window Popover -->
            <div class="shopee-chat-box" id="shopee-chat-box" style="display:none;">
                <div class="shopee-chat-header">
                    <div class="shopee-chat-header-info">
                        <span class="shopee-chat-avatar">S</span>
                        <div>
                            <div class="shopee-chat-name">Shopee CSKH 24/7</div>
                            <div class="shopee-chat-status">● Đang hoạt động</div>
                        </div>
                    </div>
                    <button type="button" class="shopee-chat-close-btn" onclick="toggleShopeeChat()">✕</button>
                </div>
                <div class="shopee-chat-body" id="shopee-chat-messages">
                    <div class="shopee-msg bot">
                        Xin chào <strong>vqp5u19dtu</strong>! Shopee Mall hỗ trợ bạn tìm kiếm cấu hình PC Gaming hay nhận mã giảm giá <strong>SHOPEE2026</strong> (-1.5 Triệu)?
                    </div>
                    <div class="shopee-quick-prompts">
                        <button type="button" class="shopee-prompt-chip" onclick="sendQuickChatMessage('Tư vấn PC RTX 5060')">PC RTX 5060</button>
                        <button type="button" class="shopee-prompt-chip" onclick="sendQuickChatMessage('Mã giảm giá SHOPEE2026')">Voucher 1.5Tr</button>
                        <button type="button" class="shopee-prompt-chip" onclick="sendQuickChatMessage('Freeship Xtra')">Freeship</button>
                    </div>
                </div>
                <div class="shopee-chat-footer">
                    <input type="text" id="shopee-chat-input" placeholder="Nhập tin nhắn..." onkeyup="if(event.key==='Enter') sendChatMessage()">
                    <button type="button" class="shopee-chat-send-btn" onclick="sendChatMessage()">Gửi</button>
                </div>
            </div>
        </div>
    </div>

    <!-- ===================================================================
         9. SHOPEE CART & ACID CHECKOUT MODAL / DRAWER (#shopee-checkout-modal)
         =================================================================== -->
    <div id="shopee-checkout-modal" class="shopee-modal-wrap" style="display:none;">
        <div class="shopee-modal-dialog">
            <!-- Modal Header -->
            <div class="shopee-modal-header">
                <div class="shopee-modal-title-box">
                    <svg viewBox="0 0 24 24" class="shopee-shield-svg"><path fill="#ee4d2d" d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg>
                    <div>
                        <div class="shopee-modal-title">Shopee Đảm Bảo | Giỏ Hàng &amp; Thanh Toán</div>
                        <div class="shopee-modal-subtitle">Giao dịch khóa dòng ACID • Hoàn tiền 100% nếu sản phẩm lỗi</div>
                    </div>
                </div>
                <button type="button" class="shopee-modal-close" onclick="closeShopeeCheckout()">✕</button>
            </div>

            <!-- Modal Body -->
            <div class="shopee-modal-body">
                <!-- Cart Items List -->
                <div class="shopee-section-card">
                    <div class="shopee-card-title-row">
                        <span class="shopee-card-title">Sản Phẩm Trong Giỏ (<span id="shopee-cart-count">0</span>)</span>
                        <button type="button" class="shopee-btn-link" onclick="addSampleShopeeProduct()">+ Thêm nhanh PC Core Ultra 7</button>
                    </div>
                    <div class="shopee-cart-list" id="shopee-cart-items-container">
                        <!-- Rendered by JS -->
                    </div>
                </div>

                <!-- Shopee Voucher Selection -->
                <div class="shopee-section-card">
                    <div class="shopee-card-title-row">
                        <span class="shopee-card-title">Shopee Voucher</span>
                        <span class="shopee-voucher-hint">Chọn 1 mã giảm giá</span>
                    </div>
                    <div class="shopee-voucher-chips">
                        <button type="button" class="shopee-voucher-chip active" data-promo="SHOPEE2026" onclick="selectVoucherChip('SHOPEE2026')">
                            <strong>SHOPEE2026</strong> (-1.500.000₫)
                        </button>
                        <button type="button" class="shopee-voucher-chip" data-promo="SHOPEE500K" onclick="selectVoucherChip('SHOPEE500K')">
                            <strong>SHOPEE500K</strong> (-500.000₫)
                        </button>
                        <button type="button" class="shopee-voucher-chip" data-promo="UTH2026" onclick="selectVoucherChip('UTH2026')">
                            <strong>UTH2026</strong> (-1.000.000₫)
                        </button>
                        <button type="button" class="shopee-voucher-chip" data-promo="TTG500K" onclick="selectVoucherChip('TTG500K')">
                            <strong>TTG500K</strong> (-500.000₫)
                        </button>
                    </div>
                    <div class="shopee-voucher-input-row">
                        <input type="text" id="shopee-voucher-input" class="shopee-voucher-input" placeholder="Nhập mã voucher Shopee..." value="SHOPEE2026">
                        <button type="button" class="shopee-btn-apply-voucher" onclick="applyVoucherInput()">Áp Dụng</button>
                    </div>
                </div>

                <!-- Phương Thức Thanh Toán -->
                <div class="shopee-section-card">
                    <div class="shopee-card-title-row">
                        <span class="shopee-card-title">Phương Thức Thanh Toán</span>
                    </div>
                    <div class="shopee-payment-options">
                        <label class="shopee-pay-option active">
                            <input type="radio" name="payment_method" value="Ví ShopeePay" checked onchange="handlePaymentChange(this)">
                            <span class="pay-radio-custom"></span>
                            <span class="pay-option-content">
                                <strong>Ví ShopeePay</strong> (Khuyên dùng - Giảm thêm phí dịch vụ &amp; tích Xu)
                            </span>
                        </label>
                        <label class="shopee-pay-option">
                            <input type="radio" name="payment_method" value="Apple Pay" onchange="handlePaymentChange(this)">
                            <span class="pay-radio-custom"></span>
                            <span class="pay-option-content">
                                <strong>Apple Pay</strong> (Xác thực Face ID / Touch ID nhanh chóng)
                            </span>
                        </label>
                        <label class="shopee-pay-option">
                            <input type="radio" name="payment_method" value="Chuyển khoản VietQR 24/7" onchange="handlePaymentChange(this)">
                            <span class="pay-radio-custom"></span>
                            <span class="pay-option-content">
                                <strong>Chuyển khoản VietQR 24/7</strong> (Quét mã Napas 247 tự động khớp lệnh)
                            </span>
                        </label>
                        <label class="shopee-pay-option">
                            <input type="radio" name="payment_method" value="COD - Thanh toán khi nhận hàng" onchange="handlePaymentChange(this)">
                            <span class="pay-radio-custom"></span>
                            <span class="pay-option-content">
                                <strong>Thanh toán khi nhận hàng (COD)</strong> (Kiểm tra hàng trước khi thanh toán)
                            </span>
                        </label>
                    </div>

                    <!-- VietQR Box -->
                    <div id="shopee-vietqr-box" class="shopee-vietqr-box" style="display:none;">
                        <div class="vietqr-info">
                            <div class="vietqr-bank">Ngân Hàng MB Bank • STK: <strong>0886976868</strong></div>
                            <div class="vietqr-name">Chủ tài khoản: <strong>SHOPEE TECH VIETNAM</strong></div>
                            <div class="vietqr-note">Nội dung chuyển khoản: Tự động ghi mã đơn sau khi đặt hàng</div>
                        </div>
                        <span class="vietqr-badge">NAPAS 247 VERIFIED</span>
                    </div>
                </div>

                <!-- Shipping Address & Receiver Info -->
                <div class="shopee-section-card">
                    <div class="shopee-card-title-row">
                        <span class="shopee-card-title">Địa Chỉ Nhận Hàng</span>
                    </div>
                    <div class="shopee-form-grid">
                        <div class="shopee-field">
                            <label for="shopee-cust-name">Họ và tên người nhận</label>
                            <input type="text" id="shopee-cust-name" value="Nguyễn Văn An" required>
                        </div>
                        <div class="shopee-field">
                            <label for="shopee-cust-phone">Số điện thoại</label>
                            <input type="tel" id="shopee-cust-phone" value="0909123456" required>
                        </div>
                        <div class="shopee-field full-width">
                            <label for="shopee-cust-address">Địa chỉ chi tiết</label>
                            <input type="text" id="shopee-cust-address" value="Số 2 Võ Oanh, Phường 25, Quận Bình Thạnh, TP. Hồ Chí Minh" required>
                        </div>
                    </div>
                </div>

                <!-- Order Receipt Box (#shopee-order-receipt) -->
                <div id="shopee-order-receipt" class="shopee-order-receipt" style="display:none;"></div>
            </div>

            <!-- Modal Footer (Price calculation & Place Order) -->
            <div class="shopee-modal-footer">
                <div class="shopee-price-summary">
                    <div class="shopee-price-row">
                        <span>Tổng tiền hàng:</span>
                        <strong id="shopee-subtotal-val">0₫</strong>
                    </div>
                    <div class="shopee-price-row">
                        <span>Phí vận chuyển:</span>
                        <span style="color:#26aa99;font-weight:600;">₫0 (Freeship Xtra)</span>
                    </div>
                    <div class="shopee-price-row discount">
                        <span>Giảm giá voucher (<span id="shopee-applied-promo">SHOPEE2026</span>):</span>
                        <span id="shopee-discount-val">-0₫</span>
                    </div>
                    <div class="shopee-price-row final">
                        <span>Tổng thanh toán:</span>
                        <strong class="shopee-total-val" id="shopee-total-val">0₫</strong>
                    </div>
                </div>

                <div class="shopee-submit-row">
                    <button type="button" id="shopee-checkout-submit-btn" class="shopee-btn-submit-order" onclick="submitShopeeAcidCheckout()">
                        Đặt Hàng (Thanh Toán ACID)
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Notification Container -->
    <div id="toast-container" class="shopee-toast-container"></div>

    <!-- Shopee Store Javascript Engine -->
    <script src="/static/shopee_store.js"></script>
</body>
</html>"""
