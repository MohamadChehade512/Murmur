"""HTTP client with a descriptive User-Agent, retries, and per-host rate limiting."""

from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "Murmur/0.1 (+https://github.com/MohamadChehade512/Murmur)"
log = logging.getLogger(__name__)


class PoliteClient:
    """Wraps requests.Session. `min_interval` sets the minimum seconds between calls to a host."""

    def __init__(self, min_interval: dict[str, float] | None = None, timeout: float = 30):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        retry = Retry(total=3, backoff_factor=2, status_forcelist=(429, 500, 502, 503, 504))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.min_interval = min_interval or {}
        self.timeout = timeout
        self._last: dict[str, float] = {}

    def get_json(self, url: str, params: dict | None = None) -> dict | None:
        host = urlparse(url).netloc
        wait = self.min_interval.get(host, 0) - (time.monotonic() - self._last.get(host, -1e9))
        if wait > 0:
            time.sleep(wait)
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            self._last[host] = time.monotonic()
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            # One failing source should never take down the whole run.
            log.warning("GET %s failed: %s", host, exc)
            return None
