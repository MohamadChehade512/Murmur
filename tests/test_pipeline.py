from datetime import timedelta

from murmur.pipeline import FIRST_LOOKBACK_HOURS, MAX_LOOKBACK_HOURS, ROTATION_GROUPS, lookback, pick


def test_featured_every_run_and_everyone_within_a_cycle(companies, now):
    featured = {c.id for c in companies if c.featured}
    last: dict[str, str] = {}
    seen = set()
    for run in range(ROTATION_GROUPS):
        chosen = pick(companies, last)
        ids = {c.id for c in chosen}
        assert featured <= ids
        assert len(ids) <= len(featured) + len(companies) // ROTATION_GROUPS + 1
        seen |= ids
        stamp = (now + timedelta(hours=run * 9)).isoformat()  # runs needn't be hourly
        last.update({c.id: stamp for c in chosen})
    assert seen == {c.id for c in companies}


def test_least_recently_collected_go_first(companies, now):
    old = {c.id: now.isoformat() for c in companies}
    old["nvidia"] = (now - timedelta(days=2)).isoformat()
    old.pop("shopify")  # never collected sorts first of all
    ids = [c.id for c in pick(companies, old)]
    assert ids.index("shopify") < ids.index("nvidia")


def test_everyone_flag_collects_all(companies):
    assert pick(companies, {}, everyone=True) == companies


def test_lookback_covers_the_gap_since_last_collection(companies, now):
    c = companies[0]
    assert lookback(c, {}, now, 6) == FIRST_LOOKBACK_HOURS
    assert lookback(c, {c.id: (now - timedelta(hours=1)).isoformat()}, now, 6) == 6
    assert lookback(c, {c.id: (now - timedelta(hours=9, minutes=10)).isoformat()}, now, 6) == 11
    assert lookback(c, {c.id: (now - timedelta(days=5)).isoformat()}, now, 6) == MAX_LOOKBACK_HOURS
