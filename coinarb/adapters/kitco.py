import re
from .base import DealerAdapter
from ..models import Observation, DealerCollection


class KitcoAdapter(DealerAdapter):
    dealer_id = 'kitco'
    BUY_URL = 'https://online.kitco.com/buy/3000/1-oz-Gold-American-Eagle-Coin-9167-3000'
    SELL_URL = 'https://online.kitco.com/sell/3000/1-oz-Gold-American-Eagle-Coin-9167-3000'

    @classmethod
    def parse_buy_text(cls, text, sku):
        titles = ('1 oz Gold Eagle Coins', '1 oz Gold American Eagle Coin')
        title = next((t for t in titles if t.lower() in text.lower()), None)
        if not title:
            raise ValueError('Kitco AGE title missing')
        # Current live page uses "1 oz Gold Eagle Coins" and a standard Qty/Wire table.
        m = re.search(r'(?:1 oz Gold Eagle Coins|1 oz Gold American Eagle Coin).*?Qty\s*\|?\s*Wire/Check.*?1\+\s*\|?\s*\$([0-9,]+\.\d{2})', text, re.S | re.I)
        if not m:
            m = re.search(r'1\+\s*\|?\s*\$([0-9,]+\.\d{2})', text)
        if not m:
            raise ValueError('Kitco ask not found')
        return Observation(cls.dealer_id, sku, 'ask', float(m.group(1).replace(',', '')), cls.BUY_URL,
                           title, quantity_min=1, inventory_status='available')

    @classmethod
    def parse_sell_text(cls, text, sku):
        m = re.search(r'Sell 1 oz American Gold Eagle Coins\s*\$([0-9,]+\.\d{2})', text, re.I)
        if not m:
            m = re.search(r'Sell 1 oz American Gold Eagle Coins.*?\$([0-9,]+\.\d{2})', text, re.S | re.I)
        if not m:
            raise ValueError('Kitco sell quote not found')
        return Observation(cls.dealer_id, sku, 'bid', float(m.group(1).replace(',', '')), cls.SELL_URL,
                           'Sell 1 oz American Gold Eagle Coins', quantity_min=1,
                           inventory_status='sell_quote_surface', bid_quality='A')

    def collect(self, canonical_sku):
        return self.collect_with_evidence(canonical_sku).observations

    def collect_with_evidence(self, canonical_sku):
        buy_text, buy_evidence = self.fetch_text(self.BUY_URL)
        sell_text, sell_evidence = self.fetch_text(self.SELL_URL)
        observations = []
        errors = []
        try:
            observations.append(self.parse_buy_text(buy_text, canonical_sku))
        except ValueError as exc:
            errors.append(f'buy: {exc}')
        try:
            observations.append(self.parse_sell_text(sell_text, canonical_sku))
        except ValueError as exc:
            errors.append(f'sell: {exc}')
        return DealerCollection(observations=observations, fetches=[buy_evidence, sell_evidence], parse_errors=errors)
