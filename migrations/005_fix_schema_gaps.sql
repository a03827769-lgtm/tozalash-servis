-- Migration 005: Fix Schema Gaps, Missing Columns, Missing Tables and Index Optimizations
-- Note: Duplicate column (1060), table already exists (1050), duplicate index (1061) xatolari
-- migrations_runner.py tomonidan xavfsiz ravishda o'tkazib yuboriladi.

-- 1. Add missing columns to clients table (referenced in database.py _CLIENT_UPDATABLE_COLUMNS)
ALTER TABLE clients ADD COLUMN address TEXT DEFAULT NULL;
ALTER TABLE clients ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE;
ALTER TABLE clients ADD COLUMN gender VARCHAR(20) DEFAULT NULL;
ALTER TABLE clients ADD COLUMN notification_enabled BOOLEAN DEFAULT TRUE;

-- 2. Create competitor_prices table (if not created yet) and ensure both detected_at and created_at exist
CREATE TABLE IF NOT EXISTS competitor_prices (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    competitor_name VARCHAR(100) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_url VARCHAR(255)
);

ALTER TABLE competitor_prices ADD COLUMN detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE competitor_prices ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 3. Create missing tables defined in app/models (orders_archive, audit_logs, worker_locations)
CREATE TABLE IF NOT EXISTS orders_archive (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    original_id INTEGER NOT NULL,
    amount DOUBLE,
    status INTEGER,
    client_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_orders_archive_original_id (original_id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NULL,
    action VARCHAR(50) NOT NULL,
    entity_name VARCHAR(100) NOT NULL,
    entity_id INTEGER NOT NULL,
    changes JSON,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_logs_user_id (user_id),
    INDEX idx_audit_logs_entity (entity_name, entity_id)
);

CREATE TABLE IF NOT EXISTS worker_locations (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    worker_id INTEGER NOT NULL,
    name VARCHAR(255),
    lat DOUBLE,
    lon DOUBLE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_worker_locations_worker_id (worker_id)
);

-- 4. Add missing index optimizations
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_city_id ON orders(city_id);
CREATE INDEX idx_workers_active_available ON workers(is_active, is_available, rating);
CREATE INDEX idx_clients_city_id ON clients(city_id);
CREATE INDEX idx_clients_referred_by ON clients(referred_by);
