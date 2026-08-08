PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS products (
  canonical_sku TEXT PRIMARY KEY,
  metal TEXT NOT NULL,
  mint TEXT,
  product TEXT NOT NULL,
  year_label TEXT,
  fine_weight_oz REAL NOT NULL,
  purity REAL,
  condition TEXT
);
CREATE TABLE IF NOT EXISTS dealers (
  dealer_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  parent TEXT,
  enabled INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS observations (
  observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  observed_at_utc TEXT NOT NULL,
  dealer_id TEXT NOT NULL,
  canonical_sku TEXT NOT NULL,
  side TEXT NOT NULL CHECK(side IN ('ask','bid')),
  price REAL NOT NULL,
  quantity_min REAL,
  quantity_max REAL,
  inventory_status TEXT,
  bid_quality TEXT,
  source_url TEXT NOT NULL,
  raw_title TEXT,
  parser_version TEXT,
  FOREIGN KEY (dealer_id) REFERENCES dealers(dealer_id),
  FOREIGN KEY (canonical_sku) REFERENCES products(canonical_sku)
);
CREATE INDEX IF NOT EXISTS idx_obs_market ON observations(canonical_sku, dealer_id, side, observed_at_utc);
CREATE TABLE IF NOT EXISTS opportunities (
  opportunity_id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_seen_utc TEXT NOT NULL,
  last_seen_utc TEXT NOT NULL,
  canonical_sku TEXT NOT NULL,
  buy_dealer_id TEXT NOT NULL,
  sell_dealer_id TEXT NOT NULL,
  buy_price REAL NOT NULL,
  sell_price REAL NOT NULL,
  gross_spread REAL NOT NULL,
  modeled_cost REAL NOT NULL,
  net_profit_per_unit REAL NOT NULL,
  net_return REAL NOT NULL,
  executable_qty REAL,
  status TEXT NOT NULL DEFAULT 'open'
);
