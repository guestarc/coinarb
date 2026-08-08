from pathlib import Path
from coinarb.adapters.bullion_exchanges import BullionExchangesAdapter
from coinarb.adapters.kitco import KitcoAdapter
from coinarb.adapters.money_metals import MoneyMetalsAdapter
SKU='US-AGE-1OZ-RANDOM-BU'
F=Path(__file__).parent/'fixtures'
def text(n): return (F/n).read_text()

def test_bullion_exchanges_snapshot():
 o=BullionExchangesAdapter.parse_text(text('bullion_exchanges_age_2026-08-07.txt'),SKU)
 assert o[0].price==4325.29 and o[0].side=='ask'
 assert o[1].price==4212.75 and o[1].bid_quality=='B'

def test_kitco_snapshot():
 a=KitcoAdapter.parse_buy_text(text('kitco_buy_age_2026-08-07.txt'),SKU)
 b=KitcoAdapter.parse_sell_text(text('kitco_sell_age_2026-08-07.txt'),SKU)
 assert a.price==4395.29 and b.price==4245.65 and b.bid_quality=='A'

def test_money_metals_snapshot():
 a=MoneyMetalsAdapter.parse_buy_text(text('money_metals_buy_age_2026-08-07.txt'),SKU)
 b=MoneyMetalsAdapter.parse_sell_text(text('money_metals_sell_age_2026-08-07.txt'),SKU)
 assert a.price==4570.45 and b.price==4250.30 and b.bid_quality=='A'
