from abc import ABC, abstractmethod
import hashlib
import os
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


class DealerAdapter(ABC):
    dealer_id: str
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    }

    def fetch_text(self, url: str):
        started = time.perf_counter()
        try:
            response = requests.get(url, timeout=20, headers=self.headers)
            latency = round((time.perf_counter() - started) * 1000)
            body = response.text
            digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
            evidence = FetchEvidence(url=url, status_code=response.status_code, latency_ms=latency, content_hash=digest, body=body)
            response.raise_for_status()
        except requests.RequestException as exc:
            latency = round((time.perf_counter() - started) * 1000)
            response = getattr(exc, "response", None)
            status = getattr(response, "status_code", None)
            body = getattr(response, "text", "") or ""
            digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest() if body else None
            evidence = FetchEvidence(url=url, status_code=status, latency_ms=latency, content_hash=digest, body=body,
                                     error_type=type(exc).__name__, error_message=str(exc))
            raise RetrievalError(str(exc), url, status, latency, evidence) from exc
        text = " ".join(BeautifulSoup(body, "html.parser").stripped_strings)
        return text, evidence

    def fetch_text_browser(self, url: str):
        if os.getenv("COINARB_BROWSER_FALLBACK", "0") != "1":
            raise RetrievalError("browser fallback disabled", url)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RetrievalError("Playwright is not installed; install coinarb[browser]", url) from exc

        started = time.perf_counter()
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page(locale="en-US")
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1500)
                body = page.content()
                status = response.status if response else None
                latency = round((time.perf_counter() - started) * 1000)
                digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
                evidence = FetchEvidence(url=url, status_code=status, latency_ms=latency, content_hash=digest, body=body)
                if status and status >= 400:
                    raise RetrievalError(f"browser HTTP {status}", url, status, latency, evidence)
                text = " ".join(BeautifulSoup(body, "html.parser").stripped_strings)
                return text, evidence
            finally:
                browser.close()

    def fetch_text_with_browser_fallback(self, url: str):
        try:
            return self.fetch_text(url)
        except RetrievalError as exc:
            if exc.status_code not in (401, 403, 429):
                raise
            return self.fetch_text_browser(url)

    @abstractmethod
    def collect(self, canonical_sku: str):
        raise NotImplementedError

    def collect_with_evidence(self, canonical_sku: str) -> DealerCollection:
        return DealerCollection(observations=self.collect(canonical_sku))
