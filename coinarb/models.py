from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    parser_version: str = "0.3.2"
    observed_at_utc: str = ""

    def with_timestamp(self):
        return self if self.observed_at_utc else replace(self, observed_at_utc=utc_now_iso())


@dataclass(frozen=True)
class FetchEvidence:
    url: str
    status_code: Optional[int]
    latency_ms: Optional[int]
    content_hash: Optional[str]
    body: str = ""
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class DealerCollection:
    observations: list[Observation] = field(default_factory=list)
    fetches: list[FetchEvidence] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)
