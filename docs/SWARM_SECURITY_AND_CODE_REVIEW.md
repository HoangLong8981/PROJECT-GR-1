# 🛍️ Báo Cáo Thẩm Định An Toàn Mã Nguồn, Bảo Mật & Kiểm Chứng Tải 500 Request (Shopee Vietnam Edition — Antigravity Swarm Review)

- **Đề tài:** Đề tài 1 — Xây dựng Hệ Thống Web Thương Mại Điện Tử Shopee Mall Vietnam / PC Gaming theo chuẩn AWS/Cloud Well-Architected Framework (V2)
- **Đơn vị thực hiện:** Tổ hợp 4 Agent chuyên biệt (**Antigravity Native Swarm**)
- **Tác giả báo cáo:** Worker 4 (`@shopee-reviewer` — 🛡️ **Security & Integration Reviewer**)
- **Ngày hoàn tất kiểm định:** 12/11/2026
- **Trạng thái tổng thể:** ✅ **PASSED (100% ĐẠT CHUẨN GIAO DIỆN SHOPEE VIETNAM, BẢO MẬT OWASP & TOÀN VẸN ACID)**

---

## 1. Tổng Quan Phân Công & Kiến Trúc Swarm (Swarm Architecture Overview)

Hệ thống được chuyển đổi toàn diện sang giao diện chuẩn **Shopee Việt Nam (`shopee.vn`)** và được kiểm định đồng thời bởi 4 Worker Agent độc lập tương tác qua Swarm Message Board:

| Agent ID | Vai trò chuyên trách | Thành phần sở hữu (Deliverables) | Trạng thái |
| :--- | :--- | :--- | :---: |
| 🛍️ **`@shopee-ui`** (Worker 1) | Giao diện Shopee Vietnam Storefront (Header Cam, Thanh tìm kiếm, Flash Sale, Shopee Mall Ribbon, Thẻ sản phẩm & Giỏ hàng Shopee) | `app/shopee_template.py`<br>`app/static/shopee_store.css`<br>`app/static/shopee_store.js` | ✅ Hoàn tất |
| ⚙️ **`@shopee-backend`** (Worker 2) | Multi-Item ACID Checkout API, Shopee Promo Voucher Engine (`SHOPEE2026`, `SHOPEE500K`, `UTH2026`, `TTG500K`), Mall Brands API & Swarm Telemetry | `app/checkout_api.py` (`POST /api/checkout`, `GET /api/shopee/mall-brands`, `GET /api/lineup/compare`, `GET /api/orders/recent`, `GET /api/swarm/telemetry`) | ✅ Hoàn tất |
| ⚡ **`@shopee-qa`** (Worker 3) | Kịch bản kiểm thử tải 500 Concurrent Requests (400 Read + 100 Write ACID) & Bộ kiểm định chống bán âm kho (Zero Overselling) | `tests/swarm_load_test_500.py`<br>`tests/data/swarm_load_test_500_summary.json` | ✅ Hoàn tất |
| 🛡️ **`@shopee-reviewer`** (Worker 4) | Thẩm định bảo mật XSS, SQLi, ACID integrity, tích hợp `app/main.py` & `app/Dockerfile`, đồng bộ `PROJECT-GR-1/app`, kích hoạt server & đo đạc tải thực tế | `app/main.py`, `app/Dockerfile`, `PROJECT-GR-1/app/*`<br>`docs/SWARM_SECURITY_AND_CODE_REVIEW.md` | ✅ Hoàn tất |

---

## 2. Đánh Giá Chi Tiết Mã Nguồn Từng Thành Phần (Code Review)

