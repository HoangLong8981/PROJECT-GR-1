-- =============================================================================
-- KHỞI TẠO LƯỢC ĐỒ CƠ SỞ DỮ LIỆU & DỮ LIỆU MẪU TTGSHOP (457 SẢN PHẨM PC GAMING)
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

-- 8 Sản phẩm chủ lực hiển thị trang đầu TTGShop
INSERT INTO products (sku, name, category, price, stock, image_key) VALUES
('TTG-PC-0001', 'PC TTG AMD Ryzen 5 5500 - RTX 5050 8GB OC', 'PC GAMING GIÁ RẺ', 20480000, 150, '/static/ttg_assets/pc_1.png'),
('TTG-PC-0002', 'PC TTG GAMING CORE ULTRA 5 250K PLUS - RTX 5060 8GB', 'PC Core Ultra', 38680000, 120, '/static/ttg_assets/pc_2.png'),
('TTG-PC-0003', 'PC TTG AMD GAMING PRO Ryzen 7 5700X - RTX 5060 8GB', 'PC GAMING PREMIUM', 25480000, 135, '/static/ttg_assets/pc_3.png'),
('TTG-PC-0004', 'PC TTG AMD GAMING PRO Ryzen 7 5700X - RTX 5050 8GB OC', 'PC STREAM GAME', 22280000, 140, '/static/ttg_assets/pc_4.png'),
('TTG-PC-0005', 'PC TTG GAMING i5 14600KF - 16GB DDR4 - RTX 5070 12GB', 'PC GAMING CAO CẤP', 44480000, 95, '/static/ttg_assets/pc_5.png'),
('TTG-PC-0006', 'PC TTG GAMING CORE ULTRA 7 270K PLUS - RTX 5070 12GB OC', 'PC Core Ultra', 51680000, 80, '/static/ttg_assets/pc_6.png'),
('TTG-PC-0007', 'PC TTG ULTRA GAMING I5 14400F - RTX 5050 8GB', 'PC STREAM GAME', 22980000, 160, '/static/ttg_assets/pc_7.png'),
('TTG-PC-0008', 'PC TTG AMD GAMING RYZEN 5 7500X3D - RTX 5060 8GB', 'PC ĐẸP', 32280000, 110, '/static/ttg_assets/pc_8.png')
ON CONFLICT (sku) DO UPDATE SET
    name = EXCLUDED.name,
    category = EXCLUDED.category,
    price = EXCLUDED.price,
    image_key = EXCLUDED.image_key;

-- Sinh tự động thêm 449 cấu hình PC (tổng 457 sản phẩm chuẩn TTGShop)
INSERT INTO products (sku, name, category, price, stock, image_key)
SELECT
    'TTG-PC-' || LPAD(i::text, 4, '0'),
    CASE (i % 8)
        WHEN 0 THEN 'PC TTG AMD Ryzen 5 5500 - RTX 5050 8GB OC #' || i
        WHEN 1 THEN 'PC TTG GAMING CORE ULTRA 5 250K PLUS - RTX 5060 #' || i
        WHEN 2 THEN 'PC TTG AMD GAMING PRO Ryzen 7 5700X - RTX 5060 #' || i
        WHEN 3 THEN 'PC TTG AMD GAMING PRO Ryzen 7 5700X - RTX 5050 #' || i
        WHEN 4 THEN 'PC TTG GAMING i5 14600KF - 16GB DDR4 - RTX 5070 #' || i
        WHEN 5 THEN 'PC TTG GAMING CORE ULTRA 7 270K PLUS - RTX 5070 #' || i
        WHEN 6 THEN 'PC TTG ULTRA GAMING I5 14400F - RTX 5050 8GB #' || i
        ELSE 'PC TTG AMD GAMING RYZEN 5 7500X3D - RTX 5060 #' || i
    END,
    CASE (i % 6)
        WHEN 0 THEN 'PC GAMING GIÁ RẺ'
        WHEN 1 THEN 'PC STREAM GAME'
        WHEN 2 THEN 'PC GAMING PREMIUM'
        WHEN 3 THEN 'PC Core Ultra'
        WHEN 4 THEN 'PC GAMING CAO CẤP'
        ELSE 'PC ĐẸP'
    END,
    ROUND((15480000 + (i * 1250000) % 65000000)::numeric, 2),
    200,
    '/static/ttg_assets/pc_' || ((i % 8) + 1) || '.png'
FROM generate_series(9, 457) AS s(i)
ON CONFLICT (sku) DO NOTHING;
