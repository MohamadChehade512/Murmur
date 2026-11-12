from murmur.sources import bluesky, gdelt, hackernews, wikipedia


def test_gdelt_parses_articles_and_skips_bad_rows():
    payload = {
        "articles": [
            {
                "url": "https://a.com/1",
                "title": " Tesla opens plant ",
                "seendate": "20261112T040000Z",
                "domain": "a.com",
            },
            {"url": "https://a.com/2", "title": "", "seendate": "20261112T040000Z"},
            {"url": "https://a.com/3", "title": "No date"},
        ]
    }
    items = gdelt.parse(payload, "tesla", "en")
    assert len(items) == 1
    assert items[0].title == "Tesla opens plant"
    assert items[0].published_at.hour == 4
    assert gdelt.parse(None, "tesla", "en") == []


def test_hackernews_uses_title_or_comment():
    payload = {
        "hits": [
            {"objectID": "9", "created_at_i": 1794454948, "title": "Tesla recall"},
            {"objectID": "10", "created_at_i": 1794454948, "comment_text": "I like my <i>Tesla</i>"},
            {"objectID": "11", "created_at_i": 1794454948},
        ]
    }
    items = hackernews.parse(payload, "tesla")
    assert [i.text for i in items] == ["Tesla recall", "I like my <i>Tesla</i>"]
    assert items[0].url == "https://news.ycombinator.com/item?id=9"


def test_bluesky_builds_post_links_and_language():
    payload = {
        "posts": [
            {
                "uri": "at://did:plc:abc/app.bsky.feed.post/3kxyz",
                "author": {"handle": "someone.bsky.social"},
                "record": {
                    "text": "طيران الإمارات رائعة",
                    "createdAt": "2026-11-12T10:00:00.000Z",
                    "langs": ["ar"],
                },
            },
            {"uri": "at://x", "author": {}, "record": {"text": "missing handle"}},
        ]
    }
    items = bluesky.parse(payload, "emirates")
    assert len(items) == 1
    assert items[0].url == "https://bsky.app/profile/someone.bsky.social/post/3kxyz"
    assert items[0].lang == "ar"


def test_wikipedia_parses_daily_views():
    payload = {"items": [{"timestamp": "2026110100", "views": 2799}]}
    assert wikipedia.parse(payload) == [{"date": "2026-11-01", "views": 2799}]
