"""Headlines from Google News RSS search, in English and Arabic (free, no key).

A second news source next to GDELT, which often rate-limits shared cloud IPs.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from ..http import PoliteClient
from ..models import Company, RawItem

API = "https://news.google.com/rss/search"
HOST = "news.google.com"
MIN_INTERVAL = 2.0
EDITIONS = {
    "en": {"hl": "en-US", "gl": "US", "ceid": "US:en"},
    "ar": {"hl": "ar", "gl": "AE", "ceid": "AE:ar"},
}


def parse(xml_text: str | None, company: str, lang: str, since: datetime | None = None) -> list[RawItem]:
    if not xml_text:
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items = []
    for it in root.iter("item"):
        title, link, pub = it.findtext("title") or "", it.findtext("link") or "", it.findtext("pubDate")
        source = it.find("source")
        publisher = (source.text or "").strip() if source is not None else ""
        try:
            published = parsedate_to_datetime(pub).astimezone(UTC) if pub else None
        except (TypeError, ValueError):
            published = None
        if not title or not link or not published or (since and published < since):
            continue
        # Titles end with " - Publisher"; drop it so the headline reads cleanly.
        if publisher and title.endswith(f" - {publisher}"):
            title = title[: -len(publisher) - 3]
        domain = urlparse(source.get("url", "")).netloc if source is not None else ""
        items.append(
            RawItem(
                source="news",
                company=company,
                native_id=it.findtext("guid") or link,
                url=link,
                published_at=published,
                text=title.strip(),
                title=title.strip(),
                domain=domain.removeprefix("www.") or publisher or None,
                lang=lang,
            )
        )
    return items


def collect(client: PoliteClient, company: Company, hours: int) -> list[RawItem]:
    since = datetime.now(UTC) - timedelta(hours=hours)
    items: list[RawItem] = []
    for lang, query in company.headlines.items():
        if lang not in EDITIONS:
            continue
        text = client.get_text(API, {"q": f"{query} when:{max(1, hours)}h", **EDITIONS[lang]})
        items += parse(text, company.id, lang, since)
    return items
