from pathlib import Path
from coinarb.db import Store
from coinarb.models import FetchEvidence, Observation


def test_poll_run_and_dealer_health(tmp_path: Path):
    store = Store(str(tmp_path / "coinarb.sqlite"), "schema.sql")
    poll_id = store.start_poll()
    store.start_dealer(poll_id, "kitco")
    obs = Observation("kitco", "US-AGE-1OZ-RANDOM-BU", "bid", 4200.0, "https://example.test/sell", "AGE", bid_quality="A")
    store.insert_observation(obs, poll_id)
    store.finish_dealer(poll_id, "kitco", "success", 1)
    store.finish_poll(poll_id, "complete")
    health = store.health_summary(poll_id)
    assert health[0]["dealer_id"] == "kitco"
    assert health[0]["status"] == "success"
    assert health[0]["observation_count"] == 1


def test_snapshots_only_retain_changed_content_by_default(tmp_path: Path):
    store = Store(str(tmp_path / "coinarb.sqlite"), "schema.sql")
    poll1 = store.start_poll()
    evidence = FetchEvidence("https://example.test", 200, 15, "abc", "<html>one</html>")
    store.record_fetch(poll1, "kitco", evidence)
    store.finish_poll(poll1, "complete")

    poll2 = store.start_poll()
    store.record_fetch(poll2, "kitco", evidence)
    store.finish_poll(poll2, "complete")

    with store.connect() as con:
        fetches = con.execute("SELECT stale_content FROM fetch_events ORDER BY fetch_id").fetchall()
        snapshots = con.execute("SELECT COUNT(*) FROM raw_snapshots").fetchone()[0]
    assert [row[0] for row in fetches] == [0, 1]
    assert snapshots == 1
