-- =============================================================================
-- KHỞI TẠO LƯỢC ĐỒ CƠ SỞ DỮ LIỆU & DỮ LIỆU MẪU (500 SẢN PHẨM THƯƠNG MẠI ĐIỆN TỬ)
-- =============================================================================

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 100,
    image_key VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    product_id INT NOT NULL REFERENCES products(id),
    quantity INT NOT NULL CHECK (quantity > 0),
    total_amount NUMERIC(12, 2) NOT NULL,
    served_by_node VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- Sinh tự động 500 sản phẩm mẫu nếu bảng đang trống
INSERT INTO products (sku, name, category, price, stock, image_key)
SELECT
    'SKU-CLOUD-' || LPAD(i::text, 4, '0'),
    CASE (i % 5)
        WHEN 0 THEN 'Laptop CloudBook Pro M' || i
        WHEN 1 THEN 'Bàn phím cơ Wireless KeyChron K' || i
        WHEN 2 THEN 'Màn hình đồ họa UltraSharp 4K U' || i
        WHEN 3 THEN 'Tai nghe chống ồn Studio ANC S' || i
        ELSE 'Ổ cứng SSD NVMe Gen4 Enterprise E' || i
    END,
    CASE (i % 5)
        WHEN 0 THEN 'Laptop'
        WHEN 1 THEN 'Phụ kiện'
        WHEN 2 THEN 'Màn hình'
        WHEN 3 THEN 'Âm thanh'
        ELSE 'Lưu trữ'
    END,
    ROUND((500000 + (i * 37000) % 25000000)::numeric, 2),
    5000,
    'products/item-' || ((i % 10) + 1) || '.svg'
FROM generate_series(1, 500) AS s(i)
ON CONFLICT (sku) DO NOTHING;
