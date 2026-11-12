"""Daily English Wikipedia page views, a simple measure of public attention."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from ..http import PoliteClient

API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user"


def parse(payload: dict | None) -> list[dict]:
    out = []
    for item in (payload or {}).get("items", []):
        ts = item.get("timestamp", "")
        if len(ts) >= 8:
            out.append({"date": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}", "views": int(item.get("views", 0))})
    return out


def collect(client: PoliteClient, article: str, days: int = 30) -> list[dict]:
    end = datetime.now(UTC) - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    title = quote(article.replace(" ", "_"), safe="")
    url = f"{API}/{title}/daily/{start:%Y%m%d}/{end:%Y%m%d}"
    return parse(client.get_json(url))
