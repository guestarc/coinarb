import re
from .base import DealerAdapter
from ..models import Observation, DealerCollection


class MoneyMetalsAdapter(DealerAdapter):
    dealer_id = 'money_metals'
    BUY_URL = 'https://www.moneymetals.com/buy/gold/american-gold-eagle/1-oz-gold-eagle-coins'
    SELL_URL = 'https://www.moneymetals.com/sell-to-us'
    PRODUCT = '1 oz Gold American Gold Eagle Coin, TYPE 2 Design (Dates Our Choice)'

    @classmethod
    def parse_buy_text(cls, text, sku):
        product = '1 oz Gold American Eagle Coin, TYPE 2 Design (Dates Our Choice)'
        pat = re.escape(product) + r'.*?1\s*-\s*9\s*\|?\s*\$([0-9,]+\.\d{2})'
        m = re.search(pat, text, re.S | re.I)
        if not m:
            raise ValueError('Money Metals random-date AGE ask not found')
        return Observation(cls.dealer_id, sku, 'ask', float(m.group(1).replace(',', '')), cls.BUY_URL, product,
                           quantity_min=1, quantity_max=9, inventory_status='available')

    @classmethod
    def parse_sell_text(cls, text, sku):
        m = re.search(r'American Gold Eagle Coin 2021 Type 2 - 1 Troy Ounce\s*Sell Price:\s*\$([0-9,]+\.\d{2}) each', text, re.S | re.I)
        if not m:
            raise ValueError('Money Metals AGE sell price not found')
        return Observation(cls.dealer_id, sku, 'bid', float(m.group(1).replace(',', '')), cls.SELL_URL,
                           'American Gold Eagle Coin 2021 Type 2 - 1 Troy Ounce', quantity_min=1,
                           inventory_status='online_committed_sale', bid_quality='A')

    def collect(self, canonical_sku):
        return self.collect_with_evidence(canonical_sku).observations

    def collect_with_evidence(self, canonical_sku):
        buy_text, buy_evidence = self.fetch_text(self.BUY_URL)
        sell_text, sell_evidence = self.fetch_text(self.SELL_URL)
        return DealerCollection(
            observations=[self.parse_buy_text(buy_text, canonical_sku), self.parse_sell_text(sell_text, canonical_sku)],
            fetches=[buy_evidence, sell_evidence],
        )
