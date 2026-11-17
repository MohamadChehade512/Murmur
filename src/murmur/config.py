"""Loads the companies Murmur follows from companies.toml.

Only `id`, `name` and `sector` are required. Everything else has a default built from the name, its
aliases and its Arabic names, so most entries stay a few lines long.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .models import Company

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "companies.toml"
# GDELT rejects very short keywords, and long OR lists slow it down.
MIN_NEWS_TERM = 3
MAX_NEWS_TERMS = 5
MAX_HEADLINE_TERMS = 3


def _quote(term: str) -> str:
    return f'"{term}"' if " " in term else term


def _or(terms: list[str], wrap: bool) -> str:
    joined = " OR ".join(_quote(t) for t in terms)
    # GDELT only allows parentheses around OR'd terms.
    return f"({joined})" if wrap and len(terms) > 1 else joined


def news_query(latin: list[str], arabic: list[str]) -> str:
    terms = [t for t in latin if len(t) >= MIN_NEWS_TERM and "&" not in t][:MAX_NEWS_TERMS] + arabic[:2]
    return _or(terms, wrap=True)


def _company(c: dict) -> Company:
    arabic = list(c.get("ar", []))
    aliases = list(c.get("aliases", [c["name"]]))
    latin = [a for a in aliases if a.isascii() and not a.startswith("@")]
    headlines = dict(c.get("headlines", {}))
    headlines.setdefault("en", _or(latin[:MAX_HEADLINE_TERMS], wrap=False))
    if arabic:
        headlines.setdefault("ar", _or(arabic[:2], wrap=False))
    return Company(
        id=c["id"],
        name=c["name"],
        color=c.get("color", "#888888"),
        aliases=tuple(dict.fromkeys(aliases + arabic)),
        news=c.get("news", news_query(latin, arabic)),
        search=tuple(c.get("search", [c["name"], *arabic[:1]])),
        wikipedia=c.get("wikipedia"),
        exclude=tuple(c.get("exclude", [])),
        headlines=headlines,
        sector=c.get("sector", ""),
        featured=bool(c.get("featured", False)),
        known_as=tuple(c.get("known_as", [])),
    )


def load_companies(path: Path = DEFAULT_PATH) -> list[Company]:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    companies = [_company(c) for c in data.get("company", [])]
    ids = [c.id for c in companies]
    if len(ids) != len(set(ids)):
        raise ValueError("company ids in companies.toml must be unique")
    return companies
