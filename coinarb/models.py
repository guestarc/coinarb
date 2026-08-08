from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

@dataclass(frozen=True)
class Observation:
    dealer_id: str
    canonical_sku: str
    side: str
    price: float
    source_url: str
    raw_title: str
    quantity_min: Optional[float] = None
    quantity_max: Optional[float] = None
    inventory_status: Optional[str] = None
    bid_quality: Optional[str] = None
    parser_version: str = "0.1.0"
    observed_at_utc: str = ""

    def with_timestamp(self):
        if self.observed_at_utc:
            return self
        return Observation(**{**self.__dict__, "observed_at_utc": datetime.now(timezone.utc).isoformat()})
