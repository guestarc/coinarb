import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from collector import run_poll

POLL_COUNT = int(os.getenv("COINARB_VALIDATION_POLLS", "6"))
INTERVAL_SECONDS = int(os.getenv("COINARB_VALIDATION_INTERVAL_SECONDS", "600"))
OUTPUT_DIR = Path(os.getenv("COINARB_VALIDATION_OUTPUT_DIR", "data/validation"))


def serialize_result(index, result):
    return {
        "validation_poll": index,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "poll_run_id": result["poll_run_id"],
        "status": result["status"],
        "observations": [
            {
                "dealer_id": o.dealer_id,
                "side": o.side,
                "price": o.price,
                "quantity_min": o.quantity_min,
                "quantity_max": o.quantity_max,
                "inventory_status": o.inventory_status,
                "bid_quality": o.bid_quality,
                "source_url": o.source_url,
            }
            for o in result["observations"]
        ],
        "dealer_health": result["dealer_health"],
        "opportunities": result["opportunities"],
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = OUTPUT_DIR / f"six_poll_{stamp}.jsonl"

    print(f"Starting {POLL_COUNT} polls, {INTERVAL_SECONDS} seconds apart")
    print(f"Dealers: {os.getenv('COINARB_DEALERS', 'all')}")
    print(f"Output: {output_path}")

    for index in range(1, POLL_COUNT + 1):
        started = time.monotonic()
        result = run_poll()
        row = serialize_result(index, result)
        with output_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, sort_keys=True) + "\n")

        print(f"\nPOLL {index}/{POLL_COUNT} status={result['status']} poll_run_id={result['poll_run_id']}")
        for observation in row["observations"]:
            print("OBSERVATION", observation)
        for health in row["dealer_health"]:
            print("HEALTH", health)

        if index < POLL_COUNT:
            elapsed = time.monotonic() - started
            sleep_for = max(0, INTERVAL_SECONDS - elapsed)
            print(f"Next poll in {round(sleep_for)} seconds")
            time.sleep(sleep_for)

    print(f"\nValidation complete. Results saved to {output_path}")


if __name__ == "__main__":
    main()
