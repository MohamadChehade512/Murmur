"""One full run: collect, clean, score, store, summarise, publish."""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .aggregate import WINDOW_DAYS, build_summary
from .clean import clean
from .http import PoliteClient
from .keywords import extract_terms
from .models import Company, Mention, RawItem, mention_id
from .sentiment import Backend
from .sources import bluesky, gdelt, google_news, hackernews, wikipedia
from .store import Store

log = logging.getLogger(__name__)
SITE_DIR = Path(__file__).resolve().parents[2] / "site"


@dataclass
class RunStats:
    collected: int = 0
    kept: int = 0
    added: int = 0
    pruned: int = 0


def collect_all(client: PoliteClient, companies: list[Company], hours: int) -> list[RawItem]:
    raw: list[RawItem] = []
    for c in companies:
        for name, fn in (
            ("gdelt", gdelt.collect),
            ("gnews", google_news.collect),
            ("hn", hackernews.collect),
            ("bluesky", bluesky.collect),
        ):
            found = fn(client, c, hours)
            log.info("%-8s %-7s %4d items", c.id, name, len(found))
            raw += found
    return raw


def to_mentions(items: list[RawItem], companies: list[Company], backend: Backend) -> list[Mention]:
    by_id = {c.id: c for c in companies}
    scores = backend.score([i.text for i in items], [i.lang or "other" for i in items])
    out = []
    for item, (label, conf) in zip(items, scores, strict=True):
        out.append(
            Mention(
                id=mention_id(item.source, item.native_id),
                company=item.company,
                source=item.source,
                url=item.url,
                published_at=item.published_at.astimezone(UTC).replace(microsecond=0).isoformat(),
                lang=item.lang or "other",
                domain=item.domain,
                headline=item.title if item.source == "news" else None,
                sentiment=label,
                sentiment_score=conf,
                terms=extract_terms(item.text, item.lang or "other", by_id[item.company]),
            )
        )
    return out


def publish(summary: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if SITE_DIR.exists():
        shutil.copytree(SITE_DIR, out_dir, dirs_exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))


def run(
    companies: list[Company],
    store: Store,
    out_dir: Path,
    backend: Backend,
    hours: int = 6,
    client: PoliteClient | None = None,
    now: datetime | None = None,
) -> RunStats:
    client = client or PoliteClient(
        min_interval={gdelt.HOST: gdelt.MIN_INTERVAL, google_news.HOST: google_news.MIN_INTERVAL}
    )
    stats = RunStats()

    raw = collect_all(client, companies, hours)
    stats.collected = len(raw)
    items = clean(raw, companies, known_ids=store.known_ids(days=3, now=now))
    stats.kept = len(items)
    stats.added = store.add(to_mentions(items, companies, backend))
    stats.pruned = store.prune(now=now)

    views = {c.id: wikipedia.collect(client, c.wikipedia) for c in companies if c.wikipedia}
    if any(views.values()):
        store.save_pageviews({**store.load_pageviews(), **{k: v for k, v in views.items() if v}})

    summary = build_summary(
        companies, store.load(WINDOW_DAYS + 1, now=now), store.load_pageviews(), backend.name, now=now
    )
    publish(summary, out_dir)
    log.info("collected %d, kept %d, stored %d new, pruned %d day files", *vars(stats).values())
    return stats
