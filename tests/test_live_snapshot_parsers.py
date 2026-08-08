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


def test_bullion_exchanges_current_structure():
    page='1 oz Gold American Eagle Coin (Random Year) Card/PayPal The prices below represent the item full list price. 1+ $4,111.10 $4,152.63 $4,275.54 Buy Now Our buy back price:$4,000.69 Sell Now'
    o=BullionExchangesAdapter.parse_text(page,SKU)
    assert o[0].price==4111.10 and o[0].inventory_status=='in_stock'
    assert o[1].price==4000.69 and o[1].bid_quality=='B'


def test_kitco_snapshot():
    a=KitcoAdapter.parse_buy_text(text('kitco_buy_age_2026-08-07.txt'),SKU)
    b=KitcoAdapter.parse_sell_text(text('kitco_sell_age_2026-08-07.txt'),SKU)
    assert a.price==4395.29 and b.price==4245.65 and b.bid_quality=='A'


def test_kitco_current_structure():
    buy='1 oz Gold Eagle Coins $4,494.30 Qty | Wire/Check | Credit Card/PayPal | Bitcoin 1+ | $4,494.30 | $4,681.56 | $4,539.70 10+ | $4,484.30'
    sell='Sell 1 oz American Gold Eagle Coins $4,245.65 What You Should Know'
    a=KitcoAdapter.parse_buy_text(buy,SKU)
    b=KitcoAdapter.parse_sell_text(sell,SKU)
    assert a.price==4494.30 and b.price==4245.65 and b.bid_quality=='A'


def test_money_metals_snapshot():
    a=MoneyMetalsAdapter.parse_buy_text(text('money_metals_buy_age_2026-08-07.txt'),SKU)
    b=MoneyMetalsAdapter.parse_sell_text(text('money_metals_sell_age_2026-08-07.txt'),SKU)
    assert a.price==4570.45 and b.price==4250.30 and b.bid_quality=='A'
