from datetime import timedelta

from murmur.pipeline import ROTATION_GROUPS, pick


def test_featured_every_run_and_everyone_once_per_cycle(companies, now):
    featured = {c.id for c in companies if c.featured}
    seen = set()
    for h in range(ROTATION_GROUPS):
        chosen = {c.id for c in pick(companies, now + timedelta(hours=h))}
        assert featured <= chosen
        assert len(chosen) <= len(featured) + len(companies) // ROTATION_GROUPS + 1
        seen |= chosen
    assert seen == {c.id for c in companies}


def test_everyone_flag_collects_all(companies, now):
    assert pick(companies, now, everyone=True) == companies
