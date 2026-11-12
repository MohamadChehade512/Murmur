"""Builds summary.json, the one file dashboards read."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

from .keywords import top_terms
from .models import Company, Mention

SCHEMA_VERSION = 1
WINDOW_DAYS = 7
HOURS = 48
SOURCES = [
    {"id": "news", "label": "News (GDELT and Google News)", "url": "https://www.gdeltproject.org/"},
    {"id": "hn", "label": "Hacker News", "url": "https://news.ycombinator.com/"},
    {"id": "bluesky", "label": "Bluesky", "url": "https://bsky.app/"},
]
LANGS = ("en", "ar")


def _shares(counts: Counter) -> dict:
    scored = sum(counts[k] for k in ("positive", "neutral", "negative"))
    shares = {k: round(counts[k] / scored, 3) if scored else 0.0 for k in ("positive", "neutral", "negative")}
    net = round((counts["positive"] - counts["negative"]) / scored, 3) if scored else 0.0
    return {**shares, "scored": scored, "net": net}


def _company_summary(company: Company, mentions: list[Mention], pageviews: list[dict], now: datetime) -> dict:
    today = now.date()
    days = [today - timedelta(days=i) for i in range(WINDOW_DAYS - 1, -1, -1)]
    start_hour = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=HOURS - 1)

    daily: dict[str, Counter] = defaultdict(Counter)
    hourly: Counter = Counter()
    sentiment: Counter = Counter()
    by_source: Counter = Counter()
    by_lang: Counter = Counter()
    for m in mentions:
        t = datetime.fromisoformat(m.published_at)
        d = daily[t.date().isoformat()]
        d["mentions"] += 1
        d[m.lang if m.lang in LANGS else "other"] += 1
        if m.sentiment:
            d[m.sentiment] += 1
            sentiment[m.sentiment] += 1
        by_source[m.source] += 1
        by_lang[m.lang if m.lang in LANGS else "other"] += 1
        if t >= start_hour:
            hourly[t.replace(minute=0, second=0, microsecond=0)] += 1

    terms = {lang: top_terms((m.terms for m in mentions if m.lang == lang), limit=10) for lang in LANGS}
    news = sorted((m for m in mentions if m.source == "news" and m.headline), key=lambda m: m.published_at)
    views = {p["date"]: p["views"] for p in pageviews}

    return {
        "id": company.id,
        "name": company.name,
        "color": company.color,
        "totals": {
            "mentions": len(mentions),
            "by_source": {s["id"]: by_source[s["id"]] for s in SOURCES},
            "by_lang": {k: by_lang[k] for k in (*LANGS, "other")},
        },
        "sentiment": _shares(sentiment),
        "daily": [
            {
                "date": day.isoformat(),
                "mentions": daily[day.isoformat()]["mentions"],
                **{k: daily[day.isoformat()][k] for k in (*LANGS, "other")},
                **{k: daily[day.isoformat()][k] for k in ("positive", "neutral", "negative")},
                "pageviews": views.get(day.isoformat()),
            }
            for day in days
        ],
        "hourly": [
            {
                "hour": (start_hour + timedelta(hours=i)).isoformat(),
                "mentions": hourly[start_hour + timedelta(hours=i)],
            }
            for i in range(HOURS)
        ],
        "top_terms": {lang: [{"term": t, "count": n} for t, n in terms[lang]] for lang in LANGS},
        "headlines": [
            {
                "title": m.headline,
                "url": m.url,
                "domain": m.domain,
                "lang": m.lang,
                "published_at": m.published_at,
                "sentiment": m.sentiment,
            }
            for m in reversed(news[-6:])
        ],
    }


def build_summary(
    companies: list[Company],
    mentions: list[Mention],
    pageviews: dict[str, list[dict]],
    sentiment_backend: str,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now(UTC)
    window_start = now - timedelta(days=WINDOW_DAYS)
    recent = [m for m in mentions if datetime.fromisoformat(m.published_at) >= window_start]
    return {
        "version": SCHEMA_VERSION,
        "generated_at": now.replace(microsecond=0).isoformat(),
        "window_days": WINDOW_DAYS,
        "sentiment_backend": sentiment_backend,
        "sources": SOURCES,
        "companies": [
            _company_summary(
                c,
                [m for m in recent if m.company == c.id],
                pageviews.get(c.id, []),
                now,
            )
            for c in companies
        ],
    }
