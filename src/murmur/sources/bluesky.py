"""Public posts from Bluesky's search endpoint (free, no login needed on api.bsky.app)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ..http import PoliteClient
from ..models import Company, RawItem

API = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"


def _parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except (AttributeError, ValueError):
        return None


def parse(payload: dict | None, company: str) -> list[RawItem]:
    items = []
    for p in (payload or {}).get("posts", []):
        record, author = p.get("record") or {}, p.get("author") or {}
        text, uri, handle = record.get("text") or "", p.get("uri") or "", author.get("handle")
        created = _parse_time(record.get("createdAt", ""))
        if not text or not uri or not handle or not created:
            continue
        rkey = uri.rsplit("/", 1)[-1]
        langs = record.get("langs") or []
        items.append(
            RawItem(
                source="bluesky",
                company=company,
                native_id=uri,
                url=f"https://bsky.app/profile/{handle}/post/{rkey}",
                published_at=created,
                text=text,
                domain="bsky.app",
                lang=langs[0].split("-")[0] if langs else None,
            )
        )
    return items


def collect(client: PoliteClient, company: Company, hours: int) -> list[RawItem]:
    since = (datetime.now(UTC) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    items: list[RawItem] = []
    for term in company.search:
        payload = client.get_json(API, {"q": term, "sort": "latest", "limit": 100, "since": since})
        items += parse(payload, company.id)
    return items
