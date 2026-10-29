CREATE TABLE IF NOT EXISTS transactions (
    invoice_no TEXT,
    stock_code TEXT,
    quantity INTEGER,
    invoice_date TIMESTAMP,
    unit_price DOUBLE PRECISION,
    customer_id TEXT,
    country TEXT
);
