from coinarb.adapters.jm_bullion import JMBullionAdapter
from coinarb.adapters.bullion_exchanges import BullionExchangesAdapter
from coinarb.adapters.kitco import KitcoAdapter
from coinarb.adapters.money_metals import MoneyMetalsAdapter
from coinarb.adapters.base import RetrievalError, ParserError
from coinarb.db import Store
from coinarb.opportunities import compute_opportunities

SKU = "US-AGE-1OZ-RANDOM-BU"
COLLECTOR_VERSION = "0.3.1"


def classify_retrieval(exc: RetrievalError) -> str:
    if exc.status_code in (401, 403, 429):
        return "blocked"
    return "retrieval_failure"


def run_poll(store=None):
    store = store or Store.from_env()
    adapters = [JMBullionAdapter(), BullionExchangesAdapter(), KitcoAdapter(), MoneyMetalsAdapter()]
    poll_run_id = store.start_poll(COLLECTOR_VERSION)
    poll_observations = []
    successes = 0

    for adapter in adapters:
        store.start_dealer(poll_run_id, adapter.dealer_id)
        try:
            collection = adapter.collect_with_evidence(SKU)
            fetch_ids = {}
            for evidence in collection.fetches:
                fetch_ids[evidence.url] = store.record_fetch(poll_run_id, adapter.dealer_id, evidence)
            for observation in collection.observations:
                store.insert_observation(observation, poll_run_id, fetch_ids.get(observation.source_url))
                poll_observations.append(observation)
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
        "observations": len(poll_observations),
        "opportunities": opportunities,
        "dealer_health": store.health_summary(poll_run_id),
    }


def main():
    result = run_poll()
    print(f"poll_run_id={result['poll_run_id']} status={result['status']} observations={result['observations']}")
    for dealer in result["dealer_health"]:
        print(dealer)
    for opportunity in result["opportunities"]:
        print("OPPORTUNITY", opportunity)


if __name__ == "__main__":
    main()
