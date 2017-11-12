-- All prices are in 1/100 NOK

CREATE TABLE IF NOT EXISTS buyers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  icon TEXT NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS products (
  -- Short stock-like code
  code TEXT PRIMARY KEY,

  -- Name of the beer
  name TEXT NOT NULL,

  -- Brewery
  brewery TEXT NOT NULL,

  -- Aquisition price
  base_price INTEGER NOT NULL,

  -- How many we have *before* any orders
  quantity INTEGER NOT NULL,

  -- Beer type
  type TEXT NOT NULL,

  -- product tags
  tags TEXT NOT NULL,

  is_hidden BOOLEAN NOT NULL DEFAULT 0
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
