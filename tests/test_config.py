from murmur.config import load_companies


def test_loads_three_companies_with_queries(companies):
    assert [c.id for c in companies] == ["apple", "tesla", "emirates"]
    for c in companies:
        assert c.aliases and c.search and c.news


def test_rejects_duplicate_ids(tmp_path):
    p = tmp_path / "c.toml"
    entry = '[[company]]\nid = "x"\nname = "X"\naliases = ["X"]\n'
    p.write_text(entry * 2)
    try:
        load_companies(p)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
