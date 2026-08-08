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

        # The live top-items surface exposes the product row as one retail price
        # followed by a labeled buyback price. Anchor the bid to the label so
        # unrelated page prices cannot be mistaken for the product buyback.
        prices = re.findall(r"\$\s*([0-9,]+\.\d{2})", block)
        buyback_match = re.search(r"Buyback\s*Price\s*\$?\s*([0-9,]+\.\d{2})", block, re.I)
        if not prices:
            raise ValueError("quantity-1 ask price not found")
        if not buyback_match:
            raise ValueError("buyback price not found")

        ask = float(prices[0].replace(",", ""))
        bid = float(buyback_match.group(1).replace(",", ""))
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
