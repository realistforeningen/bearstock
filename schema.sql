-- All prices are in 1/100 NOK

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

-- This contains the full prices at a single point in time.
-- `data` is a JSON dictionary from code -> price adjustments.
-- Note that it's an *adjustment* from the base price.
CREATE TABLE IF NOT EXISTS prices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data BLOB NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  buyer_id INTEGER NOT NULL REFERENCES buyers(id),

  product_code TEXT NOT NULL REFERENCES products(code),
  price_id INTEGER NOT NULL REFERENCES prices(id),

  -- How much the stock won/lost. Computed using:
  -- price[product]
  relative_cost INTEGER NOT NULL,

  -- How much the buyer must pay. Computed using:
  -- price.base_price + price[product]
  absolute_cost INTEGER NOT NULL,

  created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);
