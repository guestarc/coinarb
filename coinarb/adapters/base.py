from abc import ABC, abstractmethod
import hashlib
import time
import requests
from bs4 import BeautifulSoup
from ..models import DealerCollection, FetchEvidence


class RetrievalError(RuntimeError):
    def __init__(self, message, url, status_code=None, latency_ms=None):
        super().__init__(message)
        self.url = url
        self.status_code = status_code
        self.latency_ms = latency_ms


class DealerAdapter(ABC):
    dealer_id: str
    user_agent = "CoinArb research collector/0.3"

    def fetch_text(self, url: str):
        started = time.perf_counter()
        try:
            response = requests.get(url, timeout=20, headers={"User-Agent": self.user_agent})
            latency = round((time.perf_counter() - started) * 1000)
            response.raise_for_status()
        except requests.RequestException as exc:
            latency = round((time.perf_counter() - started) * 1000)
            status = getattr(getattr(exc, "response", None), "status_code", None)
            raise RetrievalError(str(exc), url, status, latency) from exc
        body = response.text
        digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
        text = " ".join(BeautifulSoup(body, "html.parser").stripped_strings)
        return text, FetchEvidence(url=url, status_code=response.status_code, latency_ms=latency, content_hash=digest, body=body)

    @abstractmethod
    def collect(self, canonical_sku: str):
        raise NotImplementedError

    def collect_with_evidence(self, canonical_sku: str) -> DealerCollection:
        return DealerCollection(observations=self.collect(canonical_sku))
