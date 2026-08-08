from coinarb.adapters.jm_bullion import JMBullionAdapter
from coinarb.adapters.bullion_exchanges import BullionExchangesAdapter
from coinarb.adapters.kitco import KitcoAdapter
from coinarb.adapters.money_metals import MoneyMetalsAdapter
from coinarb.db import Store

SKU = "US-AGE-1OZ-RANDOM-BU"

def main():
    store = Store("data/coinarb.sqlite", "schema.sql")
    adapters = [JMBullionAdapter(), BullionExchangesAdapter(), KitcoAdapter(), MoneyMetalsAdapter()]
    count = 0
    for adapter in adapters:
        try:
            obs = adapter.collect(SKU)
            for o in obs:
                store.insert_observation(o)
                print(o)
                count += 1
        except Exception as e:
            print(f"{adapter.dealer_id}: ERROR {e}")
    print(f"stored={count}")

if __name__ == "__main__":
    main()
