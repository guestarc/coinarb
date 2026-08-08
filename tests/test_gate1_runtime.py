from pathlib import Path
import sqlite3
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


def test_legacy_v01_observation_foreign_keys_are_seeded(tmp_path: Path):
    db = tmp_path / "legacy.sqlite"
    con = sqlite3.connect(db)
    con.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE products (
          canonical_sku TEXT PRIMARY KEY, metal TEXT NOT NULL, mint TEXT,
          product TEXT NOT NULL, year_label TEXT, fine_weight_oz REAL NOT NULL,
          purity REAL, condition TEXT
        );
        CREATE TABLE dealers (
          dealer_id TEXT PRIMARY KEY, name TEXT NOT NULL, parent TEXT,
          enabled INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE observations (
          observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
          observed_at_utc TEXT NOT NULL,
          dealer_id TEXT NOT NULL,
          canonical_sku TEXT NOT NULL,
          side TEXT NOT NULL,
          price REAL NOT NULL,
          quantity_min REAL,
          quantity_max REAL,
          inventory_status TEXT,
          bid_quality TEXT,
          source_url TEXT NOT NULL,
          raw_title TEXT,
          parser_version TEXT,
          FOREIGN KEY (dealer_id) REFERENCES dealers(dealer_id),
          FOREIGN KEY (canonical_sku) REFERENCES products(canonical_sku)
        );
    """)
    con.close()

    store = Store(str(db), "schema.sql")
    poll_id = store.start_poll()
    obs = Observation("kitco", "US-AGE-1OZ-RANDOM-BU", "ask", 4300.0, "https://example.test", "AGE")
    store.insert_observation(obs, poll_id)

    with store.connect() as check:
        assert check.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 1
        assert check.execute("SELECT COUNT(*) FROM dealers WHERE dealer_id='kitco'").fetchone()[0] == 1
        assert check.execute("SELECT COUNT(*) FROM products WHERE canonical_sku='US-AGE-1OZ-RANDOM-BU'").fetchone()[0] == 1
