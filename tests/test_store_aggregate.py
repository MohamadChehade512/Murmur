import json
from datetime import timedelta

from murmur.aggregate import build_summary
from murmur.models import Mention
from murmur.pipeline import publish
from murmur.store import Store


def m(i, company="tesla", when=None, lang="en", sentiment="positive", source="hn", terms=None, headline=None):
    return Mention(
        id=f"id{i}",
        company=company,
        source=source,
        url=f"https://x/{i}",
        published_at=when.isoformat(),
        lang=lang,
        sentiment=sentiment,
        terms=terms or [],
        headline=headline,
    )


def test_store_merges_by_day_and_prunes(tmp_path, now):
    store = Store(tmp_path)
    assert store.add([m(1, when=now), m(2, when=now - timedelta(days=1))]) == 2
    assert store.add([m(1, when=now)]) == 0
    assert {x.id for x in store.load(2, now=now)} == {"id1", "id2"}
    store.add([m(3, when=now - timedelta(days=40))])
    assert store.prune(keep_days=30, now=now) == 1


def test_summary_shape_and_numbers(companies, now):
    mentions = [
        m(1, when=now - timedelta(hours=1), terms=["battery range"]),
        m(2, when=now - timedelta(hours=2), sentiment="negative", terms=["battery range"]),
        m(3, when=now - timedelta(days=2), lang="ar", sentiment=None),
        m(4, when=now - timedelta(hours=3), source="news", headline="Tesla opens plant"),
        m(5, when=now - timedelta(days=20)),  # outside the 7-day window
        m(6, company="apple", when=now, sentiment="neutral"),
    ]
    pageviews = {"tesla": [{"date": now.date().isoformat(), "views": 1200}]}
    s = build_summary(companies, mentions, pageviews, "lexicon", now=now)

    assert s["version"] == 1 and len(s["companies"]) == 3
    tesla = next(c for c in s["companies"] if c["id"] == "tesla")
    assert tesla["totals"]["mentions"] == 4
    assert tesla["totals"]["by_lang"] == {"en": 3, "ar": 1, "other": 0}
    assert tesla["sentiment"]["scored"] == 3
    assert tesla["sentiment"]["net"] == round((2 - 1) / 3, 3)
    assert len(tesla["daily"]) == 7 and tesla["daily"][-1]["pageviews"] == 1200
    assert len(tesla["hourly"]) == 48
    assert tesla["top_terms"]["en"] == [{"term": "battery range", "count": 2}]
    assert tesla["headlines"][0]["title"] == "Tesla opens plant"


def test_publish_writes_summary(tmp_path, companies, now):
    publish(build_summary(companies, [], {}, "lexicon", now=now), tmp_path)
    data = json.loads((tmp_path / "summary.json").read_text())
    assert data["companies"][0]["totals"]["mentions"] == 0
