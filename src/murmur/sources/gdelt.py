"""News articles from the GDELT DOC 2.0 API (free, no key, about 65 languages).

GDELT asks for at most one request every 5 seconds; the client enforces that.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..http import PoliteClient
from ..models import Company, RawItem

API = "https://api.gdeltproject.org/api/v2/doc/doc"
HOST = "api.gdeltproject.org"
MIN_INTERVAL = 5.5
LANGS = {"en": "english", "ar": "arabic"}


def parse(payload: dict | None, company: str, lang: str) -> list[RawItem]:
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
                lang=lang,
            )
        )
    return items


def collect(client: PoliteClient, company: Company, hours: int) -> list[RawItem]:
    items: list[RawItem] = []
    for lang, query in company.news.items():
        if lang not in LANGS:
            continue
        payload = client.get_json(
            API,
            {
                "query": f"{query} sourcelang:{LANGS[lang]}",
                "mode": "artlist",
                "format": "json",
                "maxrecords": 100,
                "timespan": f"{hours}h",
                "sort": "datedesc",
            },
        )
        items += parse(payload, company.id, lang)
    return items
