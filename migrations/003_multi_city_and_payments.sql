-- Migration 003: Ko'p shaharlik tizim va to'lov jadvallar
-- Note: ADD COLUMN IF NOT EXISTS MySQL da yo'q (faqat MariaDB da).
-- Duplikat column xatosi (1060) migrations_runner tomonidan o'tkazib yuboriladi.

CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,
    price_multiplier DOUBLE DEFAULT 1.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO cities (name, price_multiplier) VALUES ('Toshkent', 1.0);
INSERT IGNORE INTO cities (name, price_multiplier) VALUES ('Samarqand', 0.8);
INSERT IGNORE INTO cities (name, price_multiplier) VALUES ('Buxoro', 0.75);

ALTER TABLE clients ADD COLUMN city_id INTEGER DEFAULT 1;
ALTER TABLE workers ADD COLUMN city_id INTEGER DEFAULT 1;
ALTER TABLE orders ADD COLUMN city_id INTEGER DEFAULT 1;
ALTER TABLE orders ADD COLUMN payment_provider VARCHAR(50) DEFAULT NULL;
ALTER TABLE orders ADD COLUMN payment_url TEXT DEFAULT NULL;

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    order_id INTEGER NOT NULL,
    provider VARCHAR(50) NOT NULL,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    amount DOUBLE NOT NULL,
    status VARCHAR(50) DEFAULT 'kutilmoqda',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE OR REPLACE VIEW view_daily_revenue AS
SELECT
    DATE(created_at) as date,
    city_id,
    SUM(total_price) as revenue,
    COUNT(*) as total_orders
FROM orders
WHERE status = 'bajarildi'
GROUP BY DATE(created_at), city_id;

CREATE OR REPLACE VIEW view_worker_performance AS
SELECT
    w.id,
    w.name,
    w.city_id,
    COUNT(o.id) as jobs_completed,
    SUM(o.total_price) as revenue_generated
FROM workers w
LEFT JOIN orders o ON FIND_IN_SET(w.id, o.worker_ids) > 0 AND o.status = 'bajarildi'
GROUP BY w.id, w.name, w.city_id;
