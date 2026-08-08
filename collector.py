import os

from coinarb.adapters.jm_bullion import JMBullionAdapter
from coinarb.adapters.bullion_exchanges import BullionExchangesAdapter
from coinarb.adapters.kitco import KitcoAdapter
from coinarb.adapters.money_metals import MoneyMetalsAdapter
from coinarb.adapters.bullionmax import BullionMaxAdapter
from coinarb.adapters.bgasc import BGASCAdapter
from coinarb.adapters.bullion_brothers import BullionBrothersAdapter
from coinarb.adapters.fmr_gold import FMRGoldAdapter
from coinarb.adapters.silver_com import SilverComAdapter
from coinarb.adapters.base import RetrievalError, ParserError
from coinarb.db import Store
from coinarb.opportunities import compute_opportunities

SKU = "US-AGE-1OZ-RANDOM-BU"
COLLECTOR_VERSION = "0.3.7"

ADAPTERS = {
    "jm_bullion": JMBullionAdapter,
    "bullion_exchanges": BullionExchangesAdapter,
    "kitco": KitcoAdapter,
    "money_metals": MoneyMetalsAdapter,
    "bullionmax": BullionMaxAdapter,
    "bgasc": BGASCAdapter,
    "bullion_brothers": BullionBrothersAdapter,
    "fmr_gold": FMRGoldAdapter,
    "silver_com": SilverComAdapter,
}


def selected_adapters():
    raw = os.getenv("COINARB_DEALERS", "").strip()
    if not raw:
        names = list(ADAPTERS)
    else:
        names = [name.strip() for name in raw.split(",") if name.strip()]
        unknown = [name for name in names if name not in ADAPTERS]
        if unknown:
            raise ValueError(f"unknown COINARB_DEALERS: {', '.join(unknown)}")
    return [ADAPTERS[name]() for name in names]


def classify_retrieval(exc: RetrievalError) -> str:
    if exc.status_code in (401, 403, 429):
        return "blocked"
    return "retrieval_failure"


def run_poll(store=None, adapters=None):
    store = store or Store.from_env()
    adapters = adapters or selected_adapters()
    poll_run_id = store.start_poll(COLLECTOR_VERSION)
    poll_observations = []
    successes = 0

    for adapter in adapters:
        store.start_dealer(poll_run_id, adapter.dealer_id)
        try:
            collection = adapter.collect_with_evidence(SKU)
            fetch_ids = {}
            retain_reason = "parser_failure" if collection.parse_errors else None
            for evidence in collection.fetches:
                fetch_ids[evidence.url] = store.record_fetch(poll_run_id, adapter.dealer_id, evidence, retain_reason=retain_reason)
            for observation in collection.observations:
                store.insert_observation(observation, poll_run_id, fetch_ids.get(observation.source_url))
                poll_observations.append(observation)

            if collection.parse_errors:
                status = "partial_parser_failure" if collection.observations else "parser_failure"
                store.finish_dealer(
                    poll_run_id,
                    adapter.dealer_id,
                    status,
                    len(collection.observations),
                    "ValueError",
                    "; ".join(collection.parse_errors),
                )
                if collection.observations:
                    successes += 1
            else:
                store.finish_dealer(poll_run_id, adapter.dealer_id, "success", len(collection.observations))
                successes += 1
        except RetrievalError as exc:
            if exc.evidence is not None:
                store.record_fetch(poll_run_id, adapter.dealer_id, exc.evidence, retain_reason="retrieval_failure")
            status = classify_retrieval(exc)
            store.finish_dealer(poll_run_id, adapter.dealer_id, status, 0, type(exc).__name__, str(exc))
        except ParserError as exc:
            for evidence in exc.fetches:
                store.record_fetch(poll_run_id, adapter.dealer_id, evidence, retain_reason="parser_failure")
            store.finish_dealer(poll_run_id, adapter.dealer_id, "parser_failure", 0, type(exc).__name__, str(exc))
        except ValueError as exc:
            store.finish_dealer(poll_run_id, adapter.dealer_id, "parser_failure", 0, type(exc).__name__, str(exc))
        except Exception as exc:
            store.finish_dealer(poll_run_id, adapter.dealer_id, "retrieval_failure", 0, type(exc).__name__, str(exc))

    if successes == len(adapters):
        poll_status = "complete"
    elif successes:
        poll_status = "partial"
    else:
        poll_status = "failed"
    store.finish_poll(poll_run_id, poll_status)

    opportunities = compute_opportunities(poll_observations)
    return {
        "poll_run_id": poll_run_id,
        "status": poll_status,
        "observations": poll_observations,
        "opportunities": opportunities,
        "dealer_health": store.health_summary(poll_run_id),
    }


def print_result(result):
    print(f"poll_run_id={result['poll_run_id']} status={result['status']} observations={len(result['observations'])}")
    for observation in result["observations"]:
        print(
            "OBSERVATION",
            {
                "dealer_id": observation.dealer_id,
                "side": observation.side,
                "price": observation.price,
                "quantity_min": observation.quantity_min,
                "quantity_max": observation.quantity_max,
                "inventory_status": observation.inventory_status,
                "bid_quality": observation.bid_quality,
                "source_url": observation.source_url,
            },
        )
    for dealer in result["dealer_health"]:
        print(dealer)
    for opportunity in result["opportunities"]:
        print("OPPORTUNITY", opportunity)


def main():
    print_result(run_poll())


if __name__ == "__main__":
    main()
