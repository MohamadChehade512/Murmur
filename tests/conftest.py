from datetime import UTC, datetime
from pathlib import Path

import pytest

from murmur.config import load_companies
from murmur.models import RawItem

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 11, 12, 15, 30, tzinfo=UTC)


@pytest.fixture
def companies():
    return load_companies(ROOT / "companies.toml")


@pytest.fixture
def now():
    return NOW


def raw(company="tesla", text="Tesla deliveries beat expectations this quarter", source="hn", nid="1", **kw):
    return RawItem(
        source=source,
        company=company,
        native_id=nid,
        url=f"https://example.com/{nid}",
        published_at=kw.pop("published_at", NOW),
        text=text,
        **kw,
    )
