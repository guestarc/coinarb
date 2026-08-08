# Expanded dealer reconciliation

## 2026-08-08 single-poll result

Working end-to-end:
- Kitco
- Money Metals
- BGASC

Parser hardening applied:
- Bullion Brothers: live page uses `Any Year - 1oz American Gold Eagle`; adapter now accepts the live title and anchors buyback to the labeled field.
- FMR Gold: live page exposes `Sell To Us Price`; adapter now tolerates rendered text where the currency symbol is separated or omitted.

Removed from executable automated candidate set:
- BullionMax: automated browser retrieval returns 401, and its current sell-to-us terms require a custom phone quote rather than a displayed executable bid.

Replacement sixth candidate:
- Silver.com: public random-year 1 oz Gold Eagle page exposes retail pricing and a displayed `Sell To Us Price`; bid remains quality B because verbal confirmation is required.

Gate candidate set for next live poll:
- Kitco
- Money Metals
- BGASC
- Bullion Brothers
- FMR Gold
- Silver.com