### 2.1. Thẩm định Giao Diện Shopee Storefront (`@shopee-ui` — `shopee_template.py`, `shopee_store.css`, `shopee_store.js`)
- **Tông màu & Thiết kế Shopee Vietnam chính hãng:**
  - Áp dụng chuẩn dải màu cam Shopee đặc trưng (`#f53d2d` chuyển dần sang `#ff6533`, `#ee4d2d`, `#fb5533`), đỏ Shopee Mall (`#d0011b`), xanh Freeship Xtra (`#26aa99`).
  - **Top Navigation Bar:** Tích hợp đầy đủ *Kênh Người Bán*, *Tải ứng dụng* (với Popover mã QR App Store & Google Play), *Kết nối* (Facebook / Instagram), *Thông Báo* (huy hiệu `9+` với thông báo voucher `SHOPEE2026`), *Hỗ Trợ*, *Tiếng Việt*, và thông tin tài khoản người dùng `vqp5u19dtu`.
  - **Main Header:**
    - Biểu tượng túi xách Shopee màu trắng kèm chữ **Shopee** đậm nét.
    - Thanh tìm kiếm cỡ lớn với menu chọn phạm vi (*Trong Thiết Bị Điện Tử*, *Trong Shopee Mall*, *Trong Toàn Sàn*), ô nhập tìm kiếm và nút kính lúp cam `#fb5533`.
    - Dải từ khóa xu hướng bên dưới: `Rtx 5060`, `Techno Spark 40`, `Techno Spark 50 Pro`, `Váy Không Lót`, `Đèn Led Chân M5`, `Techno Spark 40 Pro Plus`, `Áo Manchester United`.
    - Biểu tượng Giỏ hàng với huy hiệu số lượng động (`#cart-badge`).
    - Nút bảo toàn bảng điều khiển hạ tầng Cloud Well-Architected V2 (`#cloud-drawer`) giúp kiểm thử Load Balancing và Chaos Fault Injection.
  - **Dải thương hiệu SHOPEE MALL Brand Ribbon:**
    - Hiển thị 3 cam kết chuẩn: *Trả Hàng Miễn Phí 15 Ngày*, *Hàng Chính Hãng 100%*, *Miễn Phí Vận Chuyển*.
    - Đối tác thương hiệu: `SAMSUNG`, ` Apple Authorised Reseller`, `oppo`, `ShopDunk`, `coocaa`, `SOUNDMAX`.
  - **Khu vực Flash Sale & Gợi Ý Hôm Nay:**
    - Đồng hồ đếm ngược Flash Sale rực lửa (`[02] : [45] : [18]`).
    - Thẻ sản phẩm chuẩn Shopee: Huy hiệu góc trái `Mall` / `Yêu thích`, nhãn giảm giá vàng góc phải `-18% GIẢM`, nhãn xanh `Freeship Xtra`, giá cam kèm ký hiệu đồng (`₫20.480.000`), số sao đánh giá và số lượng `Đã bán 1.2k`.
  - **Shopee Cart & ACID Checkout Modal (`#shopee-checkout-modal`):**
    - Hỗ trợ chọn nhanh Voucher Shopee: `SHOPEE2026` (-1.500.000₫), `SHOPEE500K` (-500.000₫), `UTH2026` (-1.000.000₫), `TTG500K` (-500.000₫).
    - Hỗ trợ phương thức thanh toán: `Ví ShopeePay`, `Apple Pay`, `Chuyển khoản VietQR 24/7` (MB Bank STK `0886976868`), `COD - Thanh toán khi nhận hàng`.
    - Gửi yêu cầu `POST /api/checkout` và kết xuất biên nhận ACID xác thực node phục vụ (`served_by`) và tồn kho còn lại (`remaining_stock`).

### 2.2. Thẩm định Backend & API Checkout (`@shopee-backend` — `app/checkout_api.py`)
- **Kiến trúc Router độc lập & Tự động kết nối Context:**
  - Module `checkout_api.py` sử dụng `APIRouter()` và hàm `_get_runtime_context` để dùng chung `db_pool` (PostgreSQL), `sqlite_lock` (SQLite), và Prometheus metrics với `app.main`.
- **Cơ chế Khóa dòng ACID & Phòng chống Deadlock:**
  - Nhận diện đơn hàng đa sản phẩm (`items`) hoặc đơn lẻ (`product_id`).
  - Gộp số lượng theo mã sản phẩm (`requested_totals`) nhằm ngăn chặn việc gửi lặp nhiều dòng cùng ID để mua vượt hạn mức tồn kho.
  - **Chống Deadlock:** Sắp xếp `sorted_pids = sorted(requested_totals.keys())` tăng dần trước khi thực thi truy vấn khóa dòng `SELECT id, name, price, stock FROM products WHERE id = %s FOR UPDATE;` (PostgreSQL) hoặc `BEGIN IMMEDIATE;` trong `sqlite_lock` (SQLite).
  - Kiểm tra tồn kho toàn bộ giỏ hàng trước khi trừ kho; nếu có bất kỳ sản phẩm nào không đủ tồn kho, lập tức rollback toàn bộ giao dịch và trả về mã lỗi HTTP 400.
