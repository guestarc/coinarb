import re
from .base import DealerAdapter
from ..models import Observation, DealerCollection


class JMBullionAdapter(DealerAdapter):
    dealer_id = "jm_bullion"
    PRODUCT_URL = "https://www.jmbullion.com/1-oz-american-gold-eagle/"

    def collect(self, canonical_sku: str):
        return self.collect_with_evidence(canonical_sku).observations

    def collect_with_evidence(self, canonical_sku: str):
        text, evidence = self.fetch_text(self.PRODUCT_URL)
        title = "1 oz American Gold Eagle Coin (Random Year)"
        if title not in text:
            raise ValueError("canonical product title not found")
        m = re.search(r"1 oz American Gold Eagle Coin \(Random Year\).*?(?:As Low As:|From:)\s*\$([0-9,]+\.\d{2})", text)
        if not m:
            raise ValueError("JM ask not found; fail closed pending validated retrieval path")
        ask = float(m.group(1).replace(',', ''))
        return DealerCollection(
            observations=[Observation(self.dealer_id, canonical_sku, "ask", ask, self.PRODUCT_URL, title,
                                      quantity_min=1, inventory_status="observed_page")],
            fetches=[evidence],
        )
