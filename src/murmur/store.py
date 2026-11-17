"""Rolling storage: gzipped JSON Lines, one folder per day, kept for a fixed window.

Each run writes its new mentions to its own small file inside the day's folder
(`mentions/2026-11-16/131702.jsonl.gz`) instead of rewriting the day. On the `data` branch that
means every commit only adds the new data, so git history grows slowly; a weekly job squashes it.
Older single-file days (`mentions/2026-11-12.jsonl.gz`) are still read.
"""

from __future__ import annotations

import gzip
import json
import shutil
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from .models import Mention

KEEP_DAYS = 30


class Store:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.mentions_dir = self.root / "mentions"
        self.mentions_dir.mkdir(parents=True, exist_ok=True)

    # ---------- mentions ----------
    def _day_files(self, day: date) -> list[Path]:
        legacy = self.mentions_dir / f"{day.isoformat()}.jsonl.gz"
        folder = self.mentions_dir / day.isoformat()
        parts = sorted(folder.glob("*.jsonl.gz")) if folder.is_dir() else []
        return ([legacy] if legacy.exists() else []) + parts

    def _read(self, path: Path) -> list[Mention]:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return [Mention.from_dict(json.loads(line)) for line in f if line.strip()]

    def _write(self, path: Path, mentions: list[Mention]) -> None:
        mentions = sorted(mentions, key=lambda m: (m.published_at, m.id))
        path.parent.mkdir(parents=True, exist_ok=True)
        # mtime=0 keeps the gzip bytes stable for the same content.
        with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
            for m in mentions:
                gz.write((json.dumps(m.to_dict(), ensure_ascii=False, sort_keys=True) + "\n").encode())

    def load(self, days: int, now: datetime | None = None) -> list[Mention]:
        today = (now or datetime.now(UTC)).date()
        seen: dict[str, Mention] = {}
        for i in range(days):
            for path in self._day_files(today - timedelta(days=i)):
                for m in self._read(path):
                    seen.setdefault(m.id, m)
        return list(seen.values())

    def known_ids(self, days: int = 3, now: datetime | None = None) -> set[str]:
        return {m.id for m in self.load(days, now)}

    def add(self, mentions: list[Mention], now: datetime | None = None) -> int:
        """Writes mentions not already stored to this run's file in each day folder. Returns how many."""
        stamp = (now or datetime.now(UTC)).strftime("%H%M%S")
        by_day: dict[date, list[Mention]] = defaultdict(list)
        for m in mentions:
            by_day[datetime.fromisoformat(m.published_at).date()].append(m)
        added = 0
        for day, batch in by_day.items():
            known = {m.id for path in self._day_files(day) for m in self._read(path)}
            new = list({m.id: m for m in batch if m.id not in known}.values())
            if not new:
                continue
            folder = self.mentions_dir / day.isoformat()
            path, n = folder / f"{stamp}.jsonl.gz", 1
            while path.exists():
                path, n = folder / f"{stamp}-{n}.jsonl.gz", n + 1
            self._write(path, new)
            added += len(new)
        return added

    def prune(self, keep_days: int = KEEP_DAYS, now: datetime | None = None) -> int:
        """Removes days older than the window. Returns how many days were removed."""
        cutoff = (now or datetime.now(UTC)).date() - timedelta(days=keep_days)
        removed = 0
        for path in self.mentions_dir.iterdir():
            try:
                day = date.fromisoformat(path.name.split(".")[0])
            except ValueError:
                continue
            if day < cutoff:
                shutil.rmtree(path) if path.is_dir() else path.unlink()
                removed += 1
        return removed

    # ---------- page views ----------
    def save_pageviews(self, data: dict[str, list[dict]]) -> None:
        (self.root / "pageviews.json").write_text(json.dumps(data, indent=1, sort_keys=True))

    def load_pageviews(self) -> dict[str, list[dict]]:
        path = self.root / "pageviews.json"
        return json.loads(path.read_text()) if path.exists() else {}
