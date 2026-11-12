from conftest import raw

from murmur.clean import clean
from murmur.models import mention_id
from murmur.text import detect_lang, normalize_arabic, strip_html


def test_strip_html_and_entities():
    assert strip_html("I &amp; my <i>Tesla</i><p>again") == "I & my Tesla again"


def test_detects_arabic_and_english():
    assert detect_lang("طيران الإمارات تعلن رحلات جديدة") == "ar"
    assert detect_lang("Emirates airline adds flights") == "en"
    assert normalize_arabic("أبل") == normalize_arabic("ابل")


def test_drops_off_topic_spam_and_duplicates(companies):
    items = [
        raw(nid="1", text="Tesla deliveries beat expectations this quarter"),
        raw(nid="2", text="Nikola Tesla was an inventor"),  # still mentions Tesla: kept (word match)
        raw(nid="3", text="Ford earnings are out today and look fine"),  # no alias
        raw(nid="4", text="Tesla deliveries beat expectations this quarter"),  # same text, other id
        raw(nid="5", text="#tesla #ev #cars #musk #stock #buy #now #moon Tesla"),  # hashtag spam
        raw(nid="1", text="Tesla deliveries beat expectations this quarter"),  # same id
    ]
    kept = clean(items, companies)
    assert [i.native_id for i in kept] == ["1", "2"]


def test_skips_already_stored_ids(companies):
    items = [raw(nid="7", text="Tesla stock jumps after earnings call")]
    assert clean(items, companies, known_ids={mention_id("hn", "7")}) == []


def test_matches_arabic_alias_with_prefix(companies):
    items = [raw(company="emirates", nid="8", text="رحلة جديدة مع وطيران الإمارات إلى تورنتو", lang=None)]
    kept = clean(items, companies)
    assert len(kept) == 1 and kept[0].lang == "ar"


def test_word_boundary_for_latin_aliases(companies):
    items = [raw(company="apple", nid="9", text="Pineapple pizza is the best thing ever")]
    assert clean(items, companies) == []
