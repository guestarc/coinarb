# CoinArb Phase 0 Collector

Purpose: collect immutable dealer ask/bid observations for standardized bullion SKUs and later construct deterministic dealer-to-dealer arbitrage opportunities.

Current v0.1 scope:
- SQLite schema
- canonical config scaffolding
- JM Bullion ask collector
- Bullion Exchanges ask collector
- bid-quality gating in opportunity engine

Important: v0.1 does **not** infer a buyback bid from ambiguous page content. Dealer buyback adapters must point to an explicit sell-to-us/buyback quote surface and classify lockability before a bid may count as executable.
