"""One full run: collect, clean, score, store, summarise, publish."""

from __future__ import annotations

import json
import logging
import math
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .aggregate import WINDOW_DAYS, build_outputs
from .clean import clean
from .http import PoliteClient
from .keywords import extract_terms
from .models import Company, Mention, RawItem, mention_id
from .sentiment import Backend
from .sources import bluesky, gdelt, google_news, hackernews, wikipedia
from .store import Store

log = logging.getLogger(__name__)
# Featured companies are collected every run. Of the rest, the quarter collected longest ago go next,
# so every company comes round in about four runs however often GitHub actually runs the schedule.
ROTATION_GROUPS = 4
# Each company looks back to its last collection (plus a margin), within these bounds.
FIRST_LOOKBACK_HOURS = 24
MAX_LOOKBACK_HOURS = 48
SITE_DIR = Path(__file__).resolve().parents[2] / "site"


@dataclass
class RunStats:
    collected: int = 0
    kept: int = 0
    added: int = 0
    pruned: int = 0


def pick(companies: list[Company], last: dict[str, str], everyone: bool = False) -> list[Company]:
    """The companies to collect this run: all featured ones plus the least recently collected quarter."""
    if everyone:
        return companies
    rotating = sorted((c for c in companies if not c.featured), key=lambda c: last.get(c.id, ""))
    batch = math.ceil(len(rotating) / ROTATION_GROUPS)
    return [c for c in companies if c.featured] + rotating[:batch]


def lookback(company: Company, last: dict[str, str], now: datetime, minimum: int) -> int:
    """Hours back to search: since the last collection plus an hour, never less than `minimum`."""
    if company.id not in last:
        return max(minimum, FIRST_LOOKBACK_HOURS)
    since = (now - datetime.fromisoformat(last[company.id])).total_seconds() / 3600
    return min(MAX_LOOKBACK_HOURS, max(minimum, math.ceil(since) + 1))


def collect_all(client: PoliteClient, companies: list[Company], hours: dict[str, int]) -> list[RawItem]:
    raw: list[RawItem] = []
    for c in companies:
        for name, fn in (
            ("gdelt", gdelt.collect),
            ("gnews", google_news.collect),
            ("hn", hackernews.collect),
            ("bluesky", bluesky.collect),
        ):
            found = fn(client, c, hours[c.id])
            log.info("%-8s %-7s %4d items (%dh)", c.id, name, len(found), hours[c.id])
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


def publish(files: dict[str, dict], out_dir: Path) -> None:
    """Copies the dashboard into `out_dir` and writes each JSON file at its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if SITE_DIR.exists():
        shutil.copytree(SITE_DIR, out_dir, dirs_exist_ok=True)
    shutil.rmtree(out_dir / "companies", ignore_errors=True)  # drop companies no longer followed
    for rel, data in files.items():
        path = out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))


def run(
    companies: list[Company],
    store: Store,
    out_dir: Path,
    backend: Backend,
    hours: int = 6,
    client: PoliteClient | None = None,
    now: datetime | None = None,
    everyone: bool = False,
) -> RunStats:
    client = client or PoliteClient(
        min_interval={gdelt.HOST: gdelt.MIN_INTERVAL, google_news.HOST: google_news.MIN_INTERVAL}
    )
    stats = RunStats()

    started = now or datetime.now(UTC)
    last = store.load_collected()
    chosen = pick(companies, last, everyone)
    log.info("collecting %d of %d companies", len(chosen), len(companies))
    raw = collect_all(client, chosen, {c.id: lookback(c, last, started, hours) for c in chosen})
    stats.collected = len(raw)
    items = clean(raw, companies, known_ids=store.known_ids(days=3, now=now))
    stats.kept = len(items)
    stats.added = store.add(to_mentions(items, companies, backend), now=now)
    stats.pruned = store.prune(now=now)
    stamp = started.replace(microsecond=0).isoformat()
    store.save_collected({**last, **{c.id: stamp for c in chosen}})

    views = {c.id: wikipedia.collect(client, c.wikipedia) for c in chosen if c.wikipedia}
    if any(views.values()):
        store.save_pageviews({**store.load_pageviews(), **{k: v for k, v in views.items() if v}})

    files = build_outputs(
        companies, store.load(WINDOW_DAYS + 1, now=now), store.load_pageviews(), backend.name, now=now
    )
    publish(files, out_dir)
    log.info("collected %d, kept %d, stored %d new, pruned %d day files", *vars(stats).values())
    return stats
