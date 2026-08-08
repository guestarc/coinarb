import re
import requests
from bs4 import BeautifulSoup
from .base import DealerAdapter
from ..models import Observation

class JMBullionAdapter(DealerAdapter):
    dealer_id = "jm_bullion"
    PRODUCT_URL = "https://www.jmbullion.com/1-oz-american-gold-eagle/"

    def collect(self, canonical_sku: str):
        r = requests.get(self.PRODUCT_URL, timeout=20, headers={
            "User-Agent":"Mozilla/5.0 (compatible; CoinArbResearch/0.1; +research)"
        })
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = " ".join(soup.stripped_strings)
        title = "1 oz American Gold Eagle Coin (Random Year)"
        if title not in text:
            raise ValueError("canonical product title not found")
        # JM markup changes frequently; only accept price text explicitly adjacent to the canonical product.
        m = re.search(r"1 oz American Gold Eagle Coin \(Random Year\).*?(?:As Low As:|From:)\s*\$([0-9,]+\.\d{2})", text)
        if not m:
            raise ValueError("JM ask not found; browser/network fallback required")
        ask = float(m.group(1).replace(',', ''))
        return [Observation(self.dealer_id, canonical_sku, "ask", ask, self.PRODUCT_URL, title,
                            quantity_min=1, inventory_status="observed_page")]
