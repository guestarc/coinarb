import re, requests
from bs4 import BeautifulSoup
from .base import DealerAdapter
from ..models import Observation

class BullionExchangesAdapter(DealerAdapter):
    dealer_id = 'bullion_exchanges'
    PRODUCT_URL = 'https://bullionexchanges.com/1-oz-american-eagle-gold-coin-random-year'
    TITLE = '1 oz Gold American Eagle $50 Coin BU (Random Year)'

    @classmethod
    def parse_text(cls, text, canonical_sku):
        if cls.TITLE not in text:
            raise ValueError('canonical product title not found')
        m = re.search(r'1-19\s*\$([0-9,]+\.\d{2})\s*\$([0-9,]+\.\d{2})\s*\$([0-9,]+\.\d{2})', text)
        if not m: raise ValueError('quantity-1 ask row not found')
        ask=float(m.group(1).replace(',',''))
        bm=re.search(r'Our buy back price:\s*\$([0-9,]+\.\d{2})', text, re.I)
        out=[Observation(cls.dealer_id,canonical_sku,'ask',ask,cls.PRODUCT_URL,cls.TITLE,quantity_min=1,quantity_max=19,inventory_status='in_stock' if 'In Stock' in text else 'unknown')]
        if bm:
            out.append(Observation(cls.dealer_id,canonical_sku,'bid',float(bm.group(1).replace(',','')),cls.PRODUCT_URL,cls.TITLE,quantity_min=1,inventory_status='buyback_displayed',bid_quality='B'))
        return out

    def collect(self, canonical_sku):
        r=requests.get(self.PRODUCT_URL,timeout=20,headers={'User-Agent':'CoinArb research collector/0.2'})
        r.raise_for_status(); text=' '.join(BeautifulSoup(r.text,'html.parser').stripped_strings)
        return self.parse_text(text,canonical_sku)
