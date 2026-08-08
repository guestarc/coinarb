import sqlite3
from pathlib import Path
from .models import Observation

class Store:
    def __init__(self, db_path: str, schema_path: str):
        self.db_path = db_path
        self.schema_path = schema_path
        self.init()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def init(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con, open(self.schema_path, "r", encoding="utf-8") as f:
            con.executescript(f.read())

    def insert_observation(self, obs: Observation):
        obs = obs.with_timestamp()
        with self.connect() as con:
            con.execute(
                """INSERT INTO observations
                (observed_at_utc,dealer_id,canonical_sku,side,price,quantity_min,quantity_max,inventory_status,bid_quality,source_url,raw_title,parser_version)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (obs.observed_at_utc,obs.dealer_id,obs.canonical_sku,obs.side,obs.price,obs.quantity_min,obs.quantity_max,obs.inventory_status,obs.bid_quality,obs.source_url,obs.raw_title,obs.parser_version)
            )