- **Endpoint Thương hiệu Shopee Mall (`GET /api/shopee/mall-brands`):**
  - Cung cấp danh mục các thương hiệu chính hãng, thông tin voucher khuyến mãi, và các phương thức thanh toán được hỗ trợ.
- **Endpoint Telemetry & Nhật ký Swarm (`GET /api/swarm/telemetry`, `GET /api/orders/recent`):**
  - Cung cấp dữ liệu trực quan cho 4 Agent Swarm (`shopee-ui`, `shopee-backend`, `shopee-qa`, `shopee-reviewer`) và lưu vết 30 sự kiện giao dịch gần nhất trong bộ nhớ đệm dạng vòng (`SWARM_TELEMETRY_LOG`).

### 2.3. Thẩm định Kịch Bản Kiểm Thử Tải (`@shopee-qa` — `tests/swarm_load_test_500.py`)
- **Thư viện chuẩn (Zero External Dependencies):**
  - 100% dùng thư viện có sẵn trong Python (`concurrent.futures.ThreadPoolExecutor`, `urllib.request`), chạy được ngay mà không cần cài thêm gói pip.
- **Mô phỏng đợt bùng nổ Flash Sale 500 Requests:**
  - **400 Reads**: `GET /api/products` (120), `GET /api/products/{id}` (100), `GET /api/shopee/mall-brands` (80), `GET /health` (50), `GET /api/orders/recent` (50).
  - **100 Writes ACID**: `POST /api/checkout` với mã giảm giá `SHOPEE2026`, phương thức thanh toán luân phiên giữa `Ví ShopeePay` và `VietQR 24/7` trên 8 cấu hình Flagship PC Gaming.
- **Kiểm định Chống bán âm kho (Zero Overselling Verification):**
  - Đo lường tồn kho trước (`stock_before`) và sau (`stock_after`), kiểm chứng phương trình bảo toàn `stock_before - 100 == stock_after`.
  - Khẳng định `min_stock >= 0` trên toàn bộ danh mục sản phẩm.

---

## 3. Thẩm Định An Toàn Bảo Mật & Logic Giao Dịch (Security & Logic Audit)

### 3.1. Chống Tấn Công XSS (Cross-Site Scripting Sanitization)
- **Tầng SSR Template (`app/shopee_template.py`):**
  - Dòng 27–28: Áp dụng `html.escape(str(node or "..."), quote=True)` và `html.escape(str(arch_version or "..."), quote=True)` trước khi kết xuất mã HTML.
- **Tầng Giao diện Client (`app/static/shopee_store.js`):**
  - Hàm `escapeHtml(raw)` (dòng 11–19) chuyển đổi toàn diện 5 ký tự nguy hiểm (`&`, `<`, `>`, `"`, `'`) thành mã thực thể HTML trước khi render vào DOM (thẻ sản phẩm, giỏ hàng, thông báo Toast, chat bot, và biên nhận đơn hàng).
- **Tầng API Backend (`app/checkout_api.py`):**
  - Hàm `_sanitize_text(val, default, max_len)` (dòng 511–515) chuẩn hóa và áp dụng `html.escape(str(val).strip(), quote=True)` kết hợp cắt giảm độ dài tối đa cho mọi trường do người dùng nhập (`customer_name`, `phone`, `address`, `payment_method`, `promo_code`).

### 3.2. Chống Tấn Công SQL Injection (SQL Parameter Binding)
- Rà soát 100% các câu truy vấn SQL trong `app/main.py` và `app/checkout_api.py`:
  - **PostgreSQL (`psycopg2`):** 100% sử dụng tham số hóa `%s` truyền qua tuple:
    - `cur.execute("SELECT id, name, price, stock FROM products WHERE id = %s FOR UPDATE;", (pid,))`
    - `cur.execute("UPDATE products SET stock = stock - %s WHERE id = %s;", (qty, pid))`
    - `cur.execute("INSERT INTO orders (...) VALUES (%s, %s, %s, %s, %s) ...;", (clean_customer, pid, qty, line_total, node))`
  - **SQLite (`sqlite3`):** 100% sử dụng tham số hóa `?` truyền qua tuple tương ứng.
  - **Kết luận:** Tuyệt đối không có hiện tượng nối chuỗi thô (`f-string` hay phép cộng chuỗi) trong các câu lệnh SQL. Đạt chuẩn bảo mật OWASP Top 10 A03:2021 (Injection).

