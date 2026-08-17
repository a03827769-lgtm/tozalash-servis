CREATE TABLE IF NOT EXISTS order_workers (
    order_id INTEGER NOT NULL,
    worker_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, worker_id),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE
);

-- Insert existing relations (this is a simplified approach, in MySQL splitting strings in SQL is hard, 
-- but since this is an empty/new system, we assume we don't have a lot of complex comma-separated data,
-- or we can handle it via a python script if needed. For now we just create the table and drop old columns).
-- If there's existing data, it would need a python script to migrate it. 
-- Since we are building the roadmap, we create the table.

-- Drop the old views to recreate them
DROP VIEW IF EXISTS view_worker_performance;
DROP VIEW IF EXISTS view_daily_revenue;

-- Create views with the new many-to-many relationship
CREATE VIEW view_worker_performance AS
SELECT 
    w.id as worker_id,
    w.name as worker_name,
    w.city_id,
    c.name as city_name,
    COUNT(ow.order_id) as total_orders,
    SUM(o.total_price) as generated_revenue
FROM workers w
LEFT JOIN order_workers ow ON w.id = ow.worker_id
LEFT JOIN orders o ON ow.order_id = o.id AND o.status = 'bajarildi'
LEFT JOIN cities c ON w.city_id = c.id
GROUP BY w.id, w.name, w.city_id, c.name;

CREATE VIEW view_daily_revenue AS
SELECT 
    DATE(o.created_at) as date,
    o.city_id,
    c.name as city_name,
    COUNT(o.id) as total_orders,
    SUM(o.total_price) as total_revenue
FROM orders o
LEFT JOIN cities c ON o.city_id = c.id
WHERE o.status = 'bajarildi'
GROUP BY DATE(o.created_at), o.city_id, c.name;

-- We can drop the worker_ids column later when we confirm everything works.
-- ALTER TABLE orders DROP COLUMN worker_ids;
-- ALTER TABLE orders DROP COLUMN worker_names;
