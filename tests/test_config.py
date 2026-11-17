from murmur.config import load_companies, news_query


def test_loads_companies_with_queries(companies):
    ids = [c.id for c in companies]
    assert ids[:3] == ["apple", "tesla", "emirates"]
    for c in companies:
        assert c.aliases and c.search and c.news and c.headlines.get("en"), c.id
        assert "&" not in c.news, c.id


def test_defaults_come_from_name_and_arabic_names(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('[[company]]\nid = "x"\nname = "Xylo"\nsector = "Tech"\nar = ["زايلو"]\n')
    (c,) = load_companies(p)
    assert c.aliases == ("Xylo", "زايلو")
    assert c.search == ("Xylo", "زايلو")
    assert c.news == "(Xylo OR زايلو)"
    assert c.headlines == {"en": "Xylo", "ar": "زايلو"}
    assert not c.featured


def test_news_query_quotes_phrases_and_skips_short_terms():
    assert news_query(["EY", "Ernst Young"], []) == '"Ernst Young"'
    assert news_query(["Nvidia", "Jensen Huang"], []) == '(Nvidia OR "Jensen Huang")'


def test_rejects_duplicate_ids(tmp_path):
    p = tmp_path / "c.toml"
    entry = '[[company]]\nid = "x"\nname = "X"\naliases = ["X"]\n'
    p.write_text(entry * 2)
    try:
        load_companies(p)
    except ValueError:
        return
    raise AssertionError("expected ValueError")
