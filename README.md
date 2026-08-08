# CoinArb v0.3 Cloud Gate 1

CoinArb collects auditable dealer ask/bid observations for canonical physical-bullion SKUs and constructs deterministic dealer-to-dealer spread candidates.

## Current validation SKU

`US-AGE-1OZ-RANDOM-BU` — 1 oz American Gold Eagle, with variant/type distinctions preserved when economically relevant.

## Dealers in the current validation set

- Bullion Exchanges: retail ask + displayed product buyback
- Kitco: public buy + sell surfaces
- Money Metals: retail ask + sell-to-us surface; Type 2 matching remains explicit
- JM Bullion: fail closed until product-level retrieval is reliably validated

## v0.3 additions

- UUID poll-run records and explicit poll lifecycle
- per-dealer success/failure records
- retrieval vs parser vs blocked classifications
- HTTP status, latency, SHA-256 content hash, and stale-content tracking
- raw source snapshots on changed fetch content
- SQLite local persistence with safe migration from the earlier observation table
- PostgreSQL cloud persistence selected by `DATABASE_URL`
- automatic cross-dealer opportunity calculation after a poll
- basic collector-health output
- GitHub Actions CI
- environment-based configuration with no credentials in source control

The schema includes spot observations, but no spot feed is enabled until a source has been separately validated. Indicative/reference metal prices must never silently become executable dealer prices.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
pytest -q
python collector.py
```

SQLite is the default and writes to `data/coinarb.sqlite`.

For PostgreSQL, set `DATABASE_URL` to a PostgreSQL connection string before running the collector.

## Gate 1 sequence

Do not jump directly to the seven-day run.

1. CI must pass.
2. Deploy to a normal-network Python runtime with PostgreSQL.
3. Run six actual polls ten minutes apart.
4. Manually reconcile every captured ask/bid against the dealer source pages.
5. Fix retrieval, parser, SKU, inventory, or bid-quality discrepancies.
6. Only then begin the seven-day, approximately 1,008-cycle Gate 1 collection.

Gate 1 target: at least 90% successful observations for enabled core dealer/SKU combinations with no material parser, SKU, or bid-quality errors.

## Important economics rule

A positive displayed spread is not yet an arbitrage trade. Transaction costs, quantity limits, inventory, payment method, shipping/tax, liquidation terms, settlement timing, and metal-price exposure still have to be modeled before a candidate counts as executable net profit.
