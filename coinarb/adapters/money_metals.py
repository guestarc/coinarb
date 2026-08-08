import re, requests
from bs4 import BeautifulSoup
from .base import DealerAdapter
from ..models import Observation

class MoneyMetalsAdapter(DealerAdapter):
    dealer_id='money_metals'
    BUY_URL='https://www.moneymetals.com/buy/gold/american-gold-eagle/1-oz-gold-eagle-coins'
    SELL_URL='https://www.moneymetals.com/sell-to-us'
    PRODUCT='1 oz Gold American Eagle Coin, TYPE 2 Design (Dates Our Choice)'

    @classmethod
    def parse_buy_text(cls,text,sku):
        pat=re.escape(cls.PRODUCT)+r'.*?1\s*-\s*9\s*\|?\s*\$([0-9,]+\.\d{2})'
        m=re.search(pat,text,re.S|re.I)
        if not m: raise ValueError('Money Metals random-date AGE ask not found')
        return Observation(cls.dealer_id,sku,'ask',float(m.group(1).replace(',','')),cls.BUY_URL,cls.PRODUCT,quantity_min=1,quantity_max=9,inventory_status='available')

    @classmethod
    def parse_sell_text(cls,text,sku):
        # Money Metals states coin dates need not match, so the 2021 Type 2 line is an executable product-class bid for matching Type 2 AGE.
        m=re.search(r'American Gold Eagle Coin 2021 Type 2 - 1 Troy Ounce\s*Sell Price:\s*\$([0-9,]+\.\d{2}) each',text,re.S|re.I)
        if not m: raise ValueError('Money Metals AGE sell price not found')
        return Observation(cls.dealer_id,sku,'bid',float(m.group(1).replace(',','')),cls.SELL_URL,'American Gold Eagle Coin 2021 Type 2 - 1 Troy Ounce',quantity_min=1,inventory_status='online_committed_sale',bid_quality='A')

    def _text(self,url):
        r=requests.get(url,timeout=20,headers={'User-Agent':'CoinArb research collector/0.2'}); r.raise_for_status()
        return ' '.join(BeautifulSoup(r.text,'html.parser').stripped_strings)
    def collect(self,canonical_sku):
        return [self.parse_buy_text(self._text(self.BUY_URL),canonical_sku),self.parse_sell_text(self._text(self.SELL_URL),canonical_sku)]
