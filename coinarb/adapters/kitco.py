import re, requests
from bs4 import BeautifulSoup
from .base import DealerAdapter
from ..models import Observation

class KitcoAdapter(DealerAdapter):
    dealer_id='kitco'
    BUY_URL='https://online.kitco.com/buy/3000/1-oz-Gold-American-Eagle-Coin-9167-3000'
    SELL_URL='https://online.kitco.com/sell/3000/1-oz-Gold-American-Eagle-Coin-9167-3000'

    @classmethod
    def parse_buy_text(cls,text,sku):
        # Product page headline followed later by quantity table. Prefer explicit page-level price when present.
        if '1 oz Gold American Eagle' not in text: raise ValueError('Kitco AGE title missing')
        m=re.search(r'1 oz Gold American Eagle Coin.*?Qty\s*\|\s*Wire/Check.*?1\+\s*\|\s*\$([0-9,]+\.\d{2})',text,re.S|re.I)
        if not m:
            m=re.search(r'1\+\s*\|\s*\$([0-9,]+\.\d{2})',text)
        if not m: raise ValueError('Kitco ask not found')
        return Observation(cls.dealer_id,sku,'ask',float(m.group(1).replace(',','')),cls.BUY_URL,'1 oz Gold American Eagle Coin',quantity_min=1,inventory_status='available')

    @classmethod
    def parse_sell_text(cls,text,sku):
        m=re.search(r'#?\s*Sell 1 oz American Gold Eagle Coins\s*\$([0-9,]+\.\d{2})',text,re.I)
        if not m:
            m=re.search(r'Sell 1 oz American Gold Eagle Coins.*?\$([0-9,]+\.\d{2})',text,re.S|re.I)
        if not m: raise ValueError('Kitco sell quote not found')
        return Observation(cls.dealer_id,sku,'bid',float(m.group(1).replace(',','')),cls.SELL_URL,'Sell 1 oz American Gold Eagle Coins',quantity_min=1,inventory_status='sell_quote_surface',bid_quality='A')

    def _text(self,url):
        r=requests.get(url,timeout=20,headers={'User-Agent':'CoinArb research collector/0.2'}); r.raise_for_status()
        return ' '.join(BeautifulSoup(r.text,'html.parser').stripped_strings)
    def collect(self,canonical_sku):
        return [self.parse_buy_text(self._text(self.BUY_URL),canonical_sku),self.parse_sell_text(self._text(self.SELL_URL),canonical_sku)]
