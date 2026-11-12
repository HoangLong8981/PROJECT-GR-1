# -*- coding: utf-8 -*-
"""
Apple Vietnam iPad / Store Showcase HTML Template (apple.com/vn/ipad/ style)
Owned by: Worker 1 (@ui-frontend)
Follows apple-design, taste-skill, and emil-design-eng — Zero Flying Bees
"""

import html


def render_apple_store_html(
    node: str = "app-replica-1 (AZ-a)",
    arch_version: str = "V2-Well-Architected",
) -> str:
    """Render the complete Apple Vietnam iPad / Studio PC Pro storefront HTML."""
    safe_node = html.escape(str(node or "app-replica-1 (AZ-a)"), quote=True)
    safe_arch = html.escape(str(arch_version or "V2-Well-Architected"), quote=True)

    return f"""<!DOCTYPE html>
<html lang="vi" data-type="product">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="page-type" content="product">
    <meta name="site-kind" content="tech">
    <title>iPad &amp; Studio PC Pro — Apple / TTG Studio (VN)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/apple_store.css">
</head>
<body>
    <!-- 1. APPLE GLOBAL NAV BAR (height: 44px, Sticky Frosted Glass) -->
    <header class="apple-globalnav" role="banner">
        <div class="apple-globalnav-content">
            <a href="/" class="apple-nav-logo" aria-label="Apple / TTG Studio Trang chủ">
                <svg viewBox="0 0 17 20" aria-hidden="true">
                    <path d="M13.545 10.239c-.022-2.234 1.823-3.306 1.905-3.357-1.037-1.517-2.653-1.725-3.228-1.748-1.374-.139-2.682.809-3.379.809-.697 0-1.774-.789-2.915-.768-1.5.022-2.883.872-3.655 2.214-1.559 2.704-.398 6.709 1.119 8.902.742 1.073 1.626 2.278 2.788 2.235 1.119-.045 1.542-.724 2.895-.724 1.353 0 1.733.724 2.916.701 1.205-.022 1.968-1.095 2.709-2.168.854-1.248 1.206-2.456 1.227-2.519-.027-.012-2.357-.905-2.382-3.577zM11.318 3.654c.617-.748 1.033-1.787.919-2.824-.889.036-1.965.592-2.603 1.34-.571.661-1.071 1.719-.937 2.735.992.077 2.004-.503 2.621-1.251z"></path>
                </svg>
                <span>TTG Studio</span>
            </a>

            <ul class="apple-nav-links" role="navigation" aria-label="Điều hướng chính">
                <li><span class="apple-nav-link" onclick="filterByCategory('', this)">Cửa Hàng</span></li>
                <li><span class="apple-nav-link" onclick="scrollToSection('hero-section')">iPad / PC Pro</span></li>
                <li><span class="apple-nav-link" onclick="filterByCategory('PC GAMING PREMIUM', this)">Gaming</span></li>
                <li><span class="apple-nav-link" onclick="filterByCategory('PC GAMING CAO CẤP', this)">Workstation</span></li>
                <li><span class="apple-nav-link" onclick="filterByCategory('PC Core Ultra', this)">Core Ultra</span></li>
                <li><span class="apple-nav-link" onclick="filterBySearch('RTX 50', true)">RTX 50 Series</span></li>
                <li><span class="apple-nav-link" onclick="scrollToSection('compare-section')">So Sánh</span></li>
                <li><span class="apple-nav-link" onclick="scrollToSection('why-apple-section')">Hỗ Trợ</span></li>
            </ul>

            <div class="apple-nav-actions">
                <button type="button" class="apple-nav-icon-btn" onclick="focusAppleSearch()" aria-label="Tìm kiếm cấu hình" title="Tìm kiếm">
                    <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7.5"></circle><line x1="20" y1="20" x2="16.2" y2="16.2"></line></svg>
                </button>
                <button type="button" class="apple-nav-icon-btn" onclick="showCartSummary()" aria-label="Giỏ hàng" title="Giỏ hàng &amp; Thanh toán ACID">
                    <svg viewBox="0 0 24 24"><path d="M6 7h12l1 13H5L6 7z"></path><path d="M9 7V5a3 3 0 0 1 6 0v2"></path></svg>
                    <span class="apple-bag-badge" id="cart-badge">0</span>
                </button>
                <button type="button" class="apple-cloud-pill" onclick="toggleCloudDrawer()" title="Mở bảng điều khiển Cloud Well-Architected V2">
                    <span class="apple-cloud-dot"></span>
                    <span>☁️ Cloud V2</span>
                </button>
            </div>
        </div>
    </header>

    <!-- CLOUD WELL-ARCHITECTED V2 LIVE DRAWER (#cloud-drawer) -->
    <div id="cloud-drawer">
        <div class="apple-container">
            <div class="cloud-grid">
                <div class="cloud-badges">
                    <div class="c-badge">Kiến trúc: <strong>{safe_arch}</strong></div>
                    <div class="c-badge">Node thụ lý: <strong id="current-node">{safe_node}</strong></div>
                    <div class="c-badge">Trạng thái hạ tầng: <strong id="az-status" style="color:#30d158;">AZ-a &amp; AZ-b ONLINE (Active-Active)</strong></div>
                    <div class="c-badge">Giao dịch: <strong>ACID (SELECT ... FOR UPDATE)</strong></div>
                </div>
                <div class="cloud-actions">
                    <button type="button" class="c-btn c-btn-blue" onclick="testLoadBalancing()">⚡ Bắn 10 Request Load Balancer</button>
                    <button type="button" id="btn-chaos" class="c-btn c-btn-red" onclick="toggleChaos()">🔥 Tiêm Lỗi: Hạ Sập Node 1</button>
                    <a href="/metrics" target="_blank" class="c-btn c-btn-green">📊 Prometheus Metrics</a>
                </div>
            </div>
            <div id="lb-log"></div>
        </div>
    </div>

    <!-- 2. APPLE CHAPTER NAV RIBBON (.chapternav right under Global Nav) -->
    <nav class="chapternav" aria-label="Danh mục dòng sản phẩm">
        <ul class="chapternav-items">
            <li class="chapternav-item active" data-cat="" onclick="filterByCategory('', this)">
                <div class="chapternav-icon">
                    <svg viewBox="0 0 36 36"><rect x="4" y="6" width="20" height="15" rx="2.5"></rect><rect x="20" y="13" width="12" height="17" rx="2"></rect><line x1="10" y1="25" x2="18" y2="25"></line></svg>
                </div>
                <span class="chapternav-label">Tất cả</span>
                <span class="chapternav-new">457 mẫu</span>
            </li>
            <li class="chapternav-item" data-cat="PC Core Ultra" onclick="filterByCategory('PC Core Ultra', this)">
                <div class="chapternav-icon">
                    <svg viewBox="0 0 36 36"><rect x="8" y="8" width="20" height="20" rx="3"></rect><rect x="13" y="13" width="10" height="10" rx="1.5"></rect><line x1="18" y1="4" x2="18" y2="8"></line><line x1="18" y1="28" x2="18" y2="32"></line><line x1="4" y1="18" x2="8" y2="18"></line><line x1="28" y1="18" x2="32" y2="18"></line></svg>
                </div>
                <span class="chapternav-label">PC Core Ultra</span>
                <span class="chapternav-new">Mới</span>
            </li>
            <li class="chapternav-item" data-cat="PC GAMING PREMIUM" onclick="filterByCategory('PC GAMING PREMIUM', this)">
                <div class="chapternav-icon">
                    <svg viewBox="0 0 36 36"><rect x="9" y="5" width="18" height="26" rx="3"></rect><circle cx="18" cy="14" r="4.5"></circle><circle cx="18" cy="24" r="2"></circle></svg>
                </div>
                <span class="chapternav-label">PC Gaming Pro</span>
                <span class="chapternav-new">Mới</span>
            </li>
            <li class="chapternav-item" data-cat="PC GAMING CAO CẤP" onclick="filterByCategory('PC GAMING CAO CẤP', this)">
                <div class="chapternav-icon">
                    <svg viewBox="0 0 36 36"><rect x="5" y="7" width="26" height="18" rx="2.5"></rect><line x1="18" y1="25" x2="18" y2="30"></line><line x1="12" y1="30" x2="24" y2="30"></line><path d="M12 16l4-4 4 4 4-5"></path></svg>
                </div>
                <span class="chapternav-label">PC Gaming Cao Cấp</span>
                <span class="chapternav-new">Mới</span>
            </li>
            <li class="chapternav-item" data-cat="PC STREAM GAME" onclick="filterByCategory('PC STREAM GAME', this)">
                <div class="chapternav-icon">
                    <svg viewBox="0 0 36 36"><rect x="13" y="6" width="10" height="16" rx="5"></rect><path d="M9 16a9 9 0 0 0 18 0"></path><line x1="18" y1="25" x2="18" y2="30"></line><line x1="13" y1="30" x2="23" y2="30"></line></svg>
                </div>
                <span class="chapternav-label">PC Stream Game</span>
            </li>
            <li class="chapternav-item" data-cat="PC GAMING GIÁ RẺ" onclick="filterByCategory('PC GAMING GIÁ RẺ', this)">
                <div class="chapternav-icon">
                    <svg viewBox="0 0 36 36"><rect x="10" y="7" width="16" height="22" rx="2.5"></rect><line x1="14" y1="12" x2="22" y2="12"></line><circle cx="18" cy="23" r="2"></circle></svg>
                </div>
                <span class="chapternav-label">PC Gaming Giá Rẻ</span>
            </li>
            <li class="chapternav-item" data-cat="PC ĐẸP" onclick="filterByCategory('PC ĐẸP', this)">
                <div class="chapternav-icon">
                    <svg viewBox="0 0 36 36"><polygon points="18 5 22 14 31 15 24 21 26 30 18 25 10 30 12 21 5 15 14 14"></polygon></svg>
                </div>
                <span class="chapternav-label">PC Đẹp</span>
                <span class="chapternav-new">Mới</span>
            </li>
            <li class="chapternav-item" onclick="scrollToSection('compare-section')">
                <div class="chapternav-icon">
                    <svg viewBox="0 0 36 36"><rect x="6" y="8" width="10" height="20" rx="2"></rect><rect x="20" y="8" width="10" height="20" rx="2"></rect></svg>
                </div>
                <span class="chapternav-label">So sánh</span>
            </li>
        </ul>
    </nav>

    <!-- 3. APPLE PROMOTIONAL RIBBON -->
    <div class="apple-promo-ribbon">
        <span>Nhận ưu đãi trả góp 0% trong 24 tháng khi mua cấu hình Flagship. Vận hành trên hạ tầng Cloud Well-Architected (Multi-AZ, RTO &lt; 2s).</span>
        <a href="#lineup-section" onclick="openPromoBag(); return false;">Mua ngay &gt;</a>
    </div>

    <main>
        <!-- 4. APPLE iPAD-STYLE HERO SECTION (.apple-hero) -->
        <section class="apple-hero" id="hero-section" data-enter="hero">
            <div class="apple-container">
                <div class="apple-hero-header">
                    <div>
                        <span class="apple-hero-eyebrow">THẾ HỆ MỚI</span>
                        <h1 class="apple-hero-title">iPad &amp; Studio PC Pro</h1>
                    </div>
                    <div class="apple-hero-right">
                        <p class="apple-hero-subheadline">
                            Mỏng không tưởng. Mạnh không ngờ. Sức mạnh đồ họa RTX 50 Series &amp; Core Ultra.
                        </p>
                        <p class="apple-hero-installment">
                            Từ 20.480.000 VNĐ hoặc 853.000đ/tháng trong 24 tháng.*
                        </p>
                        <div class="apple-hero-ctas">
                            <button type="button" class="apple-btn-primary" onclick="scrollToSection('lineup-section')">
                                Khám phá dòng sản phẩm
                            </button>
                            <span class="apple-link-cta" onclick="scrollToSection('compare-section')">
                                Xem bảng so sánh <span aria-hidden="true">&gt;</span>
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Hero Showcase Stage -->
                <div class="apple-hero-stage">
                    <div class="apple-hero-main-card">
                        <img src="/static/ttg_assets/hero_setup.jpg" alt="Apple Studio &amp; RTX 50 Series Flagship Setup">
                        <div class="apple-hero-main-overlay">
                            <div class="apple-hero-chip-row">
                                <span class="apple-hero-chip">RTX 5070 12GB GDDR7</span>
                                <span class="apple-hero-chip">Intel Core Ultra 7 270K</span>
                                <span class="apple-hero-chip">Cloud Multi-AZ Active-Active</span>
                            </div>
                            <h2 class="apple-hero-main-title">Hiệu năng chuẩn Studio. Kiến trúc không điểm nghẽn.</h2>
                            <p class="apple-hero-main-desc">
                                Chế tác cho nhà sáng tạo 3D, kỹ sư AI và game thủ Esports chuyên nghiệp. Đặt mua tức thì với cơ chế khóa dòng ACID chống bán âm kho.
                            </p>
                        </div>
                    </div>

                    <div class="apple-hero-side-stack">
                        <div class="apple-hero-spot-card">
                            <div class="apple-hero-spot-info">
                                <div class="apple-hero-spot-eyebrow">MỚI • FLAGSHIP ULTRA</div>
                                <div class="apple-hero-spot-title">PC Core Ultra 7 270K Plus — RTX 5070 12GB OC</div>
                                <div class="apple-hero-spot-price">Từ 51.680.000 VNĐ • Giảm 1.500.000đ mã APPLE2026</div>
                                <button type="button" class="apple-btn-primary" style="padding:7px 16px;font-size:12.5px;" onclick="buyProduct(6, 'PC TTG GAMING CORE ULTRA 7 270K PLUS - RTX 5070 12GB OC')">
                                    Mua ngay
                                </button>
                            </div>
                            <img class="apple-hero-spot-img" src="/static/ttg_assets/pc_6.png" alt="PC Core Ultra 7 270K Plus">
                        </div>

                        <div class="apple-hero-spot-card">
                            <div class="apple-hero-spot-info">
                                <div class="apple-hero-spot-eyebrow">MỚI • BÁN CHẠY NHẤT</div>
                                <div class="apple-hero-spot-title">PC AMD Gaming Pro Ryzen 7 5700X — RTX 5060 8GB</div>
                                <div class="apple-hero-spot-price">Từ 25.480.000 VNĐ • Trả góp 0% lãi suất</div>
                                <button type="button" class="apple-btn-primary" style="padding:7px 16px;font-size:12.5px;" onclick="buyProduct(3, 'PC TTG AMD GAMING PRO Ryzen 7 5700X - RTX 5060 8GB')">
                                    Mua ngay
                                </button>
                            </div>
                            <img class="apple-hero-spot-img" src="/static/ttg_assets/pc_3.png" alt="PC Ryzen 7 5700X RTX 5060">
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- 5. EXPLORE THE LINEUP ("Khám phá dòng sản phẩm.") -->
        <section class="apple-section" id="lineup-section">
            <div class="apple-container">
                <div class="apple-section-header">
                    <h2 class="apple-section-title">Khám phá dòng sản phẩm.</h2>
                    <span class="apple-link-cta" onclick="scrollToSection('compare-section')">
                        So sánh tất cả các phiên bản <span aria-hidden="true">&gt;</span>
                    </span>
                </div>

                <!-- Apple Filter & Instant Search Bar -->
                <div class="apple-filter-toolbar">
                    <div class="apple-filter-row-top">
                        <div class="apple-filter-pills" role="tablist" aria-label="Lọc theo phân khúc">
                            <button type="button" class="apple-filter-pill active" data-cat="" onclick="filterByCategory('')">Tất cả các mẫu</button>
                            <button type="button" class="apple-filter-pill" data-cat="PC Core Ultra" onclick="filterByCategory('PC Core Ultra')">PC Core Ultra</button>
                            <button type="button" class="apple-filter-pill" data-cat="PC GAMING PREMIUM" onclick="filterByCategory('PC GAMING PREMIUM')">PC Gaming Pro</button>
                            <button type="button" class="apple-filter-pill" data-cat="PC GAMING CAO CẤP" onclick="filterByCategory('PC GAMING CAO CẤP')">PC Gaming Cao Cấp</button>
                            <button type="button" class="apple-filter-pill" data-cat="PC STREAM GAME" onclick="filterByCategory('PC STREAM GAME')">PC Stream Game</button>
                            <button type="button" class="apple-filter-pill" data-cat="PC GAMING GIÁ RẺ" onclick="filterByCategory('PC GAMING GIÁ RẺ')">PC Gaming Giá Rẻ</button>
                            <button type="button" class="apple-filter-pill" data-cat="PC ĐẸP" onclick="filterByCategory('PC ĐẸP')">PC Đẹp</button>
                        </div>

                        <div class="apple-sort-meta">
                            <div class="found-text">Tìm thấy <span id="total-found">457</span> cấu hình</div>
                            <select class="sort-select" id="sort-select" onchange="sortProducts(this.value)" aria-label="Sắp xếp theo giá">
                                <option value="default">Sắp xếp: Nổi bật</option>
                                <option value="asc">Giá: Thấp đến Cao</option>
                                <option value="desc">Giá: Cao đến Thấp</option>
                            </select>
                        </div>
                    </div>

                    <div class="apple-filter-row-bottom">
                        <div class="apple-search-wrap">
                            <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7.5"></circle><line x1="20" y1="20" x2="16.2" y2="16.2"></line></svg>
                            <input type="text" id="search-input" class="apple-search-input" placeholder="Tìm theo chip Core Ultra, Ryzen 7, RTX 5070..." onkeyup="if(event.key==='Enter') doSearch()">
                            <button type="button" class="apple-search-btn" onclick="doSearch()">Tìm kiếm</button>
                        </div>

                        <div class="apple-price-filters">
                            <button type="button" class="apple-price-chip active" data-min="0" onclick="filterByPriceRange(0, 0, this)">Mọi mức giá</button>
                            <button type="button" class="apple-price-chip" onclick="filterByPriceRange(15, 25, this)">15 – 25 triệu</button>
                            <button type="button" class="apple-price-chip" onclick="filterByPriceRange(25, 40, this)">25 – 40 triệu</button>
                            <button type="button" class="apple-price-chip" onclick="filterByPriceRange(40, 100, this)">Trên 40 triệu</button>
                            <button type="button" class="apple-price-chip" onclick="filterBySearch('RTX 5070', false)">Chip RTX 5070</button>
                        </div>
                    </div>
                </div>

                <!-- Product Grid -->
                <div id="product-grid" class="product-grid">
                    <div style="grid-column:1/-1;padding:48px;text-align:center;color:#6e6e73;">Đang tải dòng sản phẩm Studio PC Pro...</div>
                </div>
            </div>
        </section>

        <!-- 6. 4-CARD BENTO GRID ("Vì sao Apple / TTG Studio là nơi tốt nhất để mua.") -->
        <section class="apple-section" id="why-apple-section">
            <div class="apple-container">
                <div class="apple-section-header">
                    <h2 class="apple-section-title">Vì sao Apple / TTG Studio là nơi tốt nhất để mua.</h2>
                    <span class="apple-link-cta" onclick="showCartSummary()">
                        Mở Giỏ hàng &amp; Ưu đãi APPLE2026 <span aria-hidden="true">&gt;</span>
                    </span>
                </div>

                <div class="apple-bento-grid">
                    <article class="apple-bento-card">
                        <div>
                            <div class="apple-bento-icon">
                                <svg viewBox="0 0 24 24"><rect x="2" y="5" width="20" height="14" rx="2"></rect><line x1="2" y1="10" x2="22" y2="10"></line></svg>
                            </div>
                            <h3 class="apple-bento-title">Trả góp 0% Lãi Suất</h3>
                            <p class="apple-bento-desc">
                                Sở hữu ngay cấu hình Flagship mơ ước và chia nhỏ thanh toán trong 24 tháng với lãi suất 0% qua Apple Pay, VietQR 24/7 hoặc thẻ tín dụng.
                            </p>
                        </div>
                    </article>

                    <article class="apple-bento-card">
                        <div>
                            <div class="apple-bento-icon">
                                <svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                            </div>
                            <h3 class="apple-bento-title">Chống Bán Âm Kho ACID (SELECT ... FOR UPDATE)</h3>
                            <p class="apple-bento-desc">
                                Mọi giao dịch Flash Sale đều khóa dòng trực tiếp tại CSDL (Row-Level Locking), đảm bảo 100% không bán vượt tồn kho ngay cả khi 500 khách đặt cùng lúc.
                            </p>
                        </div>
                    </article>

                    <article class="apple-bento-card">
                        <div>
                            <div class="apple-bento-icon">
                                <svg viewBox="0 0 24 24"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>
                            </div>
                            <h3 class="apple-bento-title">Tự Động Chuyển Mạch Multi-AZ (RTO 1.46s)</h3>
                            <p class="apple-bento-desc">
                                Vận hành trên cụm Active-Active Replica (AZ-a &amp; AZ-b) với Nginx least_conn. Khi 1 node gặp sự cố, lưu lượng tự động chuyển mạch dưới 2 giây.
                            </p>
                        </div>
                    </article>

                    <article class="apple-bento-card">
                        <div>
                            <div class="apple-bento-icon">
                                <svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                            </div>
                            <h3 class="apple-bento-title">Giao Hàng Siêu Tốc &amp; Bảo Hành 36 Tháng</h3>
                            <p class="apple-bento-desc">
                                Giao lắp tận bàn miễn phí trong 2 giờ nội thành. Bảo hành chính hãng 1 đổi 1 suốt 36 tháng cùng hỗ trợ kỹ thuật từ xa 24/7.
                            </p>
                        </div>
                    </article>
                </div>
            </div>
        </section>

        <!-- 7. INTERACTIVE COMPARISON SECTION ("So sánh các phiên bản") -->
        <section class="apple-section" id="compare-section">
            <div class="apple-container">
                <div class="apple-section-header">
                    <h2 class="apple-section-title">So sánh các phiên bản.</h2>
                    <span class="apple-link-cta" onclick="scrollToSection('lineup-section')">
                        Xem toàn bộ 457 cấu hình <span aria-hidden="true">&gt;</span>
                    </span>
                </div>

                <div class="apple-compare-wrap">
                    <div id="apple-compare-grid" class="apple-compare-grid"></div>
                </div>
            </div>
        </section>
    </main>

    <!-- APPLE FOOTER -->
    <footer class="apple-footer">
        <div class="apple-container">
            <p style="margin-bottom:10px;">
                * Chương trình trả góp 0% áp dụng cho kỳ hạn 6–24 tháng. Nhập mã <strong>APPLE2026</strong> tại Giỏ hàng để giảm ngay 1.500.000 VNĐ cho mọi cấu hình Studio PC Pro.
            </p>
            <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;padding-top:12px;border-top:1px solid rgba(0,0,0,0.08);">
                <span>Bản quyền © 2026 Apple / TTG Studio Vietnam. Bảo lưu mọi quyền.</span>
                <span>Hạ tầng: <strong>{safe_arch}</strong> • Node: <strong>{safe_node}</strong> • Chuẩn bảo mật Non-Root UID 10001</span>
            </div>
        </div>
    </footer>

    <!-- Toast Notification Container -->
    <div id="toast-container"></div>

    <!-- Interactive Apple Store & ACID Bag Checkout Engine -->
    <script src="/static/apple_store.js"></script>
</body>
</html>"""
