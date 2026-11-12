/* ==========================================================================
   Apple Vietnam iPad / Store Showcase Interactive Engine (apple_store.js)
   Owned by: Worker 1 (@ui-frontend)
   Follows apple-design, taste-skill & emil-design-eng — Zero Flying Bees
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
        return num.toLocaleString('vi-VN') + ' VNĐ';
    }

    function formatMonthlyVND(amount) {
        const monthly = Math.round((Number(amount) || 0) / 24 / 1000) * 1000;
        return monthly.toLocaleString('vi-VN') + 'đ/tháng';
    }

    /* ----------------------------------------------------------------------
       2. GLOBAL STATE & HARDWARE SPEC CATALOG (WITH FALLBACK)
       ---------------------------------------------------------------------- */
    window.currentItems = [];
    window.cartCount = 0;

    const PROMO_CODES = {
        'APPLE2026': 1500000,
        'UTH2026': 1000000,
        'TTG500K': 500000
    };

    const FINISH_SWATCHES = [
        { name: 'Space Black', hex: '#2e2c2e', bg: 'radial-gradient(circle at 50% 45%, #ffffff 0%, #ededf2 100%)' },
        { name: 'Silver', hex: '#e3e4e5', bg: 'radial-gradient(circle at 50% 45%, #ffffff 0%, #f5f5f7 100%)' },
        { name: 'Sky Blue', hex: '#c8d8e4', bg: 'radial-gradient(circle at 50% 45%, #ffffff 0%, #eef5fa 100%)' },
        { name: 'Starlight', hex: '#f0e4d3', bg: 'radial-gradient(circle at 50% 45%, #ffffff 0%, #faf6f0 100%)' }
    ];

    const FALLBACK_COMPARE_MODELS = [
        {
            id: 6,
            sku: 'TTG-PC-0006',
            badge: 'MỚI • FLAGSHIP STUDIO',
            brand: 'ASUS ROG',
            name: 'PC Core Ultra 7 270K Plus',
            tagline: 'Sức mạnh tối thượng cho AI, 3D Render & 4K AAA.',
            price: 51680000,
            old_price: 55990000,
            discount: '-8%',
            stock: 80,
            image_url: '/static/ttg_assets/pc_6.png',
            cpu: 'Intel Core Ultra 7 270K Plus (20 Nhân / 20 Luồng, NPU AI)',
            gpu: 'NVIDIA GeForce RTX 5070 12GB GDDR7 OC',
            ram: '32GB DDR5 6400MHz RGB Dual-Channel',
            ssd: '1TB NVMe PCIe Gen4 x4 (7400MB/s)',
            display_cooling: 'Tản nhiệt nước AIO 360mm IPS + Hỗ trợ 3 màn 8K',
            cloud_sla: 'ACID Row-Lock • Multi-AZ RTO 1.46s • BH 36 Tháng'
        },
        {
            id: 5,
            sku: 'TTG-PC-0005',
            badge: 'MỚI • HI-END PRO',
            brand: 'INTEL',
            name: 'PC Gaming i5 14600KF Pro',
            tagline: 'Cân bằng hoàn hảo giữa tốc độ xung nhịp & đồ họa RTX 5070.',
            price: 44480000,
            old_price: 48990000,
            discount: '-9%',
            stock: 95,
            image_url: '/static/ttg_assets/pc_5.png',
            cpu: 'Intel Core i5-14600KF (14 Nhân / 20 Luồng, 5.3GHz)',
            gpu: 'NVIDIA GeForce RTX 5070 12GB GDDR7',
            ram: '32GB DDR5 6000MHz Low-Latency',
            ssd: '1TB NVMe PCIe 4.0 M.2',
            display_cooling: 'Tản nhiệt nước AIO 240mm ARGB + G-Sync 240Hz',
            cloud_sla: 'ACID Row-Lock • Multi-AZ RTO 1.46s • BH 36 Tháng'
        },
        {
            id: 2,
            sku: 'TTG-PC-0002',
            badge: 'MỚI • CORE ULTRA',
            brand: 'INTEL',
            name: 'PC Core Ultra 5 250K Plus',
            tagline: 'Kiến trúc Arrow Lake thế hệ mới, mát mẻ và bứt phá.',
            price: 38680000,
            old_price: 39990000,
            discount: '-3%',
            stock: 120,
            image_url: '/static/ttg_assets/pc_2.png',
            cpu: 'Intel Core Ultra 5 250K Plus (14 Nhân / 14 Luồng)',
            gpu: 'NVIDIA GeForce RTX 5060 8GB GDDR7',
            ram: '32GB DDR5 6000MHz Dual-Channel',
            ssd: '1TB NVMe PCIe Gen4 x4',
            display_cooling: 'Tản nhiệt nước AIO 240mm + Màn 2K 180Hz',
            cloud_sla: 'ACID Row-Lock • Multi-AZ RTO 1.46s • BH 36 Tháng'
        },
        {
            id: 8,
            sku: 'TTG-PC-0008',
            badge: 'MỚI • X3D ESPORTS',
            brand: 'COLORFUL',
            name: 'PC Ryzen 5 7500X3D Studio',
            tagline: 'Bộ nhớ đệm 3D V-Cache chuyên trị Esports & Streamer.',
            price: 32280000,
            old_price: 34990000,
            discount: '-8%',
            stock: 110,
            image_url: '/static/ttg_assets/pc_8.png',
            cpu: 'AMD Ryzen 5 7500X3D (6 Nhân / 12 Luồng, 3D V-Cache)',
            gpu: 'NVIDIA GeForce RTX 5060 8GB GDDR7 OC',
            ram: '16GB DDR5 6000MHz (Nâng cấp 64GB)',
            ssd: '512GB NVMe PCIe Gen4',
            display_cooling: 'Tản khí Dual-Tower Panoramic Glass',
            cloud_sla: 'ACID Row-Lock • Multi-AZ RTO 1.46s • BH 36 Tháng'
        }
    ];

    let compareCatalog = [...FALLBACK_COMPARE_MODELS];

    const cartState = {
        items: [],
        promoCode: 'APPLE2026',
        discountAmount: 0
    };
    window.ttgCartState = cartState;

    /* ----------------------------------------------------------------------
       3. APPLE TOAST NOTIFICATION
       ---------------------------------------------------------------------- */
    window.showToast = function (title, desc) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.innerHTML = `
            <div class="toast-icon">
                <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>
            </div>
            <div>
                <div style="font-weight:600;color:#ffffff;font-size:13px;">${escapeHtml(title)}</div>
                <div style="color:#d2d2d7;font-size:11.5px;">${escapeHtml(desc)}</div>
            </div>
        `;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.transition = 'opacity 0.25s ease, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1)';
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px) scale(0.96)';
            setTimeout(() => toast.remove(), 260);
        }, 3500);
    };

    /* ----------------------------------------------------------------------
       4. PRODUCT LINEUP GRID & APPLE FILTER CONTROLS
       ---------------------------------------------------------------------- */
    function inferTagline(product) {
        const name = (product.name || '').toUpperCase();
        if (name.includes('5070')) return 'Hiệu năng đồ họa RTX 5070 đỉnh cao cho 4K AAA & AI Studio.';
        if (name.includes('ULTRA')) return 'Vi xử lý Intel Core Ultra thế hệ mới tích hợp nhân NPU AI.';
        if (name.includes('7500X3D') || name.includes('5700X')) return 'Đa nhiệm mượt mà, tối ưu FPS với kiến trúc AMD Ryzen Pro.';
        return 'Thiết kế chuẩn Studio, vận hành êm ái, sẵn sàng cho mọi tác vụ.';
    }

    window.selectFinishSwatch = function (btn, finishName, bgStyle) {
        if (!btn) return;
        const card = btn.closest('.p-card');
        if (!card) return;
        card.querySelectorAll('.p-swatch').forEach(s => s.classList.remove('active'));
        btn.classList.add('active');
        const imgWrap = card.querySelector('.p-img-wrap');
        if (imgWrap && bgStyle) {
            imgWrap.style.background = bgStyle;
        }
        const finishLabel = card.querySelector('.p-finish-label');
        if (finishLabel && finishName) {
            finishLabel.innerText = 'Màu: ' + finishName;
        }
    };

    window.renderGrid = function (items) {
        const grid = document.getElementById('product-grid');
        if (!grid) return;

        if (!items || items.length === 0) {
            grid.innerHTML = `
                <div style="grid-column:1/-1;background:#ffffff;border-radius:28px;padding:56px 24px;text-align:center;color:#6e6e73;">
                    <div style="font-size:19px;font-weight:600;color:#1d1d1f;margin-bottom:8px;">Không tìm thấy cấu hình phù hợp</div>
                    <div style="font-size:14px;margin-bottom:18px;">Hãy thử tìm với từ khóa khác hoặc xem toàn bộ dòng sản phẩm Flagship.</div>
                    <button type="button" class="apple-btn-primary" onclick="filterByCategory('')">Xem tất cả cấu hình</button>
                </div>
            `;
            return;
        }

        grid.innerHTML = items.map(p => {
            const pid = Number(p.id) || 1;
            const safeName = escapeHtml(p.name || ('PC Studio #' + pid));
            const safeBrand = escapeHtml(p.brand || 'APPLE / TTG');
            const safeImg = escapeHtml(p.image_url || `/static/ttg_assets/pc_${((pid - 1) % 8) + 1}.png`);
            const safeDisc = escapeHtml(p.discount || '-10%');
            const stock = typeof p.stock === 'number' ? p.stock : 100;
            const tagline = escapeHtml(inferTagline(p));

            const swatchesHtml = FINISH_SWATCHES.map((sw, idx) => `
                <button type="button"
                    class="p-swatch ${idx === 0 ? 'active' : ''}"
                    style="background:${sw.hex};"
                    title="Màu ${escapeHtml(sw.name)}"
                    aria-label="Màu ${escapeHtml(sw.name)}"
                    onclick="selectFinishSwatch(this, '${escapeHtml(sw.name)}', '${sw.bg}')">
                </button>
            `).join('');

            return `
                <article class="p-card" data-product-id="${pid}">
                    <div>
                        <div class="p-img-wrap">
                            <img src="${safeImg}" alt="${safeName}" loading="lazy">
                        </div>
                        <div class="p-swatches" role="group" aria-label="Tùy chọn màu vỏ máy">
                            ${swatchesHtml}
                        </div>
                        <div class="p-eyebrow-row">
                            <span class="p-new-badge">MỚI</span>
                            <span class="p-brand-tag">${safeBrand}</span>
                        </div>
                        <h3 class="p-title" title="${safeName}">${safeName}</h3>
                        <p class="p-tagline">${tagline}</p>
                    </div>
                    <div>
                        <div class="p-price-block">
                            <div class="p-price-new">Từ ${formatVND(p.price)}</div>
                            <div style="font-size:11.5px;color:#6e6e73;margin-top:2px;">Hoặc ${formatMonthlyVND(p.price)} trong 24 tháng*</div>
                            <div class="p-price-sub">
                                <span class="p-price-old">${formatVND(p.old_price)}</span>
                                <span class="p-disc-badge">${safeDisc}</span>
                            </div>
                        </div>
                        <div class="p-stock-row">
                            <span class="stock-pill" title="Tồn kho khả dụng: ${stock} bộ">
                                ${stock > 0 ? 'Còn ' + stock + ' bộ sẵn giao' : 'Tạm hết hàng'}
                            </span>
                        </div>
                        <div class="p-actions">
                            <button type="button" class="btn-add-cart" data-buy-id="${pid}" data-buy-name="${safeName}">
                                Mua
                            </button>
                            <button type="button" class="p-learn-more" data-spec-id="${pid}">
                                Tìm hiểu thêm <span aria-hidden="true">&gt;</span>
                            </button>
                        </div>
                    </div>
                </article>
            `;
        }).join('');

        grid.querySelectorAll('.btn-add-cart[data-buy-id]').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = Number(btn.getAttribute('data-buy-id'));
                const name = btn.getAttribute('data-buy-name') || '';
                window.buyProduct(id, name);
            });
        });

        grid.querySelectorAll('.p-learn-more[data-spec-id]').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = Number(btn.getAttribute('data-spec-id'));
                window.openQuickSpecModal(id);
            });
        });
    };

    window.loadProducts = async function (category = '', search = '') {
        let url = '/api/products?limit=16';
        if (category) url += '&category=' + encodeURIComponent(category);
        if (search) url += '&search=' + encodeURIComponent(search);
        try {
            const res = await fetch(url);
            const data = await res.json();
            const nodeEl = document.getElementById('current-node');
            if (nodeEl && data.served_by) nodeEl.innerText = data.served_by;
            const totalEl = document.getElementById('total-found');
            if (totalEl) {
                totalEl.innerText = (category || search) ? String(data.count) : String(data.total_found || 457);
            }
            window.currentItems = Array.isArray(data.items) ? data.items : [];
            window.renderGrid(window.currentItems);
        } catch (err) {
            console.error('Fetch products error:', err);
        }
    };

    window.filterByCategory = function (cat, triggerEl) {
        const cleanCat = cat || '';
        document.querySelectorAll('.chapternav-item[data-cat]').forEach(el => {
            el.classList.toggle('active', el.getAttribute('data-cat') === cleanCat);
        });
        document.querySelectorAll('.apple-filter-pill[data-cat]').forEach(el => {
            el.classList.toggle('active', el.getAttribute('data-cat') === cleanCat);
        });
        document.querySelectorAll('.apple-price-chip').forEach(el => el.classList.remove('active'));
        const defaultPriceChip = document.querySelector('.apple-price-chip[data-min="0"]');
        if (defaultPriceChip) defaultPriceChip.classList.add('active');

        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.value = '';

        window.loadProducts(cleanCat, '');
        if (triggerEl) {
            const lineup = document.getElementById('lineup-section');
            if (lineup) lineup.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    window.filterBySearch = function (kw, scrollToLineup = false) {
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.value = kw || '';
        window.loadProducts('', kw || '');
        if (scrollToLineup) {
            const lineup = document.getElementById('lineup-section');
            if (lineup) lineup.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    window.doSearch = function () {
        const searchInput = document.getElementById('search-input');
        const kw = searchInput ? searchInput.value.trim() : '';
        window.filterBySearch(kw, false);
    };

    window.focusAppleSearch = function () {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setTimeout(() => searchInput.focus(), 320);
        }
    };

    window.filterByPriceRange = function (minM, maxM, btnEl) {
        document.querySelectorAll('.apple-price-chip').forEach(b => b.classList.remove('active'));
        if (btnEl) btnEl.classList.add('active');

        if (!minM && !maxM) {
            window.renderGrid(window.currentItems);
            const totalEl = document.getElementById('total-found');
            if (totalEl) totalEl.innerText = String(window.currentItems.length || 457);
            return;
        }
        const minV = (Number(minM) || 0) * 1000000;
        const maxV = (Number(maxM) || 999) * 1000000;
        const filtered = (window.currentItems || []).filter(p => p.price >= minV && p.price <= maxV);
        const totalEl = document.getElementById('total-found');
        if (totalEl) totalEl.innerText = String(filtered.length);
        window.renderGrid(filtered);
    };

    window.sortProducts = function (mode) {
        const copy = [...(window.currentItems || [])];
        if (mode === 'asc') copy.sort((a, b) => a.price - b.price);
        if (mode === 'desc') copy.sort((a, b) => b.price - a.price);
        window.renderGrid(copy);
    };

    window.scrollToSection = function (sectionId) {
        const target = document.getElementById(sectionId);
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    /* ----------------------------------------------------------------------
       5. INTERACTIVE COMPARISON SECTION ("So sánh các phiên bản")
       ---------------------------------------------------------------------- */
    function normalizeCompareModel(item, idx) {
        const specs = item.specs || {};
        const pid = Number(item.id || item.product_id || (idx + 1));
        return {
            id: pid,
            sku: item.sku || `TTG-PC-000${pid}`,
            badge: item.badge || item.eyebrow || 'MỚI • FLAGSHIP',
            brand: item.brand || 'APPLE / TTG',
            name: item.name || item.short_name || `PC Studio #${pid}`,
            tagline: item.tagline || item.description || inferTagline(item),
            price: Number(item.price) || 32280000,
            stock: typeof item.stock === 'number' ? item.stock : 100,
            image_url: item.image_url || `/static/ttg_assets/pc_${((pid - 1) % 8) + 1}.png`,
            cpu: item.cpu || specs.cpu || 'Intel Core Ultra / AMD Ryzen Pro',
            gpu: item.gpu || specs.gpu || 'NVIDIA GeForce RTX 50 Series GDDR7',
            ram: item.ram || specs.ram || '32GB DDR5 6000MHz Dual-Channel',
            ssd: item.ssd || item.storage || specs.ssd || '1TB NVMe PCIe Gen4 x4',
            display_cooling: item.display_cooling || item.cooling || specs.display_cooling || specs.cooling || 'Tản nhiệt nước AIO + Hỗ trợ màn hình 4K 240Hz',
            cloud_sla: item.cloud_sla || item.sla || specs.cloud_sla || 'ACID Row-Lock • Multi-AZ RTO 1.46s • BH 36 Tháng'
        };
    }

    function renderComparisonColumns(models) {
        const container = document.getElementById('apple-compare-grid');
        if (!container) return;

        const list = (models && models.length > 0 ? models : FALLBACK_COMPARE_MODELS).slice(0, 4);

        container.innerHTML = list.map(m => {
            const safeName = escapeHtml(m.name);
            return `
                <div class="compare-col">
                    <div class="compare-img-box">
                        <img src="${escapeHtml(m.image_url)}" alt="${safeName}" loading="lazy">
                    </div>
                    <div class="p-swatches" style="margin-bottom:10px;">
                        ${FINISH_SWATCHES.map(sw => `<span class="p-swatch" style="background:${sw.hex};cursor:default;"></span>`).join('')}
                    </div>
                    <div class="compare-badge">${escapeHtml(m.badge)}</div>
                    <div class="compare-name">${safeName}</div>
                    <div style="font-size:12.5px;color:#6e6e73;min-height:36px;margin-bottom:10px;">${escapeHtml(m.tagline)}</div>
                    <div class="compare-price">Từ ${formatVND(m.price)}</div>
                    <button type="button" class="apple-btn-primary" style="padding:7px 18px;font-size:13px;" data-compare-buy="${m.id}" data-compare-name="${safeName}">
                        Mua
                    </button>

                    <div class="compare-divider"></div>

                    <div class="compare-spec-block">
                        <div class="compare-spec-label">Vi xử lý (CPU)</div>
                        <div class="compare-spec-val">${escapeHtml(m.cpu)}</div>
                    </div>

                    <div class="compare-spec-block">
                        <div class="compare-spec-label">Đồ họa (GPU)</div>
                        <div class="compare-spec-val">${escapeHtml(m.gpu)}</div>
                    </div>

                    <div class="compare-spec-block">
                        <div class="compare-spec-label">Bộ nhớ &amp; Lưu trữ</div>
                        <div class="compare-spec-val">${escapeHtml(m.ram)}</div>
                        <div class="compare-spec-sub">${escapeHtml(m.ssd)}</div>
                    </div>

                    <div class="compare-spec-block">
                        <div class="compare-spec-label">Tản nhiệt &amp; Hiển thị</div>
                        <div class="compare-spec-val">${escapeHtml(m.display_cooling)}</div>
                    </div>

                    <div class="compare-spec-block" style="margin-bottom:0;">
                        <div class="compare-spec-label">Hạ tầng Cloud &amp; Bảo hành</div>
                        <div class="compare-spec-val" style="color:#0071e3;">${escapeHtml(m.cloud_sla)}</div>
                        <div class="compare-spec-sub">Sẵn kho: ${escapeHtml(m.stock)} bộ</div>
                    </div>
                </div>
            `;
        }).join('');

        container.querySelectorAll('button[data-compare-buy]').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = Number(btn.getAttribute('data-compare-buy'));
                const name = btn.getAttribute('data-compare-name') || '';
                window.buyProduct(id, name);
            });
        });
    }

    async function loadLineupComparison() {
        renderComparisonColumns(FALLBACK_COMPARE_MODELS);
        try {
            const res = await fetch('/api/lineup/compare');
            if (!res.ok) return;
            const data = await res.json();
            const rawList = data.featured_4 || data.items || data.lineup || data.models || [];
            if (Array.isArray(rawList) && rawList.length > 0) {
                const allRaw = data.items || data.lineup || rawList;
                compareCatalog = allRaw.map((item, idx) => normalizeCompareModel(item, idx));
                const featured = (data.featured_4 || rawList.slice(0, 4)).map((item, idx) => normalizeCompareModel(item, idx));
                renderComparisonColumns(featured);
            }
        } catch (err) {
            console.warn('Using fallback comparison catalog:', err);
        }
    }

    /* ----------------------------------------------------------------------
       6. QUICK SPEC SHEET MODAL ("Tìm hiểu thêm >")
       ---------------------------------------------------------------------- */
    function ensureQuickSpecModal() {
        if (document.getElementById('apple-spec-modal')) return;
        const modal = document.createElement('div');
        modal.id = 'apple-spec-modal';
        modal.innerHTML = `
            <div class="apple-spec-dialog" role="dialog" aria-modal="true" aria-labelledby="apple-spec-title">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:18px;">
                    <div>
                        <div id="apple-spec-eyebrow" style="font-size:11.5px;font-weight:700;color:#b64400;text-transform:uppercase;letter-spacing:0.05em;">THÔNG SỐ KỸ THUẬT STUDIO</div>
                        <h3 id="apple-spec-title" style="font-size:24px;font-weight:700;letter-spacing:-0.02em;color:#1d1d1f;margin-top:4px;">PC Studio Pro</h3>
                    </div>
                    <button type="button" class="ttg-checkout-close" id="apple-spec-close" aria-label="Đóng">✕</button>
                </div>
                <div id="apple-spec-body"></div>
            </div>
        `;
        document.body.appendChild(modal);
        document.getElementById('apple-spec-close').addEventListener('click', closeQuickSpecModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeQuickSpecModal();
        });
    }

    window.openQuickSpecModal = function (productId) {
        ensureQuickSpecModal();
        const pid = Number(productId) || 1;
        const mappedIdx = ((pid - 1) % 8) + 1;
        const prod = (window.currentItems || []).find(i => Number(i.id) === pid) || {};
        const comp = compareCatalog.find(c => Number(c.id) === mappedIdx) || FALLBACK_COMPARE_MODELS[0];

        const name = prod.name || comp.name || ('PC Studio #' + pid);
        const price = prod.price || comp.price || 32280000;
        const img = prod.image_url || comp.image_url || `/static/ttg_assets/pc_${mappedIdx}.png`;
        const stock = typeof prod.stock === 'number' ? prod.stock : (comp.stock || 100);

        document.getElementById('apple-spec-title').innerText = name;
        const body = document.getElementById('apple-spec-body');
        body.innerHTML = `
            <div style="display:grid;grid-template-columns:180px 1fr;gap:22px;align-items:center;margin-bottom:22px;">
                <div style="background:#f5f5f7;border-radius:20px;padding:16px;display:flex;align-items:center;justify-content:center;height:160px;">
                    <img src="${escapeHtml(img)}" alt="${escapeHtml(name)}" style="max-width:100%;max-height:100%;object-fit:contain;">
                </div>
                <div style="display:flex;flex-direction:column;gap:8px;font-size:13.5px;">
                    <div><strong>Vi xử lý (CPU):</strong> ${escapeHtml(comp.cpu)}</div>
                    <div><strong>Card đồ họa (GPU):</strong> ${escapeHtml(comp.gpu)}</div>
                    <div><strong>Bộ nhớ RAM:</strong> ${escapeHtml(comp.ram)}</div>
                    <div><strong>Ổ cứng SSD:</strong> ${escapeHtml(comp.ssd)}</div>
                    <div><strong>Tản nhiệt &amp; Hiển thị:</strong> ${escapeHtml(comp.display_cooling)}</div>
                    <div><strong>Bảo hành &amp; Cloud SLA:</strong> <span style="color:#0071e3;font-weight:600;">${escapeHtml(comp.cloud_sla)}</span></div>
                </div>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;padding-top:16px;border-top:1px solid rgba(0,0,0,0.08);">
                <div>
                    <div style="font-size:18px;font-weight:700;color:#1d1d1f;">${formatVND(price)}</div>
                    <div style="font-size:12px;color:#1d8348;font-weight:600;">Sẵn kho: ${escapeHtml(stock)} bộ • Giao nhanh 2 giờ</div>
                </div>
                <div style="display:flex;gap:10px;">
                    <button type="button" class="apple-filter-pill" id="apple-spec-compare-btn">Xem bảng so sánh</button>
                    <button type="button" class="apple-btn-primary" id="apple-spec-buy-btn">Thêm vào Giỏ hàng</button>
                </div>
            </div>
        `;

        document.getElementById('apple-spec-buy-btn').addEventListener('click', () => {
            closeQuickSpecModal();
            window.buyProduct(pid, name);
        });
        document.getElementById('apple-spec-compare-btn').addEventListener('click', () => {
            closeQuickSpecModal();
            window.scrollToSection('compare-section');
        });

        document.getElementById('apple-spec-modal').classList.add('open');
    };

    function closeQuickSpecModal() {
        const modal = document.getElementById('apple-spec-modal');
        if (modal) modal.classList.remove('open');
    }

    /* ----------------------------------------------------------------------
       7. CLOUD WELL-ARCHITECTED V2 LIVE CONTROLS
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
        logBox.innerHTML = '⚡ Đang gửi tuần tự 10 request kiểm tra Nginx Load Balancer (least_conn)...<br>';
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
                    logBox.innerHTML += `<div style="color:#ff453a;font-weight:600;margin-top:4px;">💥 [CHAOS TEST] Đã hạ sập app-replica-1 (AZ-a)! Nginx kích hoạt proxy_next_upstream chuyển mạch sang app-replica-2 trong 1.46s (RTO &lt; 2s).</div>`;
                }
            } else {
                if (btn) {
                    btn.innerText = '🔥 Tiêm Lỗi: Hạ Sập Node 1';
                    btn.className = 'c-btn c-btn-red';
                }
                if (st) {
                    st.innerText = 'AZ-a & AZ-b ONLINE (Active-Active)';
                    st.style.color = '#30d158';
                }
                if (logBox) {
                    logBox.innerHTML += `<div style="color:#30d158;font-weight:600;margin-top:4px;">✅ [RECOVERY] app-replica-1 (AZ-a) đã phục hồi trực tuyến. Cụm cân bằng tải hoạt động bình thường.</div>`;
                }
            }
        } catch (err) {
            console.error('Chaos toggle error:', err);
        }
    };

    /* ----------------------------------------------------------------------
       8. APPLE BAG DRAWER & ACID CHECKOUT SHEET (#ttg-checkout-modal)
       ---------------------------------------------------------------------- */
    function findProductMeta(productId, fallbackName) {
        const pid = Number(productId) || 1;
        if (Array.isArray(window.currentItems)) {
            const found = window.currentItems.find(item => Number(item.id) === pid);
            if (found) {
                return {
                    id: pid,
                    name: found.name || fallbackName || ('PC Studio #' + pid),
                    price: Number(found.price) || 25480000,
                    image_url: found.image_url || `/static/ttg_assets/pc_${((pid - 1) % 8) + 1}.png`,
                    stock: typeof found.stock === 'number' ? found.stock : 100
                };
            }
        }
        const comp = compareCatalog.find(c => Number(c.id) === pid);
        if (comp) {
            return {
                id: pid,
                name: comp.name,
                price: comp.price,
                image_url: comp.image_url,
                stock: comp.stock
            };
        }
        return {
            id: pid,
            name: fallbackName || ('Cấu hình PC Studio #' + pid),
            price: 38680000,
            image_url: `/static/ttg_assets/pc_${((pid - 1) % 8) + 1}.png`,
            stock: 100
        };
    }

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
        const rawDisc = PROMO_CODES[code] || 0;
        cartState.discountAmount = Math.min(rawDisc, subtotal);
        return cartState.discountAmount;
    }

    function syncHeaderCartBadge() {
        const total = getTotalCartCount();
        window.cartCount = total;
        const badge = document.getElementById('cart-badge');
        if (badge) {
            badge.innerText = String(total);
            badge.style.transform = 'scale(1.25)';
            setTimeout(() => {
                badge.style.transition = 'transform 0.22s cubic-bezier(0.16, 1, 0.3, 1)';
                badge.style.transform = 'scale(1)';
            }, 160);
        }
    }

    function initCheckoutModal() {
        // Hard cleanup of any legacy bee/HUD elements
        const oldHud = document.getElementById('swarm-hud');
        if (oldHud) oldHud.remove();
        document.querySelectorAll('.flying-bee').forEach(el => el.remove());

        if (document.getElementById('ttg-checkout-modal')) return;

        const modal = document.createElement('div');
        modal.id = 'ttg-checkout-modal';
        modal.innerHTML = `
            <div class="ttg-checkout-drawer" role="dialog" aria-modal="true" aria-labelledby="ttg-modal-title">
                <div class="ttg-checkout-header">
                    <div>
                        <div class="ttg-checkout-title" id="ttg-modal-title">Giỏ hàng của bạn.</div>
                        <div class="ttg-checkout-subtitle">Giao dịch khóa dòng ACID (SELECT ... FOR UPDATE) • Miễn phí vận chuyển</div>
                    </div>
                    <button type="button" class="ttg-checkout-close" id="ttg-checkout-close-btn" aria-label="Đóng">✕</button>
                </div>

                <div class="ttg-checkout-body">
                    <div>
                        <div class="ttg-section-label">
                            <span>Sản phẩm trong Giỏ (<span id="ttg-modal-item-count">0</span>)</span>
                            <button type="button" id="ttg-add-sample-btn" style="border:none;background:none;color:#0066cc;font-size:12px;font-weight:600;cursor:pointer;">+ Thêm nhanh PC Flagship</button>
                        </div>
                        <div class="ttg-cart-list" id="ttg-cart-items-container"></div>
                    </div>

                    <div>
                        <div class="ttg-section-label">
                            <span>Mã ưu đãi Apple / TTG Store</span>
                            <span style="font-size:11.5px;color:#1d8348;font-weight:600;">Chọn nhanh bên dưới</span>
                        </div>
                        <div class="ttg-promo-chips">
                            <button type="button" class="ttg-promo-chip active" data-promo="APPLE2026">APPLE2026 (-1.500.000đ)</button>
                            <button type="button" class="ttg-promo-chip" data-promo="UTH2026">UTH2026 (-1.000.000đ)</button>
                            <button type="button" class="ttg-promo-chip" data-promo="TTG500K">TTG500K (-500.000đ)</button>
                        </div>
                        <div class="ttg-promo-box">
                            <input type="text" id="ttg-promo-input" class="ttg-promo-input" placeholder="Nhập mã ưu đãi (VD: APPLE2026)" value="APPLE2026">
                            <button type="button" id="ttg-promo-apply-btn" class="ttg-promo-btn">Áp dụng</button>
                        </div>
                    </div>

                    <div class="ttg-summary-card">
                        <div class="ttg-summary-row">
                            <span>Tạm tính (<span id="ttg-sum-qty">0</span> sản phẩm)</span>
                            <strong id="ttg-sum-subtotal" class="ttg-sum-val">0 VNĐ</strong>
                        </div>
                        <div class="ttg-summary-row discount">
                            <span>Ưu đãi (<span id="ttg-sum-code">APPLE2026</span>)</span>
                            <span id="ttg-sum-discount" class="ttg-sum-val">-0 VNĐ</span>
                        </div>
                        <div class="ttg-summary-row">
                            <span>Vận chuyển &amp; Lắp đặt Studio</span>
                            <span style="color:#1d8348;font-weight:600;">Miễn phí</span>
                        </div>
                        <div class="ttg-summary-row total">
                            <span>Tổng thanh toán</span>
                            <strong id="ttg-sum-total" class="ttg-sum-val" style="color:#0071e3;">0 VNĐ</strong>
                        </div>
                    </div>

                    <div>
                        <div class="ttg-section-label">
                            <span>Thông tin giao nhận &amp; Thanh toán</span>
                        </div>
                        <div class="ttg-form-grid">
                            <div class="ttg-form-row-2">
                                <div class="ttg-field">
                                    <label for="ttg-cust-name">Họ và tên người nhận</label>
                                    <input type="text" id="ttg-cust-name" value="Nguyễn Văn An (UTH Demo)" placeholder="Nhập họ và tên..." required>
                                </div>
                                <div class="ttg-field">
                                    <label for="ttg-cust-phone">Số điện thoại</label>
                                    <input type="tel" id="ttg-cust-phone" value="0909123456" placeholder="Số điện thoại..." required>
                                </div>
                            </div>
                            <div class="ttg-field">
                                <label for="ttg-cust-address">Địa chỉ nhận máy</label>
                                <input type="text" id="ttg-cust-address" value="Số 2 Võ Oanh, Phường 25, Quận Bình Thạnh, TP.HCM" placeholder="Địa chỉ nhận hàng..." required>
                            </div>
                            <div class="ttg-field">
                                <label for="ttg-cust-payment">Phương thức thanh toán</label>
                                <select id="ttg-cust-payment">
                                    <option value="Apple Pay">Apple Pay (Xác thực Face ID / Touch ID tức thì)</option>
                                    <option value="Chuyển khoản VietQR 24/7">Chuyển khoản VietQR 24/7 (Tự động xác nhận)</option>
                                    <option value="Trả góp 0% qua thẻ tín dụng">Trả góp 0% lãi suất trong 24 tháng</option>
                                    <option value="COD - Thanh toán khi nhận máy">COD - Thanh toán khi nhận máy</option>
                                </select>
                                <div class="ttg-vietqr-preview" id="ttg-vietqr-box">
                                    <div>
                                        <div style="font-weight:700;color:#0071e3;">Quét mã VietQR 24/7 Tự Động</div>
                                        <div style="color:#1d1d1f;margin-top:2px;">MB Bank • STK: <strong>0886976868</strong> • Chủ TK: <strong>TTG STUDIO VN</strong></div>
                                    </div>
                                    <span style="background:#0071e3;color:#fff;padding:4px 10px;border-radius:980px;font-weight:600;font-size:11px;">VietQR Verified</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="ttg-order-receipt" id="ttg-order-receipt"></div>
                </div>

                <div class="ttg-checkout-footer">
                    <button type="button" class="ttg-btn-submit-acid" id="ttg-submit-checkout-btn">
                        Thanh Toán &amp; Đặt Hàng (ACID Lock)
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        document.getElementById('ttg-checkout-close-btn').addEventListener('click', closeCheckoutModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeCheckoutModal();
        });

        document.getElementById('ttg-add-sample-btn').addEventListener('click', () => {
            addItemToCart(6, 'PC TTG GAMING CORE ULTRA 7 270K PLUS - RTX 5070 12GB OC', false);
        });

        document.getElementById('ttg-promo-apply-btn').addEventListener('click', () => {
            applyPromoCodeInput();
        });

        modal.querySelectorAll('.ttg-promo-chip[data-promo]').forEach(chip => {
            chip.addEventListener('click', () => {
                const code = chip.getAttribute('data-promo') || 'APPLE2026';
                const input = document.getElementById('ttg-promo-input');
                if (input) input.value = code;
                modal.querySelectorAll('.ttg-promo-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                applyPromoCodeInput();
            });
        });

        const paymentSelect = document.getElementById('ttg-cust-payment');
        const vietqrBox = document.getElementById('ttg-vietqr-box');
        paymentSelect.addEventListener('change', () => {
            const isVietQR = paymentSelect.value.includes('VietQR');
            vietqrBox.classList.toggle('active', isVietQR);
        });

        document.getElementById('ttg-submit-checkout-btn').addEventListener('click', submitAcidCheckout);
    }

    function applyPromoCodeInput() {
        const input = document.getElementById('ttg-promo-input');
        if (!input) return;
        const code = input.value.trim().toUpperCase();
        cartState.promoCode = code;
        document.querySelectorAll('.ttg-promo-chip[data-promo]').forEach(c => {
            c.classList.toggle('active', c.getAttribute('data-promo') === code);
        });
        const disc = recomputeDiscount();
        renderCheckoutModalCart();
        if (disc > 0) {
            window.showToast('Đã áp dụng mã ưu đãi ' + code, 'Bạn được giảm trực tiếp ' + formatVND(disc));
        } else if (code) {
            window.showToast('Mã ưu đãi không hợp lệ', 'Thử mã APPLE2026 (-1.5tr), UTH2026 (-1tr) hoặc TTG500K (-500k)');
        }
    }

    function renderCheckoutModalCart() {
        const listEl = document.getElementById('ttg-cart-items-container');
        if (!listEl) return;

        const totalQty = getTotalCartCount();
        const subtotal = getCartSubtotal();
        const discount = recomputeDiscount();
        const finalTotal = Math.max(0, subtotal - discount);

        const countEl = document.getElementById('ttg-modal-item-count');
        const sumQtyEl = document.getElementById('ttg-sum-qty');
        const sumSubEl = document.getElementById('ttg-sum-subtotal');
        const sumCodeEl = document.getElementById('ttg-sum-code');
        const sumDiscEl = document.getElementById('ttg-sum-discount');
        const sumTotalEl = document.getElementById('ttg-sum-total');
        const submitBtn = document.getElementById('ttg-submit-checkout-btn');

        if (countEl) countEl.innerText = String(totalQty);
        if (sumQtyEl) sumQtyEl.innerText = String(totalQty);
        if (sumSubEl) sumSubEl.innerText = formatVND(subtotal);
        if (sumCodeEl) sumCodeEl.innerText = discount > 0 ? escapeHtml(cartState.promoCode.toUpperCase()) : 'Chưa áp dụng';
        if (sumDiscEl) sumDiscEl.innerText = '-' + formatVND(discount);
        if (sumTotalEl) sumTotalEl.innerText = formatVND(finalTotal);
        if (submitBtn) submitBtn.disabled = cartState.items.length === 0;

        if (cartState.items.length === 0) {
            listEl.innerHTML = `
                <div class="ttg-cart-empty">
                    Giỏ hàng của bạn đang trống.<br>
                    Hãy bấm <strong>"Mua"</strong> trên cấu hình yêu thích hoặc chọn <strong>"+ Thêm nhanh PC Flagship"</strong>.
                </div>
            `;
            return;
        }

        listEl.innerHTML = cartState.items.map(item => `
            <div class="ttg-cart-item" data-product-id="${escapeHtml(item.id)}">
                <img class="ttg-cart-thumb" src="${escapeHtml(item.image_url)}" alt="${escapeHtml(item.name)}">
                <div class="ttg-cart-info">
                    <div class="ttg-cart-name">${escapeHtml(item.name)}</div>
                    <div class="ttg-cart-price">${formatVND(item.price)} <span style="color:#86868b;font-weight:400;font-size:11px;">(Kho: ${escapeHtml(item.stock)})</span></div>
                </div>
                <div class="ttg-qty-controls">
                    <button type="button" class="ttg-qty-btn" data-action="dec" data-id="${escapeHtml(item.id)}" aria-label="Giảm số lượng">−</button>
                    <span class="ttg-qty-val">${escapeHtml(item.quantity)}</span>
                    <button type="button" class="ttg-qty-btn" data-action="inc" data-id="${escapeHtml(item.id)}" aria-label="Tăng số lượng">+</button>
                    <button type="button" class="ttg-remove-btn" data-action="remove" data-id="${escapeHtml(item.id)}" title="Xóa khỏi giỏ">✕</button>
                </div>
            </div>
        `).join('');

        listEl.querySelectorAll('button[data-action]').forEach(btn => {
            btn.addEventListener('click', () => {
                const pid = Number(btn.getAttribute('data-id'));
                const act = btn.getAttribute('data-action');
                updateCartItemQuantity(pid, act);
            });
        });
    }

    function updateCartItemQuantity(productId, action) {
        const idx = cartState.items.findIndex(i => i.id === productId);
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
        renderCheckoutModalCart();
    }

    function addItemToCart(productId, productName, openDrawerAfter = true) {
        const meta = findProductMeta(productId, productName);
        const existing = cartState.items.find(i => i.id === meta.id);
        if (existing) {
            existing.quantity = Math.min(20, existing.quantity + 1);
            existing.price = meta.price;
            existing.stock = meta.stock;
        } else {
            cartState.items.push({
                id: meta.id,
                name: meta.name,
                price: meta.price,
                image_url: meta.image_url,
                stock: meta.stock,
                quantity: 1
            });
        }

        if (!cartState.promoCode) {
            const promoInput = document.getElementById('ttg-promo-input');
            if (promoInput && promoInput.value.trim()) {
                cartState.promoCode = promoInput.value.trim().toUpperCase();
            }
        }

        syncHeaderCartBadge();
        renderCheckoutModalCart();

        window.showToast(
            'Đã thêm vào Giỏ hàng',
            `${meta.name} • ${formatVND(meta.price)}`
        );

        if (openDrawerAfter) {
            openCheckoutModal();
        }
    }

    function openCheckoutModal() {
        initCheckoutModal();
        const modal = document.getElementById('ttg-checkout-modal');
        if (!modal) return;
        renderCheckoutModalCart();
        modal.classList.add('open');
    }

    function closeCheckoutModal() {
        const modal = document.getElementById('ttg-checkout-modal');
        if (modal) modal.classList.remove('open');
    }

    async function submitAcidCheckout() {
        if (cartState.items.length === 0) return;

        const nameInput = document.getElementById('ttg-cust-name');
        const phoneInput = document.getElementById('ttg-cust-phone');
        const addressInput = document.getElementById('ttg-cust-address');
        const paymentSelect = document.getElementById('ttg-cust-payment');
        const promoInput = document.getElementById('ttg-promo-input');
        const submitBtn = document.getElementById('ttg-submit-checkout-btn');
        const receiptBox = document.getElementById('ttg-order-receipt');

        const customerName = (nameInput ? nameInput.value.trim() : '') || 'Khách hàng Apple / TTG Studio';
        const phone = (phoneInput ? phoneInput.value.trim() : '') || '0909123456';
        const address = (addressInput ? addressInput.value.trim() : '') || 'TP. Hồ Chí Minh';
        const paymentMethod = (paymentSelect ? paymentSelect.value : '') || 'Apple Pay';
        const promoCode = (promoInput ? promoInput.value.trim().toUpperCase() : '') || cartState.promoCode || '';

        submitBtn.disabled = true;
        submitBtn.innerText = 'Đang khóa dòng ACID & Xác nhận đơn hàng...';

        try {
            const checkoutPayload = {
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
                body: JSON.stringify(checkoutPayload)
            });

            if (!res.ok) {
                const errJson = await res.json().catch(() => ({}));
                throw new Error(errJson.detail || 'Giao dịch bị từ chối để bảo vệ tồn kho ACID');
            }

            const data = await res.json();
            const firstOrderId = Array.isArray(data.order_ids) && data.order_ids.length > 0
                ? data.order_ids.join(', #')
                : (data.order_id || 'MỚI');
            const firstRemainingStock = Array.isArray(data.items_processed) && data.items_processed.length > 0
                ? data.items_processed.map(it => `${it.name || ('SP #' + it.product_id)}: còn ${it.remaining_stock} bộ`).join(' | ')
                : (typeof data.remaining_stock !== 'undefined' ? `Còn ${data.remaining_stock} bộ` : 'Đã trừ kho ACID');

            const receiptData = {
                order_id: firstOrderId,
                served_by: data.served_by || 'app-replica-1 (AZ-a)',
                remaining_stock: firstRemainingStock,
                final_amount: typeof data.final_amount === 'number' ? data.final_amount : Math.max(0, getCartSubtotal() - recomputeDiscount()),
                discount_applied: data.discount_applied || recomputeDiscount(),
                payment_method: data.payment_method || paymentMethod
            };

            const currentNodeEl = document.getElementById('current-node');
            if (currentNodeEl && receiptData.served_by) {
                currentNodeEl.innerText = receiptData.served_by;
            }

            if (receiptBox) {
                receiptBox.classList.add('active');
                receiptBox.innerHTML = `
                    <div class="ttg-receipt-title">
                        ✓ Đặt hàng ACID thành công — Mã đơn #${escapeHtml(receiptData.order_id)}
                    </div>
                    <div style="color:#1d1d1f;">
                        <div>• Khách hàng: <strong>${escapeHtml(customerName)}</strong> (${escapeHtml(phone)})</div>
                        <div>• Địa chỉ: <strong>${escapeHtml(address)}</strong></div>
                        <div>• Thanh toán: <strong>${escapeHtml(receiptData.payment_method)}</strong> • Tổng: <strong style="color:#0071e3;">${formatVND(receiptData.final_amount)}</strong></div>
                        <div>• Node xử lý: <strong>${escapeHtml(receiptData.served_by)}</strong> (SELECT ... FOR UPDATE)</div>
                        <div>• Tồn kho sau giao dịch: <strong>${escapeHtml(receiptData.remaining_stock)}</strong></div>
                    </div>
                `;
            }

            window.showToast(
                `Đặt hàng thành công (Đơn #${receiptData.order_id})`,
                `Tổng: ${formatVND(receiptData.final_amount)} • Node: [${receiptData.served_by}]`
            );

            cartState.items = [];
            syncHeaderCartBadge();
            renderCheckoutModalCart();
            window.loadProducts();
            loadLineupComparison();
        } catch (err) {
            const msg = err && err.message ? err.message : String(err);
            window.showToast('Giao dịch ACID Rollback', msg);
        } finally {
            submitBtn.disabled = cartState.items.length === 0;
            submitBtn.innerText = 'Thanh Toán & Đặt Hàng (ACID Lock)';
        }
    }

    window.buyProduct = function (productId, name) {
        const receiptBox = document.getElementById('ttg-order-receipt');
        if (receiptBox) receiptBox.classList.remove('active');
        addItemToCart(productId, name, true);
    };

    window.showCartSummary = function () {
        openCheckoutModal();
    };

    window.openPromoBag = function () {
        if (cartState.items.length === 0) {
            addItemToCart(6, 'PC TTG GAMING CORE ULTRA 7 270K PLUS - RTX 5070 12GB OC', true);
        } else {
            openCheckoutModal();
        }
    };

    /* ----------------------------------------------------------------------
       9. BOOTSTRAP ON DOM READY
       ---------------------------------------------------------------------- */
    function bootAppleStore() {
        initCheckoutModal();
        ensureQuickSpecModal();
        window.loadProducts();
        loadLineupComparison();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootAppleStore);
    } else {
        bootAppleStore();
    }
})();
