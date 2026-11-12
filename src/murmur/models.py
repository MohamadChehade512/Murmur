"""Core data types shared across the pipeline."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Literal

Source = Literal["news", "hn", "bluesky"]
Label = Literal["positive", "neutral", "negative"]


@dataclass(frozen=True)
class Company:
    id: str
    name: str
    color: str
    aliases: tuple[str, ...]
    news: str
    search: tuple[str, ...]
    wikipedia: str | None = None
    exclude: tuple[str, ...] = ()


@dataclass
class RawItem:
    """One item as a collector found it, before cleaning. Text is kept in memory only."""

    source: Source
    company: str
    native_id: str
    url: str
    published_at: datetime
    text: str
    title: str | None = None
    domain: str | None = None
    lang: str | None = None


@dataclass
class Mention:
    """A cleaned, scored mention as stored on the data branch.

    We keep links, scores and extracted terms, not copies of people's posts.
    `headline` is only set for news articles.
    """

    id: str
    company: str
    source: Source
    url: str
    published_at: str  # ISO 8601, UTC
    lang: str
    domain: str | None = None
    headline: str | None = None
    sentiment: Label | None = None
    sentiment_score: float | None = None
    terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> Mention:
        return cls(**d)


def mention_id(source: str, native_id: str) -> str:
    return hashlib.sha1(f"{source}:{native_id}".encode()).hexdigest()[:16]
