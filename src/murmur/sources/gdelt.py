"""News articles from the GDELT DOC 2.0 API (free, no key, about 65 languages).

GDELT asks for at most one request every 5 seconds; the client enforces that.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..http import PoliteClient
from ..models import Company, RawItem

API = "https://api.gdeltproject.org/api/v2/doc/doc"
HOST = "api.gdeltproject.org"
MIN_INTERVAL = 6.0
# One query per company covers both languages, which halves the requests.
LANG_FILTER = "(sourcelang:english OR sourcelang:arabic)"
LANG_CODES = {"English": "en", "Arabic": "ar"}


def parse(payload: dict | None, company: str) -> list[RawItem]:
    items = []
    for a in (payload or {}).get("articles", []):
        url, title = a.get("url"), (a.get("title") or "").strip()
        if not url or not title:
            continue
        try:
            seen = datetime.strptime(a["seendate"], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
        except (KeyError, ValueError):
            continue
        items.append(
            RawItem(
                source="news",
                company=company,
                native_id=url,
                url=url,
                published_at=seen,
                text=title,
                title=title,
                domain=a.get("domain"),
                lang=LANG_CODES.get(a.get("language", ""), "other"),
            )
        )
    return items


def collect(client: PoliteClient, company: Company, hours: int) -> list[RawItem]:
    if not company.news:
        return []
    payload = client.get_json(
        API,
        {
            "query": f"{company.news} {LANG_FILTER}",
            "mode": "artlist",
            "format": "json",
            "maxrecords": 150,
            "timespan": f"{hours}h",
            "sort": "datedesc",
        },
    )
    return parse(payload, company.id)
