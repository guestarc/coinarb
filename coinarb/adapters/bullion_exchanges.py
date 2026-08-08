import os
import re
from .base import DealerAdapter, RetrievalError
from ..models import Observation, DealerCollection


class BullionExchangesAdapter(DealerAdapter):
    dealer_id = 'bullion_exchanges'
    PRODUCT_URL = 'https://bullionexchanges.com/1-oz-american-eagle-gold-coin-random-year'
    TITLE_ALIASES = (
        '1 oz Gold American Eagle $50 Coin BU (Random Year)',
        '1 oz Gold American Eagle Coin (Random Year)',
    )

    @classmethod
    def parse_text(cls, text, canonical_sku):
        title = next((t for t in cls.TITLE_ALIASES if t.lower() in text.lower()), None)
        if not title:
            raise ValueError('canonical product title not found')

        m = re.search(
            r'(?:1\s*-\s*19|1\+)\s*\$([0-9,]+\.\d{2})\s*\$([0-9,]+\.\d{2})(?:\s*\$([0-9,]+\.\d{2}))?',
            text,
            re.I,
        )
        if not m:
            raise ValueError('quantity-1 ask row not found')

        ask = float(m.group(1).replace(',', ''))
        bm = re.search(r'Our buy back price:\s*\$([0-9,]+\.\d{2})', text, re.I)
        out = [Observation(
            cls.dealer_id,
            canonical_sku,
            'ask',
            ask,
            cls.PRODUCT_URL,
            title,
            quantity_min=1,
            quantity_max=19,
            inventory_status='in_stock' if ('Buy Now' in text or 'In Stock' in text) else 'unknown',
        )]
        if bm:
            out.append(Observation(
                cls.dealer_id,
                canonical_sku,
                'bid',
                float(bm.group(1).replace(',', '')),
                cls.PRODUCT_URL,
                title,
                quantity_min=1,
                inventory_status='buyback_displayed',
                bid_quality='B',
            ))
        return out

    def collect(self, canonical_sku):
        return self.collect_with_evidence(canonical_sku).observations

    def collect_with_evidence(self, canonical_sku):
        text, evidence = self.fetch_text(self.PRODUCT_URL)
        try:
            observations = self.parse_text(text, canonical_sku)
            return DealerCollection(observations=observations, fetches=[evidence])
        except ValueError as direct_exc:
            if os.getenv('COINARB_BROWSER_FALLBACK', '0') != '1':
                if str(direct_exc) == 'canonical product title not found':
                    raise RetrievalError(
                        'HTTP 200 non-product response from Bullion Exchanges',
                        self.PRODUCT_URL,
                        status_code=200,
                        evidence=evidence,
                    )
                return DealerCollection(fetches=[evidence], parse_errors=[str(direct_exc)])

            browser_text, browser_evidence = self.fetch_text_browser(self.PRODUCT_URL)
            try:
                observations = self.parse_text(browser_text, canonical_sku)
                return DealerCollection(observations=observations, fetches=[evidence, browser_evidence])
            except ValueError as browser_exc:
                if (
                    str(direct_exc) == 'canonical product title not found'
                    and str(browser_exc) == 'canonical product title not found'
                ):
                    raise RetrievalError(
                        'HTTP 200 non-product response from Bullion Exchanges in direct and browser retrieval',
                        self.PRODUCT_URL,
                        status_code=200,
                        evidence=browser_evidence,
                    )
                return DealerCollection(
                    fetches=[evidence, browser_evidence],
                    parse_errors=[f'direct: {direct_exc}', f'browser: {browser_exc}'],
                )
