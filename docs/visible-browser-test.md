# Visible browser diagnostic

For local diagnostics only, CoinArb can run the existing Playwright fallback in a visible installed Chrome window.

Environment variables:

- `COINARB_BROWSER_FALLBACK=1` enables the browser fallback after blocked retrieval or semantic page mismatch.
- `COINARB_BROWSER_HEADLESS=0` launches visible Chrome instead of headless Chrome.

This is a diagnostic step, not an anti-bot bypass strategy. If visible Chrome still receives 401/403 responses, CoinArb should fail closed and not escalate to stealth plugins, CAPTCHA solving, residential proxies, or browser fingerprint evasion during Phase 0.
