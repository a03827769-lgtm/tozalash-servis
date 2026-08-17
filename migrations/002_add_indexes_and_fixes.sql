-- Indexes for performance
-- Note: Bu migratsiya migrations_runner tomonidan boshqariladi.
-- Index allaqachon mavjud bo'lsa, xato e'tiborga olinmaydi (runner tomonidan handle qilinadi).
CREATE INDEX idx_clients_telegram_id ON clients(telegram_id);
CREATE INDEX idx_orders_client_id ON orders(client_id);
CREATE INDEX idx_orders_client_telegram_id ON orders(client_telegram_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_workers_telegram_id ON workers(telegram_id);
CREATE INDEX idx_finance_order_id ON finance(order_id);
CREATE INDEX idx_finance_date ON finance(`date`);
CREATE INDEX idx_conversations_telegram_id ON conversations(telegram_id);
