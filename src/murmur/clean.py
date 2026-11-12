"""Turns raw collector output into clean, relevant, de-duplicated items."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .models import Company, RawItem
from .text import detect_lang, fold, remove_urls, strip_html

MAX_HASHTAGS = 6
MIN_CHARS = 12


def _alias_patterns(company: Company) -> list[re.Pattern]:
    patterns = []
    for alias in company.aliases:
        a = re.escape(fold(alias))
        # Word boundaries for Latin script; Arabic attaches prefixes (و، ب، ال) so match inside words.
        patterns.append(re.compile(rf"\b{a}\b" if alias.isascii() else a))
    return patterns


def is_relevant(text: str, patterns: list[re.Pattern]) -> bool:
    folded = fold(text)
    return any(p.search(folded) for p in patterns)


# Listings, giveaways and bots that post song titles add noise for every company.
SPAM_PHRASES = ("#nowplaying", "now playing", "for sale (", "giveaway", "promo code", "use code")


def looks_like_spam(text: str) -> bool:
    lowered = text.casefold()
    return text.count("#") > MAX_HASHTAGS or len(text) < MIN_CHARS or any(p in lowered for p in SPAM_PHRASES)


def clean(
    raw: Iterable[RawItem], companies: list[Company], known_ids: set[str] | None = None
) -> list[RawItem]:
    """Strips markup, fills in language, drops spam and off-topic items, removes duplicates.

    Duplicates are caught by id (same post twice) and by text (the same post copied across accounts).
    `known_ids` are ids already stored, so re-collected items are skipped.
    """
    from .models import mention_id

    patterns = {c.id: _alias_patterns(c) for c in companies}
    excludes = {c.id: [fold(x) for x in c.exclude] for c in companies}
    seen_ids = set(known_ids or ())
    seen_text: set[tuple[str, str]] = set()
    out: list[RawItem] = []
    for item in raw:
        mid = mention_id(item.source, item.native_id)
        if mid in seen_ids:
            continue
        text = remove_urls(strip_html(item.text)).strip()
        if looks_like_spam(text) or not is_relevant(text, patterns.get(item.company, [])):
            continue
        if any(x in fold(text) for x in excludes.get(item.company, [])):
            continue
        key = (item.company, fold(text)[:200])
        if key in seen_text:
            continue
        seen_ids.add(mid)
        seen_text.add(key)
        item.text = text
        if item.title:
            item.title = strip_html(item.title)
        guessed = detect_lang(text)
        # Trust the source's language tag unless the script clearly says Arabic.
        item.lang = "ar" if guessed == "ar" else (item.lang or guessed)
        out.append(item)
    return out
