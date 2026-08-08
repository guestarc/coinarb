import os
import sqlite3
import uuid
from pathlib import Path
from .models import Observation, utc_now_iso


class Store:
    def __init__(self, db_path: str | None = None, schema_path: str = "schema.sql"):
        self.db_path = db_path or os.getenv("COINARB_SQLITE_PATH", "data/coinarb.sqlite")
        self.schema_path = schema_path
        self.init()

    @classmethod
    def from_env(cls):
        database_url = os.getenv("DATABASE_URL", "")
        if database_url.startswith(("postgres://", "postgresql://")):
            return PostgresStore(database_url)
        return cls()

    def connect(self):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    def init(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con, open(self.schema_path, "r", encoding="utf-8") as f:
            con.executescript(f.read())
        self._migrate_sqlite()

    def _migrate_sqlite(self):
        with self.connect() as con:
            cols = {r[1] for r in con.execute("PRAGMA table_info(observations)")}
            if "poll_run_id" not in cols:
                con.execute("ALTER TABLE observations ADD COLUMN poll_run_id TEXT")
            if "fetch_id" not in cols:
                con.execute("ALTER TABLE observations ADD COLUMN fetch_id INTEGER")

    def start_poll(self, collector_version="0.3.0") -> str:
        poll_run_id = str(uuid.uuid4())
        with self.connect() as con:
            con.execute("INSERT INTO poll_runs VALUES (?,?,?,?,?)", (poll_run_id, utc_now_iso(), None, "running", collector_version))
        return poll_run_id

    def finish_poll(self, poll_run_id: str, status: str):
        with self.connect() as con:
            con.execute("UPDATE poll_runs SET completed_at_utc=?, status=? WHERE poll_run_id=?", (utc_now_iso(), status, poll_run_id))

    def start_dealer(self, poll_run_id: str, dealer_id: str):
        with self.connect() as con:
            con.execute("INSERT OR REPLACE INTO dealer_poll_status (poll_run_id,dealer_id,started_at_utc,status) VALUES (?,?,?,?)", (poll_run_id, dealer_id, utc_now_iso(), "running"))

    def finish_dealer(self, poll_run_id: str, dealer_id: str, status: str, observation_count=0, error_type=None, error_message=None):
        with self.connect() as con:
            con.execute("""UPDATE dealer_poll_status SET completed_at_utc=?,status=?,observation_count=?,error_type=?,error_message=?
                         WHERE poll_run_id=? AND dealer_id=?""",
                        (utc_now_iso(), status, observation_count, error_type, error_message, poll_run_id, dealer_id))

    def record_fetch(self, poll_run_id, dealer_id, evidence, retain_reason=None):
        with self.connect() as con:
            previous = con.execute("""SELECT content_hash FROM fetch_events WHERE dealer_id=? AND source_url=? AND content_hash IS NOT NULL
                                      ORDER BY fetch_id DESC LIMIT 1""", (dealer_id, evidence.url)).fetchone()
            stale = bool(previous and previous[0] == evidence.content_hash)
            cur = con.execute("""INSERT INTO fetch_events
                (poll_run_id,dealer_id,source_url,fetched_at_utc,http_status,latency_ms,content_hash,stale_content,error_type,error_message)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (poll_run_id,dealer_id,evidence.url,utc_now_iso(),evidence.status_code,evidence.latency_ms,evidence.content_hash,int(stale),evidence.error_type,evidence.error_message))
            fetch_id = cur.lastrowid
            reason = retain_reason or ("content_changed" if not stale else None)
            if evidence.body and reason:
                con.execute("INSERT INTO raw_snapshots (fetch_id,content_hash,body,retained_reason) VALUES (?,?,?,?)",
                            (fetch_id,evidence.content_hash,evidence.body,reason))
        return fetch_id

    def insert_observation(self, obs: Observation, poll_run_id=None, fetch_id=None):
        obs = obs.with_timestamp()
        with self.connect() as con:
            con.execute("""INSERT INTO observations
                (poll_run_id,fetch_id,observed_at_utc,dealer_id,canonical_sku,side,price,quantity_min,quantity_max,inventory_status,bid_quality,source_url,raw_title,parser_version)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (poll_run_id,fetch_id,obs.observed_at_utc,obs.dealer_id,obs.canonical_sku,obs.side,obs.price,obs.quantity_min,obs.quantity_max,obs.inventory_status,obs.bid_quality,obs.source_url,obs.raw_title,obs.parser_version))

    def health_summary(self, poll_run_id: str):
        with self.connect() as con:
            rows = con.execute("SELECT dealer_id,status,observation_count,error_type,error_message FROM dealer_poll_status WHERE poll_run_id=? ORDER BY dealer_id", (poll_run_id,)).fetchall()
        return [dict(r) for r in rows]


class PostgresStore:
    """Small PostgreSQL backend for the cloud collector. SQLite remains the local default."""
    def __init__(self, database_url: str, schema_path="schema_postgres.sql"):
        import psycopg
        self.psycopg = psycopg
        self.database_url = database_url
        with self.connect() as con, open(schema_path, "r", encoding="utf-8") as f:
            con.execute(f.read())

    def connect(self):
        return self.psycopg.connect(self.database_url)

    def start_poll(self, collector_version="0.3.0"):
        poll_run_id = str(uuid.uuid4())
        with self.connect() as con:
            con.execute("INSERT INTO poll_runs (poll_run_id,started_at_utc,status,collector_version) VALUES (%s,%s,%s,%s)", (poll_run_id, utc_now_iso(), "running", collector_version))
        return poll_run_id

    def finish_poll(self, poll_run_id, status):
        with self.connect() as con:
            con.execute("UPDATE poll_runs SET completed_at_utc=%s,status=%s WHERE poll_run_id=%s", (utc_now_iso(), status, poll_run_id))

    def start_dealer(self, poll_run_id, dealer_id):
        with self.connect() as con:
            con.execute("""INSERT INTO dealer_poll_status (poll_run_id,dealer_id,started_at_utc,status) VALUES (%s,%s,%s,%s)
                           ON CONFLICT (poll_run_id,dealer_id) DO UPDATE SET started_at_utc=EXCLUDED.started_at_utc,status=EXCLUDED.status""", (poll_run_id, dealer_id, utc_now_iso(), "running"))

    def finish_dealer(self, poll_run_id, dealer_id, status, observation_count=0, error_type=None, error_message=None):
        with self.connect() as con:
            con.execute("""UPDATE dealer_poll_status SET completed_at_utc=%s,status=%s,observation_count=%s,error_type=%s,error_message=%s
                           WHERE poll_run_id=%s AND dealer_id=%s""", (utc_now_iso(), status, observation_count, error_type, error_message, poll_run_id, dealer_id))

    def record_fetch(self, poll_run_id, dealer_id, evidence, retain_reason=None):
        with self.connect() as con:
            previous = con.execute("""SELECT content_hash FROM fetch_events WHERE dealer_id=%s AND source_url=%s AND content_hash IS NOT NULL
                                      ORDER BY fetch_id DESC LIMIT 1""", (dealer_id, evidence.url)).fetchone()
            stale = bool(previous and previous[0] == evidence.content_hash)
            row = con.execute("""INSERT INTO fetch_events
                (poll_run_id,dealer_id,source_url,fetched_at_utc,http_status,latency_ms,content_hash,stale_content,error_type,error_message)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING fetch_id""",
                (poll_run_id,dealer_id,evidence.url,utc_now_iso(),evidence.status_code,evidence.latency_ms,evidence.content_hash,stale,evidence.error_type,evidence.error_message)).fetchone()
            fetch_id = row[0]
            reason = retain_reason or ("content_changed" if not stale else None)
            if evidence.body and reason:
                con.execute("INSERT INTO raw_snapshots (fetch_id,content_hash,body,retained_reason) VALUES (%s,%s,%s,%s)",
                            (fetch_id,evidence.content_hash,evidence.body,reason))
        return fetch_id

    def insert_observation(self, obs, poll_run_id=None, fetch_id=None):
        obs = obs.with_timestamp()
        with self.connect() as con:
            con.execute("""INSERT INTO observations
                (poll_run_id,fetch_id,observed_at_utc,dealer_id,canonical_sku,side,price,quantity_min,quantity_max,inventory_status,bid_quality,source_url,raw_title,parser_version)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (poll_run_id,fetch_id,obs.observed_at_utc,obs.dealer_id,obs.canonical_sku,obs.side,obs.price,obs.quantity_min,obs.quantity_max,obs.inventory_status,obs.bid_quality,obs.source_url,obs.raw_title,obs.parser_version))

    def health_summary(self, poll_run_id):
        with self.connect() as con:
            rows = con.execute("SELECT dealer_id,status,observation_count,error_type,error_message FROM dealer_poll_status WHERE poll_run_id=%s ORDER BY dealer_id", (poll_run_id,)).fetchall()
        return [dict(zip(("dealer_id","status","observation_count","error_type","error_message"), r)) for r in rows]
