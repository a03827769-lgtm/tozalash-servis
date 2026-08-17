-- Task 41: Add FOREIGN KEY constraint to finance.order_id
-- We have to ensure that order_id references orders.id

-- Add constraint (make sure order_id matches the orders table's id type)
ALTER TABLE finance
ADD CONSTRAINT fk_finance_order
FOREIGN KEY (order_id) REFERENCES orders(id)
ON DELETE SET NULL;

-- Task 42: Change context type in user_states to JSON
ALTER TABLE user_states
MODIFY COLUMN context JSON;
