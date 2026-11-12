"""Stories and comments from Hacker News, through the Algolia search API (free, no key)."""

from __future__ import annotations

from datetime import UTC, datetime

from ..http import PoliteClient
from ..models import Company, RawItem

API = "https://hn.algolia.com/api/v1/search_by_date"


def parse(payload: dict | None, company: str) -> list[RawItem]:
    items = []
    for h in (payload or {}).get("hits", []):
        text = h.get("title") or h.get("comment_text") or ""
        if not text or not h.get("objectID"):
            continue
        items.append(
            RawItem(
                source="hn",
                company=company,
                native_id=h["objectID"],
                url=f"https://news.ycombinator.com/item?id={h['objectID']}",
                published_at=datetime.fromtimestamp(h["created_at_i"], tz=UTC),
                text=text,
                domain="news.ycombinator.com",
            )
        )
    return items


def collect(client: PoliteClient, company: Company, hours: int) -> list[RawItem]:
    since = int(datetime.now(UTC).timestamp()) - hours * 3600
    items: list[RawItem] = []
    for term in company.search:
        if not term.isascii():  # HN is English-language
            continue
        payload = client.get_json(
            API,
            {
                "query": term,
                "tags": "(story,comment)",
                "numericFilters": f"created_at_i>{since}",
                "hitsPerPage": 100,
            },
        )
        items += parse(payload, company.id)
    return items