### 3.3. Tính Toàn Vẹn Giao Dịch ACID & Cơ Chế Rollback
- **Khóa bi quan (Pessimistic Row Locking):**
  - Trên PostgreSQL: Sử dụng `FOR UPDATE` độc quyền trên từng dòng sản phẩm.
  - Trên SQLite: Kết hợp khóa luồng `with sqlite_lock:` và chế độ `BEGIN IMMEDIATE;` đảm bảo chỉ một tiến trình ghi được phép can thiệp vào kho tại một thời điểm.
- **Cơ chế Rollback nguyên khối:**
  - Nếu tồn kho của bất kỳ sản phẩm nào không đủ (`stock < requested_quantity`), gọi ngay lệnh `conn.rollback()` và phát sinh lỗi `HTTP 400 Bad Request` trước khi có bất kỳ dòng dữ liệu nào bị thay đổi.
  - Sau khi cập nhật trừ kho và thêm đơn hàng thành công cho toàn bộ sản phẩm, mới thực hiện `conn.commit()`.

### 3.4. Bảo Mật Container Non-Root (`UID 10001` trong `Dockerfile`)
- Kiểm tra `app/Dockerfile` và bản đồng bộ tại `PROJECT-GR-1/app/Dockerfile`:
  ```dockerfile
  # Sao chép mã nguồn ứng dụng & tài nguyên tĩnh TTGShop / Shopee Mall / Apple Store
  COPY main.py shopee_template.py apple_template.py checkout_api.py ./
  COPY static ./static

  # Trụ cột Security (Well-Architected): Không chạy ứng dụng dưới quyền root (UID 10001)
  RUN groupadd -g 10001 appgroup && \
      useradd -u 10001 -g appgroup -s /bin/sh appuser && \
      chown -R appuser:appgroup /app
  USER appuser
  ```
- **Kết luận:** Đảm bảo nguyên tắc đặc quyền tối thiểu (Principle of Least Privilege), ngăn ngừa nguy cơ thoát container (Container Breakout).

---

## 4. Kết Quả Kiểm Chứng Tích Hợp & Kiểm Thử Tải 500 Concurrent Requests

Sau khi tích hợp `render_shopee_store_html` (`shopee_template.py`) và `checkout_api.router` vào `app/main.py`, cập nhật `Dockerfile`, đồng bộ sang `PROJECT-GR-1/app`, và khởi động lại uvicorn trên cổng 8000, `@shopee-reviewer` đã kích hoạt kịch bản kiểm thử tải thực tế:
`python tests/swarm_load_test_500.py --url http://localhost:8000 --workers 50`

### 4.1. Bảng Tổng Hợp Chỉ Số Hiệu Năng (500 Concurrent Requests Benchmark)

| Chỉ số đo lường (Benchmark Metric) | Giá trị thực nghiệm (Measured) | Đánh giá SLA |
| :--- | :--- | :---: |
| **1. Tổng số Request (Total Requests)** | **500 requests** (400 READ + 100 WRITE ACID) | ✅ Đạt 100% |
| **2. Tỷ lệ thành công (Success Rate %)** | **100.00%** (500/500 request hợp lệ) | ✅ Tuyệt đối |
| **3. Số lỗi máy chủ HTTP 5xx (Server Errors)** | **0 lỗi** (Zero Server Crash) | ✅ Không sập |
| **4. Thời gian hoàn tất (Wall Time)** | **1.547 giây** (50 luồng song song) | ✅ Rất nhanh |
| **5. Thông lượng xử lý (Throughput)** | **323.25 req/s** | ✅ Rất cao |
| **6. Độ trễ trung vị P50 (Median Latency)** | **142.45 ms** | ✅ Cực kỳ mượt |
| **7. Độ trễ phân vị P95 (P95 Latency)** | **213.70 ms** | ✅ Đạt SLA (< 250ms) |
| **8. Độ trễ phân vị P99 (P99 Latency)** | **241.28 ms** (Min: `18.1 ms`, Max: `258.3 ms`) | ✅ Ổn định |
| **9. Phân bổ tải Multi-AZ (Load Balancing)** | `app-replica-1 (AZ-a)`: **246 reqs (49.20%)**<br>`app-replica-2 (AZ-b)`: **254 reqs (50.80%)** | ✅ Cân bằng hoàn hảo 50/50 |

