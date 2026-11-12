from datetime import UTC, datetime

from conftest import raw

from murmur.clean import clean
from murmur.sources import google_news

FEED = """<?xml version="1.0"?><rss><channel>
<item><title>Emirates Airline Profit Falls After Disruption - WSJ</title>
  <link>https://news.google.com/rss/articles/abc</link><guid>abc</guid>
  <pubDate>Thu, 12 Nov 2026 03:08:14 GMT</pubDate><source url="https://www.wsj.com">WSJ</source></item>
<item><title>Old story - Paper</title><link>https://news.google.com/rss/articles/old</link>
  <pubDate>Mon, 02 Nov 2026 03:08:14 GMT</pubDate><source url="https://paper.com">Paper</source></item>
<item><title></title><link>x</link></item>
</channel></rss>"""


def test_parses_headlines_and_drops_publisher_suffix():
    items = google_news.parse(FEED, "emirates", "en", since=datetime(2026, 11, 11, tzinfo=UTC))
    assert len(items) == 1
    assert items[0].title == "Emirates Airline Profit Falls After Disruption"
    assert items[0].domain == "wsj.com" and items[0].lang == "en"


def test_bad_feed_is_ignored():
    assert google_news.parse("<not xml", "emirates", "en") == []
    assert google_news.parse(None, "emirates", "en") == []


def test_news_headlines_skip_the_name_check_but_posts_do_not(companies):
    news = raw(company="emirates", source="news", nid="n1", text="دبي تتصدر مطارات العالم في رحلات A380")
    post = raw(company="emirates", source="bluesky", nid="p1", text="Dubai airport is busy again this week")
    assert [i.native_id for i in clean([news, post], companies)] == ["n1"]
