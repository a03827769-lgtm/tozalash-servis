-- 1. Clients jadvaliga Tozalash Coin (loyallik tizimi) uchun balans qo'shish
ALTER TABLE clients 
ADD COLUMN loyalty_coins DECIMAL(10, 2) DEFAULT 0.00;

-- 2. Worker rating tizimi: Mijozlar tomonidan baholash
CREATE TABLE IF NOT EXISTS worker_ratings (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    worker_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    order_id INTEGER,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL
);

-- 3. Xodimlar jadvalida o'rtacha reytingni kesh qilish
ALTER TABLE workers
ADD COLUMN average_rating DECIMAL(3, 2) DEFAULT 5.00,
ADD COLUMN total_ratings INTEGER DEFAULT 0;

-- 4. Raqobatchilar narxlari tahlilini saqlash jadvali
CREATE TABLE IF NOT EXISTS competitor_prices (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    competitor_name VARCHAR(100) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_url VARCHAR(255)
);