### 4.2. Bảng Kiểm Định Toàn Vẹn Tồn Kho ACID Trên 8 Dòng Flagship PC

| ID | Mã SKU | Tên cấu hình Flagship PC | Tồn đầu (`stock_before`) | Đơn mua (`sold`) | Tồn kỳ vọng | Tồn thực tế (`stock_after`) | Kết luận ACID |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **#1** | `TTG-PC-0001` | PC TTG AMD Ryzen 5 5500 - RTX 5050 8GB OC | 134 | 13 | 121 | **121** | ✅ Khớp 100% |
| **#2** | `TTG-PC-0002` | PC TTG GAMING CORE ULTRA 5 250K PLUS - RTX 5060 | 104 | 13 | 91 | **91** | ✅ Khớp 100% |
| **#3** | `TTG-PC-0003` | PC TTG AMD GAMING PRO Ryzen 7 5700X - RTX 5060 | 121 | 13 | 108 | **108** | ✅ Khớp 100% |
| **#4** | `TTG-PC-0004` | PC TTG AMD GAMING PRO Ryzen 7 5700X - RTX 5050 | 127 | 13 | 114 | **114** | ✅ Khớp 100% |
| **#5** | `TTG-PC-0005` | PC TTG GAMING i5 14600KF - 16GB DDR4 - RTX 5070 | 83 | 12 | 71 | **71** | ✅ Khớp 100% |
| **#6** | `TTG-PC-0006` | PC TTG GAMING CORE ULTRA 7 270K PLUS - RTX 5070 | 67 | 12 | 55 | **55** | ✅ Khớp 100% |
| **#7** | `TTG-PC-0007` | PC TTG ULTRA GAMING I5 14400F - RTX 5050 8GB | 148 | 12 | 136 | **136** | ✅ Khớp 100% |
| **#8** | `TTG-PC-0008` | PC TTG AMD GAMING RYZEN 5 7500X3D - RTX 5060 8GB | 98 | 12 | 86 | **86** | ✅ Khớp 100% |
| **TỔNG** | **8 SKUs** | **Toàn bộ danh mục Flagship PC Gaming** | **882** | **100** | **782** | **782** | ✅ **ZERO OVERSELLING** |

- **Xác thực phương trình bảo toàn:**
  $$\text{stock\_before } (882) - \text{sold } (100) = \text{stock\_after } (782)$$
- **Tồn kho thấp nhất:** `55 >= 0` (**Cam kết Không bán âm kho — Zero Overselling 100%**).
- **Số giao dịch commit thành công:** `100/100` đơn hàng (mỗi đơn áp dụng voucher `SHOPEE2026`).

### 4.3. Chi Tiết Độ Trễ Theo Từng Endpoint

| Endpoint | Phương thức | Số lượng | HTTP 2xx | HTTP 4xx | HTTP 5xx | P50 (ms) | P95 (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `GET /api/orders/recent` | GET | 50 | 50 | 0 | 0 | 143.15 | 177.69 |
| `GET /api/products` | GET | 120 | 120 | 0 | 0 | 144.19 | 198.42 |
| `GET /api/products/{id}` | GET | 100 | 100 | 0 | 0 | 141.21 | 165.31 |
| `GET /api/shopee/mall-brands`| GET | 80 | 80 | 0 | 0 | 137.42 | 157.39 |
| `GET /health` | GET | 50 | 50 | 0 | 0 | 136.30 | 144.45 |
| `POST /api/checkout` | POST | 100 | 100 | 0 | 0 | 177.27 | 239.88 |

---

## 5. Kết Luận & Nghiệm Thu (Final Sign-Off)

Toàn bộ hệ thống giao diện **Shopee Vietnam Storefront (`app/shopee_template.py`, `app/static/shopee_store.css`, `app/static/shopee_store.js`)**, **API Đặt Hàng ACID Shopee Mall (`POST /api/checkout`, `GET /api/shopee/mall-brands`, `GET /api/swarm/telemetry` trong `app/checkout_api.py`)**, và **Kịch Bản Đo Tải 500 Requests (`tests/swarm_load_test_500.py`)** đã được thẩm định bảo mật thành công, tích hợp hoàn chỉnh vào `app/main.py` và `app/Dockerfile` (đồng bộ sang `PROJECT-GR-1/app`), và đang phục vụ trực tiếp tại địa chỉ `http://localhost:8000`.
