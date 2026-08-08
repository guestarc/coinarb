CREATE TABLE IF NOT EXISTS poll_runs (
  poll_run_id TEXT PRIMARY KEY,
  started_at_utc TIMESTAMPTZ NOT NULL,
  completed_at_utc TIMESTAMPTZ,
  status TEXT NOT NULL,
  collector_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dealer_poll_status (
  poll_run_id TEXT NOT NULL,
  dealer_id TEXT NOT NULL,
  started_at_utc TIMESTAMPTZ NOT NULL,
  completed_at_utc TIMESTAMPTZ,
  status TEXT NOT NULL,
  observation_count INTEGER NOT NULL DEFAULT 0,
  error_type TEXT,
  error_message TEXT,
  PRIMARY KEY (poll_run_id, dealer_id)
);
CREATE TABLE IF NOT EXISTS observations (
  observation_id BIGSERIAL PRIMARY KEY,
  poll_run_id TEXT,
  fetch_id BIGINT,
  observed_at_utc TIMESTAMPTZ NOT NULL,
  dealer_id TEXT NOT NULL,
  canonical_sku TEXT NOT NULL,
  side TEXT NOT NULL,
  price DOUBLE PRECISION NOT NULL,
  quantity_min DOUBLE PRECISION,
  quantity_max DOUBLE PRECISION,
  inventory_status TEXT,
  bid_quality TEXT,
  source_url TEXT NOT NULL,
  raw_title TEXT,
  parser_version TEXT
);
CREATE INDEX IF NOT EXISTS idx_obs_market ON observations(canonical_sku,dealer_id,side,observed_at_utc);
CREATE INDEX IF NOT EXISTS idx_obs_poll ON observations(poll_run_id,dealer_id);
CREATE TABLE IF NOT EXISTS fetch_events (
  fetch_id BIGSERIAL PRIMARY KEY,
  poll_run_id TEXT NOT NULL,
  dealer_id TEXT NOT NULL,
  source_url TEXT NOT NULL,
  fetched_at_utc TIMESTAMPTZ NOT NULL,
  http_status INTEGER,
  latency_ms INTEGER,
  content_hash TEXT,
  stale_content BOOLEAN NOT NULL DEFAULT FALSE,
  error_type TEXT,
  error_message TEXT
);
CREATE TABLE IF NOT EXISTS raw_snapshots (
  snapshot_id BIGSERIAL PRIMARY KEY,
  fetch_id BIGINT NOT NULL,
  content_hash TEXT NOT NULL,
  body TEXT NOT NULL,
  retained_reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS spot_observations (
  spot_observation_id BIGSERIAL PRIMARY KEY,
  poll_run_id TEXT NOT NULL,
  observed_at_utc TIMESTAMPTZ NOT NULL,
  metal TEXT NOT NULL,
  price_usd DOUBLE PRECISION NOT NULL,
  source TEXT NOT NULL,
  source_url TEXT,
  quality TEXT NOT NULL DEFAULT 'reference'
);
CREATE TABLE IF NOT EXISTS opportunities (
  opportunity_id BIGSERIAL PRIMARY KEY,
  episode_key TEXT,
  first_seen_utc TIMESTAMPTZ NOT NULL,
  last_seen_utc TIMESTAMPTZ NOT NULL,
  canonical_sku TEXT NOT NULL,
  buy_dealer_id TEXT NOT NULL,
  sell_dealer_id TEXT NOT NULL,
  buy_price DOUBLE PRECISION NOT NULL,
  sell_price DOUBLE PRECISION NOT NULL,
  gross_spread DOUBLE PRECISION NOT NULL,
  modeled_cost DOUBLE PRECISION NOT NULL,
  net_profit_per_unit DOUBLE PRECISION NOT NULL,
  net_return DOUBLE PRECISION NOT NULL,
  executable_qty DOUBLE PRECISION,
  status TEXT NOT NULL DEFAULT 'open'
);
