from abc import ABC, abstractmethod
import hashlib
import time
import requests
from bs4 import BeautifulSoup
from ..models import DealerCollection, FetchEvidence


class RetrievalError(RuntimeError):
    def __init__(self, message, url, status_code=None, latency_ms=None, evidence=None):
        super().__init__(message)
        self.url = url
        self.status_code = status_code
        self.latency_ms = latency_ms
        self.evidence = evidence


class ParserError(ValueError):
    def __init__(self, message, fetches=None):
        super().__init__(message)
        self.fetches = fetches or []


class DealerAdapter(ABC):
    dealer_id: str
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    def fetch_text(self, url: str):
        started = time.perf_counter()
        try:
            response = requests.get(url, timeout=20, headers=self.headers, allow_redirects=True)
        except requests.RequestException as exc:
            latency = round((time.perf_counter() - started) * 1000)
            raise RetrievalError(str(exc), url, None, latency) from exc

        latency = round((time.perf_counter() - started) * 1000)
        body = response.text
        digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
        evidence = FetchEvidence(
            url=url,
            status_code=response.status_code,
            latency_ms=latency,
            content_hash=digest,
            body=body,
        )
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RetrievalError(str(exc), url, response.status_code, latency, evidence) from exc

        text = " ".join(BeautifulSoup(body, "html.parser").stripped_strings)
        return text, evidence

    @abstractmethod
    def collect(self, canonical_sku: str):
        raise NotImplementedError

    def collect_with_evidence(self, canonical_sku: str) -> DealerCollection:
        return DealerCollection(observations=self.collect(canonical_sku))
