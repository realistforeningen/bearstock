
-- table of buyers
CREATE TABLE IF NOT EXISTS buyers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    scaling REAL NOT NULL,
    icon TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

-- table of products
-- code refers to a short "stock-like" code identifying the product
CREATE TABLE IF NOT EXISTS products (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    producer TEXT NOT NULL,
    -- NOTE: base_price is multiple of 1 NOK
    base_price INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    type TEXT NOT NULL,
    tags TEXT NOT NULL,
    hidden BOOLEAN NOT NULL DEFAULT 0
);

-- this table contains parameters for the price computations
-- parameters are stored as a JSON dictionary
CREATE TABLE IF NOT EXISTS parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    data BLOB NOT NULL
);

-- table of orders
-- the relative_cos column store the price relative to the base_price of the product
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id INTEGER NOT NULL REFERENCES buyers(id),
    product_code TEXT NOT NULL REFERENCES products(code),
    -- NOTE: base_price is multiple of 1 NOK
    relative_cost INTEGER NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

-- table of ticks
-- price adjustments contain the adjustments relative to the product base price
CREATE TABLE IF NOT EXISTS ticks (
    tick_no INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    -- NOTE: adjustments are stored in 1/100 NOK
    price_adjustments BLOB NOT NULL
);

