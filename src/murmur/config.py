"""Loads the companies Murmur follows from companies.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path

from .models import Company

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "companies.toml"


def load_companies(path: Path = DEFAULT_PATH) -> list[Company]:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    companies = []
    for c in data.get("company", []):
        companies.append(
            Company(
                id=c["id"],
                name=c["name"],
                color=c.get("color", "#888888"),
                aliases=tuple(c["aliases"]),
                news=c.get("news", ""),
                search=tuple(c.get("search", [])),
                wikipedia=c.get("wikipedia"),
                exclude=tuple(c.get("exclude", [])),
                headlines=dict(c.get("headlines", {})),
            )
        )
    ids = [c.id for c in companies]
    if len(ids) != len(set(ids)):
        raise ValueError("company ids in companies.toml must be unique")
    return companies
