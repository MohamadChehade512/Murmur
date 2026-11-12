"""Rolling storage: one gzipped JSON Lines file per day, kept for a fixed window.

In production the `data/` folder is a checkout of the repo's `data` branch, so history lives in git
without cluttering the main branch.
"""

from __future__ import annotations

import gzip
import json
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
    def _file(self, day: date) -> Path:
        return self.mentions_dir / f"{day.isoformat()}.jsonl.gz"

    def _read(self, path: Path) -> list[Mention]:
        if not path.exists():
            return []
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return [Mention.from_dict(json.loads(line)) for line in f if line.strip()]

    def _write(self, path: Path, mentions: list[Mention]) -> None:
        mentions = sorted(mentions, key=lambda m: (m.published_at, m.id))
        # mtime=0 keeps the gzip bytes stable, so unchanged days don't create git diffs.
        with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
            for m in mentions:
                gz.write((json.dumps(m.to_dict(), ensure_ascii=False, sort_keys=True) + "\n").encode())

    def load(self, days: int, now: datetime | None = None) -> list[Mention]:
        today = (now or datetime.now(UTC)).date()
        out: list[Mention] = []
        for i in range(days):
            out += self._read(self._file(today - timedelta(days=i)))
        return out

    def known_ids(self, days: int = 3, now: datetime | None = None) -> set[str]:
        return {m.id for m in self.load(days, now)}

    def add(self, mentions: list[Mention]) -> int:
        """Merges new mentions into their day files. Returns how many were actually new."""
        by_day: dict[date, list[Mention]] = defaultdict(list)
        for m in mentions:
            by_day[datetime.fromisoformat(m.published_at).date()].append(m)
        added = 0
        for day, new in by_day.items():
            path = self._file(day)
            existing = {m.id: m for m in self._read(path)}
            for m in new:
                if m.id not in existing:
                    existing[m.id] = m
                    added += 1
            self._write(path, list(existing.values()))
        return added

    def prune(self, keep_days: int = KEEP_DAYS, now: datetime | None = None) -> int:
        cutoff = (now or datetime.now(UTC)).date() - timedelta(days=keep_days)
        removed = 0
        for path in self.mentions_dir.glob("*.jsonl.gz"):
            try:
                day = date.fromisoformat(path.name.split(".")[0])
            except ValueError:
                continue
            if day < cutoff:
                path.unlink()
                removed += 1
        return removed

    # ---------- page views ----------
    def save_pageviews(self, data: dict[str, list[dict]]) -> None:
        (self.root / "pageviews.json").write_text(json.dumps(data, indent=1, sort_keys=True))

    def load_pageviews(self) -> dict[str, list[dict]]:
        path = self.root / "pageviews.json"
        return json.loads(path.read_text()) if path.exists() else {}
