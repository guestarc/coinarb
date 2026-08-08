import os
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

        # Current product page shows the product heading, a displayed price, then
        # the Qty/Wire table. Anchor to the heading and stop before the next
        # product so a nearby coin cannot be mistaken for the AGE.
        product_block = re.search(
            r'(?:1 oz Gold Eagle Coins|1 oz Gold American Eagle Coin)(.*?)(?=1 oz Gold Canadian Maple Leaf Coin|1/2 oz Gold American Eagle Coin|$)',
            text,
            re.S | re.I,
        )
        block = product_block.group(0) if product_block else text
        m = re.search(r'Qty\s*\|?\s*Wire/Check.*?1\+\s*\|?\s*\$([0-9,]+\.\d{2})', block, re.S | re.I)
        if not m:
            # Browser-rendered text can omit table separators but retains the
            # product heading followed by the quantity-one wire price.
            m = re.search(r'1\+\s*\$([0-9,]+\.\d{2})', block, re.I)
        if not m:
            raise ValueError('Kitco ask not found')

        return Observation(
            cls.dealer_id,
            sku,
            'ask',
            float(m.group(1).replace(',', '')),
            cls.BUY_URL,
            title,
            quantity_min=1,
            inventory_status='available',
        )

    @classmethod
    def parse_sell_text(cls, text, sku):
        # Current sell page presents the quote directly below the H1.
        m = re.search(r'Sell 1 oz American Gold Eagle Coins\s*\$([0-9,]+\.\d{2})', text, re.I)
        if not m:
            m = re.search(r'Sell 1 oz American Gold Eagle Coins.*?\$([0-9,]+\.\d{2})', text, re.S | re.I)
        if not m:
            raise ValueError('Kitco sell quote not found')
        return Observation(
            cls.dealer_id,
            sku,
            'bid',
            float(m.group(1).replace(',', '')),
            cls.SELL_URL,
            'Sell 1 oz American Gold Eagle Coins',
            quantity_min=1,
            inventory_status='sell_quote_surface',
            bid_quality='A',
        )

    def collect(self, canonical_sku):
        return self.collect_with_evidence(canonical_sku).observations

    def _collect_surface(self, url, parser, canonical_sku, label):
        text, evidence = self.fetch_text(url)
        try:
            return parser(text, canonical_sku), [evidence], []
        except ValueError as direct_exc:
            if os.getenv('COINARB_BROWSER_FALLBACK', '0') != '1':
                return None, [evidence], [f'{label}: {direct_exc}']
            browser_text, browser_evidence = self.fetch_text_browser(url)
            try:
                return parser(browser_text, canonical_sku), [evidence, browser_evidence], []
            except ValueError as browser_exc:
                return None, [evidence, browser_evidence], [
                    f'{label} direct: {direct_exc}',
                    f'{label} browser: {browser_exc}',
                ]

    def collect_with_evidence(self, canonical_sku):
        observations = []
        fetches = []
        errors = []

        buy_obs, buy_fetches, buy_errors = self._collect_surface(
            self.BUY_URL, self.parse_buy_text, canonical_sku, 'buy'
        )
        fetches.extend(buy_fetches)
        errors.extend(buy_errors)
        if buy_obs:
            observations.append(buy_obs)

        sell_obs, sell_fetches, sell_errors = self._collect_surface(
            self.SELL_URL, self.parse_sell_text, canonical_sku, 'sell'
        )
        fetches.extend(sell_fetches)
        errors.extend(sell_errors)
        if sell_obs:
            observations.append(sell_obs)

        return DealerCollection(observations=observations, fetches=fetches, parse_errors=errors)
