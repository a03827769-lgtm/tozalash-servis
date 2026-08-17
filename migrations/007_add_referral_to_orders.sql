-- Add discount_code and referred_by to orders table
ALTER TABLE orders ADD COLUMN discount_code VARCHAR(50);
ALTER TABLE orders ADD COLUMN referred_by INTEGER;
ALTER TABLE orders ADD CONSTRAINT fk_orders_referred_by FOREIGN KEY (referred_by) REFERENCES clients(id) ON DELETE SET NULL;
