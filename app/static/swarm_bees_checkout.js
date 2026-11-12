/* ==========================================================================
   TTGShop — Interactive Cart Drawer & ACID Checkout Modal
   ========================================================================== */

(function () {
    'use strict';

    function escapeHtml(raw) {
        if (raw === null || raw === undefined) return '';
        return String(raw)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function fmtVND(amount) {
        const num = Number(amount) || 0;
        return num.toLocaleString('vi-VN') + ' VNĐ';
    }

    const PROMO_CODES = {
        'TTG500K': 500000,
        'UTH2026': 1000000
    };

    const cartState = {
        items: [],
        promoCode: '',
        discountAmount: 0
    };

    window.ttgCartState = cartState;

    function findProductMeta(productId, fallbackName) {
        const pid = Number(productId) || 1;
        if (typeof currentItems !== 'undefined' && Array.isArray(currentItems)) {
            const found = currentItems.find(item => Number(item.id) === pid);
            if (found) {
                return {
                    id: pid,
                    name: found.name || fallbackName || ('Cấu hình PC #' + pid),
                    price: Number(found.price) || 25480000,
                    image_url: found.image_url || `/static/ttg_assets/pc_${((pid - 1) % 8) + 1}.png`,
                    stock: typeof found.stock === 'number' ? found.stock : 100
                };
            }
        }
        return {
            id: pid,
            name: fallbackName || ('Cấu hình PC TTG #' + pid),
            price: 25480000,
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
        if (typeof window.cartCount !== 'undefined') {
            window.cartCount = total;
        }
        const badge = document.getElementById('cart-badge');
        if (badge) {
            badge.innerText = String(total);
            badge.style.transform = 'scale(1.28)';
            setTimeout(() => {
                badge.style.transition = 'transform 0.25s cubic-bezier(0.16, 1, 0.3, 1)';
                badge.style.transform = 'scale(1)';
            }, 180);
        }
    }

    function initCheckoutModal() {
        // Remove any lingering bee/HUD elements if present
        const oldHud = document.getElementById('swarm-hud');
        if (oldHud) oldHud.remove();
        document.querySelectorAll('.flying-bee').forEach(el => el.remove());

        if (document.getElementById('ttg-checkout-modal')) return;

        const modal = document.createElement('div');
        modal.id = 'ttg-checkout-modal';
        modal.innerHTML = `
            <div class="ttg-checkout-drawer" role="dialog" aria-modal="true" aria-labelledby="ttg-modal-title">
                <div class="ttg-checkout-header">
                    <div class="ttg-checkout-header-left">
                        <div>
                            <div class="ttg-checkout-title" id="ttg-modal-title">🛒 Giỏ Hàng &amp; Thanh Toán ACID</div>
                            <div class="ttg-checkout-subtitle">TTGShop High-Availability • Chống bán âm kho (SELECT ... FOR UPDATE)</div>
                        </div>
                    </div>
                    <button type="button" class="ttg-checkout-close" id="ttg-checkout-close-btn" aria-label="Đóng">✕</button>
                </div>

                <div class="ttg-checkout-body">
                    <div>
                        <div class="ttg-section-label">
                            <span>1. Cấu hình PC đã chọn (<span id="ttg-modal-item-count">0</span>)</span>
                            <button type="button" id="ttg-add-sample-btn" style="border:none;background:none;color:#0284c7;font-size:11.5px;font-weight:700;cursor:pointer;">+ Thêm nhanh PC Flagship</button>
                        </div>
                        <div class="ttg-cart-list" id="ttg-cart-items-container"></div>
                    </div>

                    <div>
                        <div class="ttg-section-label">
                            <span>2. Mã giảm giá ưu đãi</span>
                            <span style="font-size:11px;color:#059669;font-weight:700;">Gợi ý: TTG500K (-500.000đ)</span>
                        </div>
                        <div class="ttg-promo-box">
                            <input type="text" id="ttg-promo-input" class="ttg-promo-input" placeholder="Nhập mã giảm giá (VD: TTG500K)" value="TTG500K">
                            <button type="button" id="ttg-promo-apply-btn" class="ttg-promo-btn">Áp dụng</button>
                        </div>
                    </div>

                    <div class="ttg-summary-card">
                        <div class="ttg-summary-row">
                            <span>Tạm tính (<span id="ttg-sum-qty">0</span> sản phẩm):</span>
                            <strong id="ttg-sum-subtotal">0 VNĐ</strong>
                        </div>
                        <div class="ttg-summary-row discount">
                            <span>Giảm giá khuyến mãi (<span id="ttg-sum-code">Chưa áp dụng</span>):</span>
                            <span id="ttg-sum-discount">-0 VNĐ</span>
                        </div>
                        <div class="ttg-summary-row total">
                            <span>Tổng thanh toán:</span>
                            <strong id="ttg-sum-total">0 VNĐ</strong>
                        </div>
                    </div>

                    <div>
                        <div class="ttg-section-label">
                            <span>3. Thông tin người nhận &amp; Thanh toán</span>
                        </div>
                        <div class="ttg-form-grid">
                            <div class="ttg-form-row-2">
                                <div class="ttg-field">
                                    <label for="ttg-cust-name">Họ và tên người nhận *</label>
                                    <input type="text" id="ttg-cust-name" value="Nguyễn Văn An (UTH Demo)" placeholder="Nhập họ và tên..." required>
                                </div>
                                <div class="ttg-field">
                                    <label for="ttg-cust-phone">Số điện thoại *</label>
                                    <input type="tel" id="ttg-cust-phone" value="0909123456" placeholder="Số điện thoại liên hệ..." required>
                                </div>
                            </div>
                            <div class="ttg-field">
                                <label for="ttg-cust-address">Địa chỉ giao hàng tận nơi *</label>
                                <input type="text" id="ttg-cust-address" value="Số 2 Võ Oanh, Phường 25, Quận Bình Thạnh, TP.HCM" placeholder="Số nhà, tên đường, phường/xã, quận/huyện..." required>
                            </div>
                            <div class="ttg-field">
                                <label for="ttg-cust-payment">Phương thức thanh toán *</label>
                                <select id="ttg-cust-payment">
                                    <option value="COD - Thanh toán khi nhận máy">COD - Thanh toán khi nhận máy</option>
                                    <option value="Chuyển khoản VietQR 24/7">Chuyển khoản VietQR 24/7</option>
                                    <option value="Trả góp 0% qua thẻ tín dụng">Trả góp 0% qua thẻ tín dụng</option>
                                </select>
                                <div class="ttg-vietqr-preview" id="ttg-vietqr-box">
                                    <div>
                                        <div style="font-weight:800;color:#1e40af;">🏦 Quét mã VietQR 24/7 Tự Động</div>
                                        <div>Ngân hàng MB Bank • STK: <strong>0886976868</strong> • Chủ TK: <strong>TTGSHOP PC GAMING</strong></div>
                                    </div>
                                    <span style="background:#1d4ed8;color:#fff;padding:4px 8px;border-radius:6px;font-weight:800;font-size:10.5px;">VietQR Verified</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="ttg-order-receipt" id="ttg-order-receipt"></div>
                </div>

                <div class="ttg-checkout-footer">
                    <button type="button" class="ttg-btn-submit-acid" id="ttg-submit-checkout-btn">
                        ⚡ XÁC NHẬN ĐẶT HÀNG (GIAO DỊCH ACID)
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
            addItemToCart(1, 'PC TTG AMD Ryzen 5 5500 - RTX 5050 8GB OC', false);
        });

        document.getElementById('ttg-promo-apply-btn').addEventListener('click', () => {
            applyPromoCodeInput();
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
        const disc = recomputeDiscount();
        renderCheckoutModalCart();
        if (disc > 0 && typeof showToast === 'function') {
            showToast('Áp dụng mã giảm giá thành công!', `Mã ${escapeHtml(code)} giúp bạn tiết kiệm ${fmtVND(disc)}.`);
        } else if (code && disc === 0 && typeof showToast === 'function') {
            showToast('Mã giảm giá không hợp lệ', 'Vui lòng thử mã TTG500K (-500.000đ) hoặc UTH2026 (-1.000.000đ).');
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
        if (sumSubEl) sumSubEl.innerText = fmtVND(subtotal);
        if (sumCodeEl) sumCodeEl.innerText = discount > 0 ? escapeHtml(cartState.promoCode.toUpperCase()) : 'Không có';
        if (sumDiscEl) sumDiscEl.innerText = '-' + fmtVND(discount);
        if (sumTotalEl) sumTotalEl.innerText = fmtVND(finalTotal);
        if (submitBtn) submitBtn.disabled = cartState.items.length === 0;

        if (cartState.items.length === 0) {
            listEl.innerHTML = `
                <div class="ttg-cart-empty">
                    Giỏ hàng của bạn đang trống. Hãy chọn <strong>"THÊM VÀO GIỎ"</strong> trên bất kỳ cấu hình PC nào hoặc bấm <strong>"+ Thêm nhanh PC Flagship"</strong> ở trên!
                </div>
            `;
            return;
        }

        listEl.innerHTML = cartState.items.map(item => `
            <div class="ttg-cart-item" data-product-id="${escapeHtml(item.id)}">
                <img class="ttg-cart-thumb" src="${escapeHtml(item.image_url)}" alt="${escapeHtml(item.name)}">
                <div class="ttg-cart-info">
                    <div class="ttg-cart-name">${escapeHtml(item.name)}</div>
                    <div class="ttg-cart-price">${fmtVND(item.price)} <span style="color:#64748b;font-weight:500;font-size:11px;">(Kho: ${escapeHtml(item.stock)})</span></div>
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

        if (typeof showToast === 'function') {
            showToast(
                '🛒 Đã thêm cấu hình vào Giỏ hàng!',
                `${escapeHtml(meta.name)} • Giá: ${fmtVND(meta.price)}`
            );
        }

        if (openDrawerAfter) {
            openCheckoutModal();
        }
    }

    function openCheckoutModal() {
        initCheckoutModal();
        const modal = document.getElementById('ttg-checkout-modal');
        if (!modal) return;

        const promoInput = document.getElementById('ttg-promo-input');
        if (promoInput && promoInput.value.trim() && !cartState.promoCode) {
            cartState.promoCode = promoInput.value.trim().toUpperCase();
        }

        renderCheckoutModalCart();
        modal.classList.add('open');
    }

    function closeCheckoutModal() {
        const modal = document.getElementById('ttg-checkout-modal');
        if (modal) {
            modal.classList.remove('open');
        }
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

        const customerName = (nameInput ? nameInput.value.trim() : '') || 'Khách hàng TTGShop';
        const phone = (phoneInput ? phoneInput.value.trim() : '') || '0909123456';
        const address = (addressInput ? addressInput.value.trim() : '') || 'TP. Hồ Chí Minh';
        const paymentMethod = (paymentSelect ? paymentSelect.value : '') || 'COD - Thanh toán khi nhận máy';
        const promoCode = (promoInput ? promoInput.value.trim().toUpperCase() : '') || cartState.promoCode || '';

        submitBtn.disabled = true;
        submitBtn.innerText = '⏳ ĐANG THỰC THI GIAO DỊCH ACID TRÊN CLUSTER...';

        try {
            let receiptData = null;

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

            if (res.ok) {
                const data = await res.json();
                const firstOrderId = Array.isArray(data.order_ids) && data.order_ids.length > 0
                    ? data.order_ids.join(', #')
                    : (data.order_id || 'MỚI');
                const firstRemainingStock = Array.isArray(data.items_processed) && data.items_processed.length > 0
                    ? data.items_processed.map(it => `${it.name || ('SP #' + it.product_id)}: còn ${it.remaining_stock} bộ`).join(' | ')
                    : (typeof data.remaining_stock !== 'undefined' ? `Còn ${data.remaining_stock} bộ` : 'Đã trừ kho ACID');

                receiptData = {
                    order_id: firstOrderId,
                    served_by: data.served_by || 'app-replica-1 (AZ-a)',
                    remaining_stock: firstRemainingStock,
                    final_amount: typeof data.final_amount === 'number' ? data.final_amount : Math.max(0, getCartSubtotal() - recomputeDiscount()),
                    discount_applied: data.discount_applied || recomputeDiscount(),
                    payment_method: data.payment_method || paymentMethod
                };
            } else {
                const errJson = await res.json().catch(() => ({}));
                throw new Error(errJson.detail || 'Giao dịch bị từ chối để bảo vệ tồn kho ACID');
            }

            const currentNodeEl = document.getElementById('current-node');
            if (currentNodeEl && receiptData.served_by) {
                currentNodeEl.innerText = receiptData.served_by;
            }

            if (receiptBox) {
                receiptBox.classList.add('active');
                receiptBox.innerHTML = `
                    <div class="ttg-receipt-title">
                        <span>✅ ĐẶT HÀNG ACID THÀNH CÔNG — MÃ ĐƠN #${escapeHtml(receiptData.order_id)}</span>
                    </div>
                    <div class="ttg-receipt-meta">
                        <div>• Khách hàng: <strong>${escapeHtml(customerName)}</strong> (${escapeHtml(phone)})</div>
                        <div>• Địa chỉ nhận: <strong>${escapeHtml(address)}</strong></div>
                        <div>• Thanh toán: <strong>${escapeHtml(receiptData.payment_method)}</strong> • Tổng tiền: <strong style="color:#e11d48;">${fmtVND(receiptData.final_amount)}</strong></div>
                        <div>• Node xử lý: <strong style="color:#0284c7;">${escapeHtml(receiptData.served_by)}</strong></div>
                        <div>• Tồn kho sau giao dịch: <strong>${escapeHtml(receiptData.remaining_stock)}</strong></div>
                    </div>
                `;
            }

            if (typeof showToast === 'function') {
                showToast(
                    `🎉 Đặt hàng thành công (Đơn #${escapeHtml(receiptData.order_id)})`,
                    `Tổng: ${fmtVND(receiptData.final_amount)} • Node: [${escapeHtml(receiptData.served_by)}] • Tồn kho: ${escapeHtml(receiptData.remaining_stock)}`
                );
            }

            cartState.items = [];
            syncHeaderCartBadge();
            renderCheckoutModalCart();

            if (typeof loadProducts === 'function') {
                loadProducts();
            }
        } catch (err) {
            const msg = err && err.message ? err.message : String(err);
            if (typeof showToast === 'function') {
                showToast('❌ Giao dịch ACID Rollback', escapeHtml(msg));
            } else {
                alert('Lỗi đặt hàng: ' + msg);
            }
        } finally {
            submitBtn.disabled = cartState.items.length === 0;
            submitBtn.innerText = '⚡ XÁC NHẬN ĐẶT HÀNG (GIAO DỊCH ACID)';
        }
    }

    function installCartOverrides() {
        window.buyProduct = function (productId, name) {
            const receiptBox = document.getElementById('ttg-order-receipt');
            if (receiptBox) {
                receiptBox.classList.remove('active');
            }
            addItemToCart(productId, name, true);
        };

        window.showCartSummary = function () {
            openCheckoutModal();
        };
    }

    function bootCartFrontend() {
        initCheckoutModal();
        installCartOverrides();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootCartFrontend);
    } else {
        bootCartFrontend();
    }
})();
