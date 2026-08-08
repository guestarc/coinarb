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
CREATE TABLE IF NOT EXISTS poll_runs (
  poll_run_id TEXT PRIMARY KEY,
  started_at_utc TEXT NOT NULL,
  completed_at_utc TEXT,
  status TEXT NOT NULL CHECK(status IN ('running','complete','partial','failed')),
  collector_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dealer_poll_status (
  poll_run_id TEXT NOT NULL,
  dealer_id TEXT NOT NULL,
  started_at_utc TEXT NOT NULL,
  completed_at_utc TEXT,
  status TEXT NOT NULL CHECK(status IN ('running','success','retrieval_failure','parser_failure','blocked','unavailable')),
  observation_count INTEGER NOT NULL DEFAULT 0,
  error_type TEXT,
  error_message TEXT,
  PRIMARY KEY (poll_run_id, dealer_id)
);
CREATE TABLE IF NOT EXISTS fetch_events (
  fetch_id INTEGER PRIMARY KEY AUTOINCREMENT,
  poll_run_id TEXT NOT NULL,
  dealer_id TEXT NOT NULL,
  source_url TEXT NOT NULL,
  fetched_at_utc TEXT NOT NULL,
  http_status INTEGER,
  latency_ms INTEGER,
  content_hash TEXT,
  stale_content INTEGER NOT NULL DEFAULT 0,
  error_type TEXT,
  error_message TEXT
);
CREATE TABLE IF NOT EXISTS raw_snapshots (
  snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
  fetch_id INTEGER NOT NULL,
  content_hash TEXT NOT NULL,
  body TEXT NOT NULL,
  retained_reason TEXT NOT NULL,
  FOREIGN KEY (fetch_id) REFERENCES fetch_events(fetch_id)
);
CREATE TABLE IF NOT EXISTS observations (
  observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  poll_run_id TEXT,
  fetch_id INTEGER,
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
  parser_version TEXT
);
CREATE INDEX IF NOT EXISTS idx_obs_market ON observations(canonical_sku, dealer_id, side, observed_at_utc);
CREATE INDEX IF NOT EXISTS idx_obs_poll ON observations(poll_run_id, dealer_id);
CREATE TABLE IF NOT EXISTS spot_observations (
  spot_observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  poll_run_id TEXT NOT NULL,
  observed_at_utc TEXT NOT NULL,
  metal TEXT NOT NULL CHECK(metal IN ('gold','silver')),
  price_usd REAL NOT NULL,
  source TEXT NOT NULL,
  source_url TEXT,
  quality TEXT NOT NULL DEFAULT 'reference'
);
CREATE TABLE IF NOT EXISTS opportunities (
  opportunity_id INTEGER PRIMARY KEY AUTOINCREMENT,
  episode_key TEXT,
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
