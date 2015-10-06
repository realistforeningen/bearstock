-- All prices are in 1/100 NOK

CREATE TABLE IF NOT EXISTS buyers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS products (
  -- Short stock-like code
  code TEXT PRIMARY KEY,

  -- Name of the beer
  name TEXT NOT NULL,

  -- "Innkjøpspris"
  base_price INTEGER NOT NULL,

  -- How many we have *before* any orders
  quantity INTEGER NOT NULL,

  tags TEXT NOT NULL
);

-- This contains the full prices at a single point in time.
-- `data` is a JSON dictionary from code -> price adjustments.
-- Note that it's an *adjustment* from the base price.
CREATE TABLE IF NOT EXISTS prices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data TEXT NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  buyer_id INTEGER NOT NULL REFERENCES buyers(id),

  product_code TEXT NOT NULL REFERENCES products(code),
  price_id INTEGER NOT NULL REFERENCES prices(id),

  -- How much the buyer must pay. Computed using:
  -- price.base_price + price[product]
  cost INTEGER NOT NULL,

  -- How much the stock won/lost. Computed using:
  -- price[product]
  stock_cost INTEGER NOT NULL,

  created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

