import os
import re

from .base import DealerAdapter
from ..models import Observation, DealerCollection


class BullionBrothersAdapter(DealerAdapter):
    dealer_id = "bullion_brothers"
    PRODUCT_URL = "https://bullionbrother.com/top-items"
    TITLE_ALIASES = (
        "Any Year - 1oz American Gold Eagle",
        "(Random Year) - 1oz American Gold Eagle",
    )

    @classmethod
    def parse_text(cls, text, canonical_sku):
        lower = text.lower()
        title = next((candidate for candidate in cls.TITLE_ALIASES if candidate.lower() in lower), None)
        if not title:
            raise ValueError("canonical product title not found")
        start = lower.find(title.lower())
        block = text[start:start + 500]

        # Flattened page text can place the Buyback Price label before the row's
        # numeric values. Require the label, then treat the first product-block
        # price as the retail ask and the last as the displayed buyback.
        if not re.search(r"Buyback\s*Price", block, re.I):
            raise ValueError("buyback label not found")
        prices = re.findall(r"\$\s*([0-9,]+\.\d{2})", block)
        if len(prices) < 2:
            raise ValueError("ask/buyback prices not found")

        ask = float(prices[0].replace(",", ""))
        bid = float(prices[-1].replace(",", ""))
        return [
            Observation(cls.dealer_id, canonical_sku, "ask", ask, cls.PRODUCT_URL, title, quantity_min=1, inventory_status="available"),
            Observation(cls.dealer_id, canonical_sku, "bid", bid, cls.PRODUCT_URL, title, quantity_min=1, inventory_status="displayed_buyback", bid_quality="B"),
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
