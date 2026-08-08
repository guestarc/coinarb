from coinarb.adapters.bgasc import BGASCAdapter
from coinarb.adapters.bullion_brothers import BullionBrothersAdapter
from coinarb.adapters.bullionmax import BullionMaxAdapter
from coinarb.adapters.fmr_gold import FMRGoldAdapter

SKU = "US-AGE-1OZ-RANDOM-BU"


def test_bullionmax_structure():
    text = "1 oz American Gold Eagle Coin (Random Year) Availability: In Stock Qty 1-9 $4,215.90 $4,259.82 $4,391.56 Sell To Us Price: $3,940.91"
    obs = BullionMaxAdapter.parse_text(text, SKU)
    assert obs[0].price == 4215.90 and obs[0].side == "ask"
    assert obs[1].price == 3940.91 and obs[1].bid_quality == "B"


def test_bgasc_structure():
    text = "1 oz American Gold Eagle Coin (Random Year) In Stock Pricing 1-9 $4,222.68 $4,266.67 $4,398.62 SELL TO US PRICE:$3,952.69"
    obs = BGASCAdapter.parse_text(text, SKU)
    assert obs[0].price == 4222.68 and obs[0].side == "ask"
    assert obs[1].price == 3952.69 and obs[1].bid_quality == "B"


def test_fmr_gold_structure():
    text = "1 Oz American Gold Eagle Coin BU (Any Date) Volume Discount Pricing Quantity Check / Wire 1 – 9 4,173.60 4,257.07 4,340.54 Sell To Us Price: $3,960.82"
    obs = FMRGoldAdapter.parse_text(text, SKU)
    assert obs[0].price == 4173.60 and obs[0].side == "ask"
    assert obs[1].price == 3960.82 and obs[1].bid_quality == "B"


def test_fmr_gold_rendered_text_without_currency_symbol():
    text = "1 Oz American Gold Eagle Coin BU (Any Date) Quantity 1 - 9 4,173.60 4,257.07 4,340.54 Sell To Us Price 3,960.82"
    obs = FMRGoldAdapter.parse_text(text, SKU)
    assert obs[0].price == 4173.60
    assert obs[1].price == 3960.82


def test_bullion_brothers_structure():
    text = "(Random Year) - 1oz American Gold Eagle Tier Qty Tier 1 Buyback Price $4,245.42 $4,012.10 Add to Cart"
    obs = BullionBrothersAdapter.parse_text(text, SKU)
    assert obs[0].price == 4245.42 and obs[0].side == "ask"
    assert obs[1].price == 4012.10 and obs[1].bid_quality == "B"


def test_bullion_brothers_live_title_alias():
    text = "Any Year - 1oz American Gold Eagle Qty 1+ $4,245.42 Buyback Price $4,012.10 Add to Cart"
    obs = BullionBrothersAdapter.parse_text(text, SKU)
    assert obs[0].price == 4245.42
    assert obs[1].price == 4012.10
