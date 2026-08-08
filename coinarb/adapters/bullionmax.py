import os
import re

from .base import DealerAdapter
from ..models import Observation, DealerCollection


class BullionMaxAdapter(DealerAdapter):
    dealer_id = "bullionmax"
    PRODUCT_URL = "https://www.bullionmax.com/buy-gold/1-oz-american-gold-eagle-coin/"
    TITLE = "1 oz American Gold Eagle Coin (Random Year)"

    @classmethod
    def parse_text(cls, text, canonical_sku):
        if cls.TITLE.lower() not in text.lower():
            raise ValueError("canonical product title not found")
        ask_match = re.search(r"1\s*-\s*9\s*\$([0-9,]+\.\d{2})", text, re.I)
        bid_match = re.search(r"Sell To Us Price:\s*\$([0-9,]+\.\d{2})", text, re.I)
        if not ask_match:
            raise ValueError("quantity-1 ask row not found")
        if not bid_match:
            raise ValueError("sell-to-us price not found")
        return [
            Observation(cls.dealer_id, canonical_sku, "ask", float(ask_match.group(1).replace(",", "")), cls.PRODUCT_URL, cls.TITLE, quantity_min=1, quantity_max=9, inventory_status="available" if "In Stock" in text else "unknown"),
            Observation(cls.dealer_id, canonical_sku, "bid", float(bid_match.group(1).replace(",", "")), cls.PRODUCT_URL, cls.TITLE, quantity_min=1, inventory_status="displayed_sell_to_us", bid_quality="B"),
        ]

    def collect(self, canonical_sku):
        return self.collect_with_evidence(canonical_sku).observations

    def collect_with_evidence(self, canonical_sku):
        text, evidence = self.fetch_text_with_browser_fallback(self.PRODUCT_URL)
        try:
            return DealerCollection(observations=self.parse_text(text, canonical_sku), fetches=[evidence])
        except ValueError as direct_exc:
            if os.getenv("COINARB_BROWSER_FALLBACK", "0") != "1":
                return DealerCollection(fetches=[evidence], parse_errors=[str(direct_exc)])
            browser_text, browser_evidence = self.fetch_text_browser(self.PRODUCT_URL)
            try:
                return DealerCollection(observations=self.parse_text(browser_text, canonical_sku), fetches=[evidence, browser_evidence])
            except ValueError as browser_exc:
                return DealerCollection(fetches=[evidence, browser_evidence], parse_errors=[f"direct: {direct_exc}", f"browser: {browser_exc}"])
