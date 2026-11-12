/* ==========================================================================
   Shopee Vietnam (shopee.vn) E-Commerce Interactive Engine (shopee_store.js)
   Owned by: Worker 1 (@shopee-ui)
   Signature Shopee Orange Theme & Architecture:
   - Full Shopee UI: Carousel, Mall Ribbon, Flash Sale Timer, Dynamic Product Cards
   - Cloud Well-Architected V2 Controls (#cloud-drawer, Multi-AZ Active-Active, Chaos Injection)
   - ACID Checkout (#shopee-checkout-modal, SHOPEE2026, ShopeePay, Apple Pay, VietQR)
   - Shopee Floating Live Chat & Back-to-top Widget
   ========================================================================== */

(function () {
    'use strict';

    /* ----------------------------------------------------------------------
       1. UTILITIES & SAFE XSS ESCAPING
       ---------------------------------------------------------------------- */
    function escapeHtml(raw) {
        if (raw === null || raw === undefined) return '';
        return String(raw)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatVND(amount) {
        const num = Number(amount) || 0;
        return num.toLocaleString('vi-VN') + '₫';
    }

    function formatVNDFull(amount) {
        const num = Number(amount) || 0;
        return num.toLocaleString('vi-VN') + ' VNĐ';
    }

    /* ----------------------------------------------------------------------
       2. GLOBAL STATE & PROMO DISCOUNTS
       ---------------------------------------------------------------------- */
    window.currentItems = [];
    window.cartCount = 0;

    const PROMO_DISCOUNTS = {
        'SHOPEE2026': 1500000,
        'SHOPEE500K': 500000,
        'UTH2026': 1000000,
        'TTG500K': 500000,
        'APPLE2026': 1500000
    };

    const cartState = {
        items: [],
        promoCode: 'SHOPEE2026',
        discountAmount: 1500000,
        paymentMethod: 'Ví ShopeePay'
    };
    window.shopeeCartState = cartState;

    let currentCategoryFilter = '';
    let currentSearchFilter = '';
    let currentDisplayLimit = 18;
    let currentSortMode = 'pop';

    /* ----------------------------------------------------------------------
       3. TOAST NOTIFICATIONS (SHOPEE STYLE)
       ---------------------------------------------------------------------- */
    window.showShopeeToast = function (title, desc) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'shopee-toast';
        toast.innerHTML = `
            <div class="shopee-toast-icon">✓</div>
            <div>
                <div class="shopee-toast-title">${escapeHtml(title)}</div>
                <div class="shopee-toast-desc">${escapeHtml(desc)}</div>
            </div>
        `;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.transition = 'opacity 0.25s ease, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1)';
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            setTimeout(() => toast.remove(), 260);
        }, 3600);
    };

    // Global alias
    window.showToast = window.showShopeeToast;

    /* ----------------------------------------------------------------------
       4. CAROUSEL ENGINE (EDIFIER / RTX 50 SERIES HERO)
       ---------------------------------------------------------------------- */
    let carouselIdx = 0;
    const totalSlides = 2;
    let carouselTimer = null;

    function updateCarousel() {
        const track = document.getElementById('carousel-track');
        const dots = document.querySelectorAll('.shopee-car-dot');
        if (track) {
            track.style.transform = `translateX(-${carouselIdx * 50}%)`;
        }
        dots.forEach((dot, idx) => {
            dot.classList.toggle('active', idx === carouselIdx);
        });
    }

    window.moveCarousel = function (dir) {
        carouselIdx = (carouselIdx + dir + totalSlides) % totalSlides;
        updateCarousel();
        resetCarouselTimer();
    };

    window.jumpCarousel = function (idx) {
        carouselIdx = Math.max(0, Math.min(idx, totalSlides - 1));
        updateCarousel();
        resetCarouselTimer();
    };

    function resetCarouselTimer() {
        if (carouselTimer) clearInterval(carouselTimer);
        carouselTimer = setInterval(() => {
            carouselIdx = (carouselIdx + 1) % totalSlides;
            updateCarousel();
        }, 4500);
    }

    /* ----------------------------------------------------------------------
       5. FLASH SALE COUNTDOWN TIMER
       ---------------------------------------------------------------------- */
    let fsSecondsLeft = 2 * 3600 + 45 * 60 + 18; // 02:45:18

    function initFlashSaleTimer() {
        const hEl = document.getElementById('fs-hours');
        const mEl = document.getElementById('fs-mins');
        const sEl = document.getElementById('fs-secs');

        setInterval(() => {
            if (fsSecondsLeft > 0) fsSecondsLeft--;
            const h = Math.floor(fsSecondsLeft / 3600);
            const m = Math.floor((fsSecondsLeft % 3600) / 60);
            const s = fsSecondsLeft % 60;

            if (hEl) hEl.innerText = String(h).padStart(2, '0');
            if (mEl) mEl.innerText = String(m).padStart(2, '0');
            if (sEl) sEl.innerText = String(s).padStart(2, '0');
        }, 1000);
    }

    function renderFlashSaleRow(items) {
        const row = document.getElementById('flash-sale-items');
        if (!row) return;

        const deals = (items && items.length > 0 ? items : window.currentItems).slice(0, 6);
        if (deals.length === 0) return;

        row.innerHTML = deals.map((p, idx) => {
            const pid = Number(p.id) || (idx + 1);
            const safeName = escapeHtml(p.name || ('PC Gaming #' + pid));
            const safeImg = escapeHtml(p.image_url || `/static/ttg_assets/pc_${((pid - 1) % 8) + 1}.png`);
            const price = Number(p.price) || 20480000;
            const soldCount = 28 + (pid * 7) % 65;
            const pct = Math.min(95, Math.max(30, soldCount * 1.2));

            return `
                <div class="shopee-fs-item" onclick="buyShopeeProduct(${pid}, '${safeName}')">
                    <div class="shopee-fs-img-box">
                        <img src="${safeImg}" alt="${safeName}" loading="lazy">
                        <span class="shopee-disc-tag">
                            ${escapeHtml(p.discount || '-18%')}
                            <span class="shopee-disc-tag-label">GIẢM</span>
                        </span>
                    </div>
                    <div class="shopee-fs-price">${formatVND(price)}</div>
                    <div class="shopee-fs-progress-wrap">
                        <div class="shopee-fs-progress-bar" style="width:${pct}%;"></div>
                        <div class="shopee-fs-progress-text">🔥 ĐÃ BÁN ${soldCount}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    /* ----------------------------------------------------------------------
       6. SHOPEE MALL BRANDS RIBBON
       ---------------------------------------------------------------------- */
    async function loadShopeeMallBrands() {
        try {
            const res = await fetch('/api/shopee/mall-brands');
            if (!res.ok) return;
            const data = await res.json();
            const brands = data.brands || [];
            if (!Array.isArray(brands) || brands.length === 0) return;

            const container = document.getElementById('shopee-mall-brands');
            if (!container) return;

            container.innerHTML = brands.slice(0, 6).map(b => `
                <div class="shopee-brand-col" onclick="filterBySearch('${escapeHtml(b.name)}')">
                    <div class="shopee-brand-logo-box">
                        <span class="shopee-brand-text" style="color:${escapeHtml(b.color || '#212121')};">
                            ${escapeHtml(b.logo_text || b.name)}
                        </span>
                    </div>
                    <div class="shopee-brand-promo">${escapeHtml(b.promo_label || 'Chính Hãng 100%')}</div>
                </div>
            `).join('');
        } catch (err) {
            console.warn('Shopee mall brands endpoint notice:', err);
        }
    }

    /* ----------------------------------------------------------------------
       7. PRODUCT GRID & SHOPEE CARD RENDERING
       ---------------------------------------------------------------------- */
    window.renderGrid = function (items) {
        const grid = document.getElementById('product-grid');
        if (!grid) return;

        if (!items || items.length === 0) {
            grid.innerHTML = `
                <div class="shopee-grid-loading">
                    <div style="font-size:16px;font-weight:600;color:#ee4d2d;margin-bottom:8px;">Không tìm thấy sản phẩm phù hợp</div>
                    <div style="font-size:13px;color:#757575;margin-bottom:14px;">Thử tìm với từ khóa "RTX 5060", "Core Ultra", hoặc bấm nút bên dưới để xem toàn bộ danh mục.</div>
                    <button type="button" class="shopee-cat-pill active" onclick="filterByCategory('')">Xem tất cả sản phẩm</button>
                </div>
            `;
            return;
        }

        grid.innerHTML = items.map((p, idx) => {
            const pid = Number(p.id) || (idx + 1);
            const safeName = escapeHtml(p.name || ('PC Gaming #' + pid));
            const safeImg = escapeHtml(p.image_url || `/static/ttg_assets/pc_${((pid - 1) % 8) + 1}.png`);
            const price = Number(p.price) || 20480000;
            const oldPrice = Number(p.old_price) || Math.round(price * 1.15);
            const discount = escapeHtml(p.discount || '-15%');
            const stock = typeof p.stock === 'number' ? p.stock : 100;
            const isMall = pid % 2 === 0;
            const soldCount = (1.2 + (pid * 0.1)).toFixed(1);

            return `
                <article class="shopee-card" data-product-id="${pid}">
                    <!-- Top-right Yellow Discount Tag -->
                    <div class="shopee-disc-tag">
                        ${discount}
                        <span class="shopee-disc-tag-label">GIẢM</span>
                    </div>

                    <!-- Top-left Mall or Yêu Thích Badge -->
                    <span class="shopee-tag-badge ${isMall ? 'mall' : 'fav'}">
                        ${isMall ? 'Mall' : 'Yêu thích'}
                    </span>

                    <!-- Product Image -->
                    <div class="shopee-card-img-wrap" onclick="buyShopeeProduct(${pid}, '${safeName}')">
                        <img src="${safeImg}" alt="${safeName}" loading="lazy">
                        <span class="shopee-freeship-badge">Freeship Xtra</span>
                    </div>

                    <!-- Card Body -->
                    <div class="shopee-card-info">
                        <div>
                            <h3 class="shopee-card-title" title="${safeName}" onclick="buyShopeeProduct(${pid}, '${safeName}')">
                                ${safeName}
                            </h3>
                            <span class="shopee-card-voucher-tag">Giảm ₫500k</span>
                        </div>

                        <div>
                            <div class="shopee-card-price-row">
                                <span class="shopee-card-new-price">${formatVND(price)}</span>
                                <span class="shopee-card-old-price">${formatVND(oldPrice)}</span>
                            </div>

                            <div class="shopee-card-meta-row">
                                <span class="shopee-card-stars">★★★★★</span>
                                <span class="shopee-card-sold">Đã bán ${soldCount}k</span>
                            </div>
                            <div class="shopee-card-location">TP. Hồ Chí Minh • Kho: ${stock}</div>

                            <div class="shopee-card-actions">
                                <button type="button" class="shopee-btn-card-buy" onclick="buyShopeeProduct(${pid}, '${safeName}')">
                                    Mua ngay
                                </button>
                                <button type="button" class="shopee-btn-card-cart" onclick="addShopeeItemToCart(${pid}, '${safeName}', false)" title="Thêm vào giỏ">
                                    🛒
                                </button>
                            </div>
                        </div>
                    </div>
                </article>
            `;
        }).join('');
    };

    window.loadProducts = async function (category = '', search = '', limit = 18) {
        let url = `/api/products?limit=${limit}`;
        if (category) url += '&category=' + encodeURIComponent(category);
        if (search) url += '&search=' + encodeURIComponent(search);

        try {
            const res = await fetch(url);
            const data = await res.json();

            const nodeEl = document.getElementById('current-node');
            if (nodeEl && data.served_by) nodeEl.innerText = data.served_by;
            const footerNode = document.getElementById('footer-node');
            if (footerNode && data.served_by) footerNode.innerText = data.served_by;

            const totalEl = document.getElementById('total-found');
            if (totalEl) {
                totalEl.innerText = (category || search) ? String(data.count) : String(data.total_found || 457);
            }

            window.currentItems = Array.isArray(data.items) ? data.items : [];
            window.applySortingAndRender();
            renderFlashSaleRow(window.currentItems);
        } catch (err) {
            console.error('Fetch products error:', err);
        }
    };

    window.applySortingAndRender = function () {
        let list = [...(window.currentItems || [])];
        if (currentSortMode === 'asc') {
            list.sort((a, b) => a.price - b.price);
        } else if (currentSortMode === 'desc') {
            list.sort((a, b) => b.price - a.price);
        } else if (currentSortMode === 'sold') {
            list.sort((a, b) => b.stock - a.stock);
        }
        window.renderGrid(list);
    };

    window.filterByCategory = function (cat, triggerEl) {
        currentCategoryFilter = cat || '';
        document.querySelectorAll('.shopee-cat-pill[data-cat]').forEach(el => {
            el.classList.toggle('active', el.getAttribute('data-cat') === currentCategoryFilter);
        });

        const searchInput = document.getElementById('search-input');
        if (searchInput && !currentSearchFilter) searchInput.value = '';

        window.loadProducts(currentCategoryFilter, currentSearchFilter, currentDisplayLimit);

        if (triggerEl) {
            const recSection = document.getElementById('recommend-section');
            if (recSection) recSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    window.filterBySearch = function (kw, scrollToGrid = false) {
        currentSearchFilter = kw || '';
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.value = currentSearchFilter;

        window.loadProducts(currentCategoryFilter, currentSearchFilter, currentDisplayLimit);

        if (scrollToGrid) {
            const recSection = document.getElementById('recommend-section');
            if (recSection) recSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    window.quickSearchTag = function (tag) {
        window.filterBySearch(tag, true);
    };

    window.doShopeeSearch = function () {
        const input = document.getElementById('search-input');
        const kw = input ? input.value.trim() : '';
        window.filterBySearch(kw, true);
    };

    window.toggleSearchScopeDropdown = function () {
        const d = document.getElementById('search-scope-dropdown');
        if (d) d.classList.toggle('show');
    };

    window.setSearchScope = function (scopeText, itemEl) {
        const label = document.getElementById('search-scope-label');
        if (label) label.innerText = scopeText;
        document.querySelectorAll('.shopee-scope-item').forEach(el => el.classList.remove('active'));
        if (itemEl) itemEl.classList.add('active');
        const d = document.getElementById('search-scope-dropdown');
        if (d) d.classList.remove('show');
    };

    window.selectShopeeTab = function (tabKey, btnEl) {
        document.querySelectorAll('.shopee-tab-btn').forEach(b => b.classList.remove('active'));
        if (btnEl) btnEl.classList.add('active');

        if (tabKey === 'pc-gaming') {
            window.filterByCategory('PC GAMING PREMIUM');
        } else if (tabKey === 'flash-sale') {
            window.scrollToSection('flash-sale-section');
        } else if (tabKey === 'mall') {
            window.scrollToSection('mall-section');
        } else {
            window.filterByCategory('');
        }
    };

    window.sortShopeeProducts = function (mode, btnEl) {
        currentSortMode = mode;
        document.querySelectorAll('.shopee-sort-btn').forEach(b => b.classList.remove('active'));
        if (btnEl && btnEl.classList) btnEl.classList.add('active');
        window.applySortingAndRender();
    };

    window.loadMoreProducts = function () {
        currentDisplayLimit += 12;
        window.loadProducts(currentCategoryFilter, currentSearchFilter, currentDisplayLimit);
        window.showShopeeToast('Đã tải thêm sản phẩm', `Hiển thị ${currentDisplayLimit} sản phẩm Shopee Mall`);
    };

    window.scrollToSection = function (sectionId) {
        const el = document.getElementById(sectionId);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    window.scrollShopeeToTop = function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    /* ----------------------------------------------------------------------
       8. CLOUD WELL-ARCHITECTED V2 CONTROLS (#cloud-drawer)
       ---------------------------------------------------------------------- */
    window.toggleCloudDrawer = function () {
        const d = document.getElementById('cloud-drawer');
        if (!d) return;
        d.style.display = (d.style.display === 'none' || d.style.display === '') ? 'block' : 'none';
    };

    window.testLoadBalancing = async function () {
        const logBox = document.getElementById('lb-log');
        if (!logBox) return;
        logBox.style.display = 'block';
        logBox.innerHTML = '⚡ Đang gửi 10 request kiểm tra Nginx Load Balancer (Active-Active)...<br>';

        for (let i = 1; i <= 10; i++) {
            const t0 = performance.now();
            try {
                const res = await fetch('/health?t=' + Date.now() + '-' + i);
                const data = await res.json();
                const dt = (performance.now() - t0).toFixed(1);
                logBox.innerHTML += `[Request #${i.toString().padStart(2, '0')}] HTTP ${res.status} OK | Node: <strong style="color:#64d2ff;">${escapeHtml(data.node_id)}</strong> | RTT: ${dt} ms<br>`;
                const curNode = document.getElementById('current-node');
                if (curNode && data.node_id) curNode.innerText = data.node_id;
            } catch (e) {
                logBox.innerHTML += `[Request #${i}] ❌ Lỗi kết nối: ${escapeHtml(e)}<br>`;
            }
        }
        logBox.scrollTop = logBox.scrollHeight;
    };

    window.toggleChaos = async function () {
        try {
            const res = await fetch('/api/chaos/toggle-node-1', { method: 'POST' });
            const data = await res.json();
            const btn = document.getElementById('btn-chaos');
            const st = document.getElementById('az-status');
            const logBox = document.getElementById('lb-log');
            if (logBox) logBox.style.display = 'block';

            if (!data.node_1_active) {
                if (btn) {
                    btn.innerText = '💚 Khôi Phục: Bật Lại Node 1';
                    btn.className = 'c-btn c-btn-green';
                }
                if (st) {
                    st.innerText = 'AZ-a CRASHED -> FAILOVER AZ-b (RTO 1.46s)';
                    st.style.color = '#ffd60a';
                }
                if (logBox) {
                    logBox.innerHTML += `<div style="color:#ff453a;font-weight:600;margin-top:4px;">💥 [CHAOS TEST] Đã hạ sập app-replica-1 (AZ-a)! Nginx failover sang app-replica-2 trong 1.46s (RTO &lt; 2s).</div>`;
                }
            } else {
                if (btn) {
                    btn.innerText = '🔥 Tiêm Lỗi: Hạ Sập Node 1';
                    btn.className = 'c-btn c-btn-red';
                }
                if (st) {
                    st.innerText = 'AZ-a & AZ-b ONLINE (Active-Active)';
                    st.style.color = '#26aa99';
                }
                if (logBox) {
                    logBox.innerHTML += `<div style="color:#26aa99;font-weight:600;margin-top:4px;">✅ [RECOVERY] app-replica-1 (AZ-a) phục hồi trực tuyến. Cụm Active-Active hoạt động bình thường.</div>`;
                }
            }
        } catch (err) {
            console.error('Chaos toggle error:', err);
        }
    };

    /* ----------------------------------------------------------------------
       9. SHOPEE FLOATING LIVE CHAT WIDGET
       ---------------------------------------------------------------------- */
    window.toggleShopeeChat = function () {
        const box = document.getElementById('shopee-chat-box');
        if (!box) return;
        box.style.display = (box.style.display === 'none' || box.style.display === '') ? 'flex' : 'none';
        if (box.style.display === 'flex') {
            const input = document.getElementById('shopee-chat-input');
            if (input) setTimeout(() => input.focus(), 150);
        }
    };

    window.sendChatMessage = function () {
        const input = document.getElementById('shopee-chat-input');
        if (!input) return;
        const msg = input.value.trim();
        if (!msg) return;

        appendChatMessage('user', msg);
        input.value = '';

        setTimeout(() => {
            handleBotChatReply(msg);
        }, 600);
    };

    window.sendQuickChatMessage = function (text) {
        appendChatMessage('user', text);
        setTimeout(() => {
            handleBotChatReply(text);
        }, 500);
    };

    function appendChatMessage(sender, text) {
        const msgs = document.getElementById('shopee-chat-messages');
        if (!msgs) return;
        const div = document.createElement('div');
        div.className = `shopee-msg ${sender}`;
        div.innerHTML = escapeHtml(text);
        msgs.appendChild(div);
        msgs.scrollTop = msgs.scrollHeight;
    }

    function handleBotChatReply(userMsg) {
        const low = userMsg.toLowerCase();
        let reply = 'Cảm ơn bạn đã nhắn tin cho Shopee Mall! Đội ngũ tư vấn kỹ thuật sẵn sàng hỗ trợ bạn.';

        if (low.includes('5060') || low.includes('rtx')) {
            reply = 'Dòng PC RTX 5060 8GB OC đang có ưu đãi tặng voucher 1.5 Triệu mã <strong>SHOPEE2026</strong>! Tồn kho sẵn sàng giao ngay trong 2 giờ.';
        } else if (low.includes('voucher') || low.includes('mã') || low.includes('giảm')) {
            reply = 'Mã giảm giá hot nhất hôm nay: <strong>SHOPEE2026</strong> (-1.500.000₫ cho PC Gaming), <strong>SHOPEE500K</strong> (-500.000₫), <strong>UTH2026</strong> (-1.000.000₫). Áp dụng ngay tại Giỏ hàng!';
        } else if (low.includes('freeship') || low.includes('vận chuyển')) {
            reply = 'Tất cả đơn hàng PC Gaming Shopee Mall đều được Miễn Phí Vận Chuyển Toàn Quốc (Freeship Xtra). Giao hỏa tốc 2H tại TP.HCM & Hà Nội.';
        } else if (low.includes('cloud') || low.includes('v2') || low.includes('acid')) {
            reply = 'Hệ thống vận hành kiến trúc Cloud Well-Architected V2 với Active-Active Multi-AZ và giao dịch khóa dòng ACID chống bán âm kho 100%.';
        }

        const msgs = document.getElementById('shopee-chat-messages');
        if (!msgs) return;
        const div = document.createElement('div');
        div.className = 'shopee-msg bot';
        div.innerHTML = reply;
        msgs.appendChild(div);
        msgs.scrollTop = msgs.scrollHeight;
    }

    /* ----------------------------------------------------------------------
       10. SHOPEE CART & ACID CHECKOUT MODAL (#shopee-checkout-modal)
       ---------------------------------------------------------------------- */
    function getTotalCartCount() {
        return cartState.items.reduce((acc, item) => acc + item.quantity, 0);
    }

    function getCartSubtotal() {
        return cartState.items.reduce((acc, item) => acc + (item.price * item.quantity), 0);
    }

    function recomputeDiscount() {
        const subtotal = getCartSubtotal();
        if (subtotal <= 0) {
            cartState.discountAmount = 0;
            return 0;
        }
        const code = (cartState.promoCode || '').trim().toUpperCase();
        const rawDisc = PROMO_DISCOUNTS[code] || 0;
        cartState.discountAmount = Math.min(rawDisc, subtotal);
        return cartState.discountAmount;
    }

    function syncHeaderCartBadge() {
        const total = getTotalCartCount();
        window.cartCount = total;
        const badge = document.getElementById('cart-badge');
        if (badge) {
            badge.innerText = String(total);
            badge.style.transform = 'scale(1.3)';
            setTimeout(() => {
                badge.style.transform = 'scale(1)';
            }, 180);
        }
    }

    window.showCartSummary = function () {
        openShopeeCheckout();
    };

    window.openShopeeCheckout = function () {
        const modal = document.getElementById('shopee-checkout-modal');
        if (!modal) return;
        renderShopeeModalCart();
        modal.style.display = 'flex';
    };

    window.closeShopeeCheckout = function () {
        const modal = document.getElementById('shopee-checkout-modal');
        if (modal) modal.style.display = 'none';
    };

    window.selectVoucherChip = function (code) {
        cartState.promoCode = code;
        const input = document.getElementById('shopee-voucher-input');
        if (input) input.value = code;

        document.querySelectorAll('.shopee-voucher-chip').forEach(c => {
            c.classList.toggle('active', c.getAttribute('data-promo') === code);
        });

        recomputeDiscount();
        renderShopeeModalCart();
        window.showShopeeToast('Đã chọn mã ' + code, `Giảm ngay ${formatVND(PROMO_DISCOUNTS[code] || 0)}`);
    };

    window.quickApplyPromo = function (code) {
        window.selectVoucherChip(code);
        window.openShopeeCheckout();
    };

    window.applyVoucherInput = function () {
        const input = document.getElementById('shopee-voucher-input');
        if (!input) return;
        const code = input.value.trim().toUpperCase();
        window.selectVoucherChip(code);
    };

    window.handlePaymentChange = function (radioEl) {
        if (!radioEl) return;
        cartState.paymentMethod = radioEl.value;

        document.querySelectorAll('.shopee-pay-option').forEach(opt => {
            const rad = opt.querySelector('input[type="radio"]');
            opt.classList.toggle('active', rad && rad.checked);
        });

        const vietqrBox = document.getElementById('shopee-vietqr-box');
        if (vietqrBox) {
            vietqrBox.style.display = radioEl.value.includes('VietQR') ? 'flex' : 'none';
        }
    };

    function renderShopeeModalCart() {
        const listEl = document.getElementById('shopee-cart-items-container');
        if (!listEl) return;

        const totalQty = getTotalCartCount();
        const subtotal = getCartSubtotal();
        const discount = recomputeDiscount();
        const finalTotal = Math.max(0, subtotal - discount);

        const countEl = document.getElementById('shopee-cart-count');
        const subtotalEl = document.getElementById('shopee-subtotal-val');
        const promoLabelEl = document.getElementById('shopee-applied-promo');
        const discountEl = document.getElementById('shopee-discount-val');
        const totalEl = document.getElementById('shopee-total-val');
        const submitBtn = document.getElementById('shopee-checkout-submit-btn');

        if (countEl) countEl.innerText = String(totalQty);
        if (subtotalEl) subtotalEl.innerText = formatVND(subtotal);
        if (promoLabelEl) promoLabelEl.innerText = discount > 0 ? escapeHtml(cartState.promoCode.toUpperCase()) : 'Chưa áp dụng';
        if (discountEl) discountEl.innerText = '-' + formatVND(discount);
        if (totalEl) totalEl.innerText = formatVND(finalTotal);
        if (submitBtn) submitBtn.disabled = cartState.items.length === 0;

        if (cartState.items.length === 0) {
            listEl.innerHTML = `
                <div class="shopee-cart-empty">
                    🛒 Giỏ hàng Shopee của bạn đang trống.<br>
                    Hãy bấm <strong>"Mua ngay"</strong> trên sản phẩm hoặc bấm <strong>"+ Thêm nhanh PC Core Ultra 7"</strong>.
                </div>
            `;
            return;
        }

        listEl.innerHTML = cartState.items.map(item => `
            <div class="shopee-cart-item" data-product-id="${item.id}">
                <img class="shopee-cart-thumb" src="${escapeHtml(item.image_url)}" alt="${escapeHtml(item.name)}">
                <div class="shopee-cart-info">
                    <div class="shopee-cart-name">${escapeHtml(item.name)}</div>
                    <div class="shopee-cart-price">${formatVND(item.price)} <span style="font-size:11px;color:#888;font-weight:400;">(Kho: ${escapeHtml(item.stock)})</span></div>
                </div>
                <div class="shopee-qty-controls">
                    <button type="button" class="shopee-qty-btn" onclick="updateShopeeCartQty(${item.id}, 'dec')" aria-label="Giảm">−</button>
                    <span class="shopee-qty-val">${escapeHtml(item.quantity)}</span>
                    <button type="button" class="shopee-qty-btn" onclick="updateShopeeCartQty(${item.id}, 'inc')" aria-label="Tăng">+</button>
                </div>
                <button type="button" class="shopee-remove-btn" onclick="updateShopeeCartQty(${item.id}, 'remove')" title="Xóa">✕</button>
            </div>
        `).join('');
    }

    window.updateShopeeCartQty = function (productId, action) {
        const idx = cartState.items.findIndex(i => Number(i.id) === Number(productId));
        if (idx === -1) return;

        if (action === 'inc') {
            if (cartState.items[idx].quantity < 20) {
                cartState.items[idx].quantity += 1;
            }
        } else if (action === 'dec') {
            cartState.items[idx].quantity -= 1;
            if (cartState.items[idx].quantity <= 0) {
                cartState.items.splice(idx, 1);
            }
        } else if (action === 'remove') {
            cartState.items.splice(idx, 1);
        }

        syncHeaderCartBadge();
        renderShopeeModalCart();
    };

    window.addShopeeItemToCart = function (productId, productName, openModal = true) {
        const pid = Number(productId) || 1;
        const prod = (window.currentItems || []).find(i => Number(i.id) === pid);

        const name = prod ? prod.name : (productName || ('PC Gaming #' + pid));
        const price = prod ? Number(prod.price) : 25480000;
        const img = prod ? prod.image_url : `/static/ttg_assets/pc_${((pid - 1) % 8) + 1}.png`;
        const stock = prod && typeof prod.stock === 'number' ? prod.stock : 100;

        const existing = cartState.items.find(i => Number(i.id) === pid);
        if (existing) {
            existing.quantity = Math.min(20, existing.quantity + 1);
            existing.price = price;
            existing.stock = stock;
        } else {
            cartState.items.push({
                id: pid,
                name: name,
                price: price,
                image_url: img,
                stock: stock,
                quantity: 1
            });
        }

        syncHeaderCartBadge();
        renderShopeeModalCart();

        window.showShopeeToast('Đã thêm vào giỏ hàng Shopee', `${name} • ${formatVND(price)}`);

        if (openModal) {
            window.openShopeeCheckout();
        }
    };

    window.buyShopeeProduct = function (productId, name) {
        const receipt = document.getElementById('shopee-order-receipt');
        if (receipt) receipt.style.display = 'none';
        window.addShopeeItemToCart(productId, name, true);
    };

    window.addSampleShopeeProduct = function () {
        window.addShopeeItemToCart(6, 'PC TTG GAMING CORE ULTRA 7 270K PLUS - RTX 5070 12GB OC', false);
    };

    window.submitShopeeAcidCheckout = async function () {
        if (cartState.items.length === 0) return;

        const nameInput = document.getElementById('shopee-cust-name');
        const phoneInput = document.getElementById('shopee-cust-phone');
        const addrInput = document.getElementById('shopee-cust-address');
        const submitBtn = document.getElementById('shopee-checkout-submit-btn');
        const receiptBox = document.getElementById('shopee-order-receipt');

        const customerName = (nameInput ? nameInput.value.trim() : '') || 'vqp5u19dtu';
        const phone = (phoneInput ? phoneInput.value.trim() : '') || '0909123456';
        const address = (addrInput ? addrInput.value.trim() : '') || 'TP. Hồ Chí Minh';
        const promoCode = cartState.promoCode || 'SHOPEE2026';
        const paymentMethod = cartState.paymentMethod || 'Ví ShopeePay';

        submitBtn.disabled = true;
        submitBtn.innerText = 'Đang khóa dòng ACID & Xác nhận đơn hàng...';

        try {
            const payload = {
                customer_name: customerName,
                phone: phone,
                address: address,
                payment_method: paymentMethod,
                promo_code: promoCode,
                items: cartState.items.map(i => ({
                    product_id: i.id,
                    quantity: i.quantity
                }))
            };

            const res = await fetch('/api/checkout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errJson = await res.json().catch(() => ({}));
                throw new Error(errJson.detail || 'Giao dịch bị từ chối để bảo vệ toàn vẹn tồn kho ACID');
            }

            const data = await res.json();
            const orderId = Array.isArray(data.order_ids) && data.order_ids.length > 0
                ? data.order_ids.join(', #')
                : (data.order_id || 'SHOPEE-' + Date.now());

            const servedBy = data.served_by || 'app-replica-1 (AZ-a)';
            const finalAmount = typeof data.final_amount === 'number'
                ? data.final_amount
                : Math.max(0, getCartSubtotal() - recomputeDiscount());

            const remainingInfo = Array.isArray(data.items_processed) && data.items_processed.length > 0
                ? data.items_processed.map(it => `${it.name || ('SP #' + it.product_id)}: còn ${it.remaining_stock} bộ`).join(' | ')
                : (typeof data.remaining_stock !== 'undefined' ? `Còn ${data.remaining_stock} bộ` : 'Đã trừ tồn kho ACID');

            const curNode = document.getElementById('current-node');
            if (curNode) curNode.innerText = servedBy;

            if (receiptBox) {
                receiptBox.style.display = 'block';
                receiptBox.innerHTML = `
                    <div class="shopee-receipt-title">
                        ✓ Đặt Hàng Shopee Thành Công — Mã Đơn #${escapeHtml(orderId)}
                    </div>
                    <div>
                        <div>• Khách hàng: <strong>${escapeHtml(customerName)}</strong> (${escapeHtml(phone)})</div>
                        <div>• Địa chỉ giao hàng: <strong>${escapeHtml(address)}</strong></div>
                        <div>• Phương thức thanh toán: <strong>${escapeHtml(paymentMethod)}</strong> • Tổng tiền: <strong style="color:#ee4d2d;">${formatVND(finalAmount)}</strong></div>
                        <div>• Hạ tầng thụ lý: <strong>${escapeHtml(servedBy)}</strong> (ACID SELECT ... FOR UPDATE)</div>
                        <div>• Tồn kho cập nhật: <strong>${escapeHtml(remainingInfo)}</strong></div>
                    </div>
                `;
            }

            window.showShopeeToast(
                `Đặt hàng Shopee thành công!`,
                `Đơn #${orderId} • Tổng: ${formatVND(finalAmount)} • Node: ${servedBy}`
            );

            cartState.items = [];
            syncHeaderCartBadge();
            renderShopeeModalCart();
            window.loadProducts(currentCategoryFilter, currentSearchFilter, currentDisplayLimit);
        } catch (err) {
            const msg = err && err.message ? err.message : String(err);
            window.showShopeeToast('Giao dịch ACID Rollback', msg);
        } finally {
            submitBtn.disabled = cartState.items.length === 0;
            submitBtn.innerText = 'Đặt Hàng (Thanh Toán ACID)';
        }
    };

    // Backward compatibility aliases
    window.buyProduct = window.buyShopeeProduct;
    window.openPromoBag = function () {
        window.quickApplyPromo('SHOPEE2026');
    };

    /* ----------------------------------------------------------------------
       11. BOOTSTRAP ON DOM READY
       ---------------------------------------------------------------------- */
    function bootShopeeStore() {
        initFlashSaleTimer();
        resetCarouselTimer();
        window.loadProducts('', '', 18);
        loadShopeeMallBrands();
        syncHeaderCartBadge();

        // Close search scope dropdown on outside click
        document.addEventListener('click', (e) => {
            const scopeBtn = document.getElementById('search-scope-btn');
            const scopeDropdown = document.getElementById('search-scope-dropdown');
            if (scopeBtn && scopeDropdown && !scopeBtn.contains(e.target)) {
                scopeDropdown.classList.remove('show');
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootShopeeStore);
    } else {
        bootShopeeStore();
    }
})();
