# Expanded dealer reconciliation

## 2026-08-08 single-poll result

Working end-to-end:
- Kitco
- Money Metals
- BGASC

Needs parser hardening:
- Bullion Brothers: live page uses `Any Year - 1oz American Gold Eagle` while the adapter anchored on `(Random Year) - 1oz American Gold Eagle`.
- FMR Gold: live page exposes `Sell To Us Price`, but rendered text may omit or separate the currency symbol from the numeric value.

Remove from executable automated candidate set:
- BullionMax: automated browser retrieval returns 401, and the dealer's current sell-to-us terms require a custom phone quote rather than a displayed executable bid.

The six-dealer Gate target remains the goal, but only dealers with both auditable purchase ask and auditable buyback/sell-to-us pricing should count toward it.
