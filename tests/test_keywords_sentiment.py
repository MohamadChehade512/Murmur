from murmur.keywords import extract_terms, top_terms
from murmur.sentiment import get_backend


def test_extracts_words_and_phrases_without_stopwords_or_company(companies):
    tesla = companies[1]
    terms = extract_terms("Tesla's battery range is impressive, battery range matters", "en", tesla)
    assert "battery range" in terms
    assert "tesla" not in terms and "tesla's" not in terms and "the" not in terms


def test_arabic_terms_skip_stopwords(companies):
    emirates = companies[2]
    terms = extract_terms("طيران الإمارات تطلق رحلات جديدة إلى تورنتو", "ar", emirates)
    assert "رحلات" in terms
    assert "الي" not in terms and "إلى" not in terms


def test_arabic_spelling_variants_count_once_and_keep_real_spelling():
    docs = [["أمنية"], ["أمنية"], ["امنيه"]]
    assert top_terms(docs, limit=3) == [("أمنية", 3)]


def test_top_terms_prefers_phrases_and_needs_two_mentions():
    docs = [["battery", "range", "battery range"], ["battery", "range", "battery range"], ["recall"]]
    assert top_terms(docs, limit=5) == [("battery range", 2)]


def test_lexicon_scores_english_and_skips_arabic():
    backend = get_backend("lexicon")
    scores = backend.score(
        ["I love this, it is great", "This is terrible and awful", "مرحبا"], ["en", "en", "ar"]
    )
    assert scores[0][0] == "positive"
    assert scores[1][0] == "negative"
    assert scores[2] == (None, None)


def test_model_backend_falls_back_when_unavailable(monkeypatch):
    import murmur.sentiment as s

    def boom(*a, **k):
        raise ImportError("no transformers")

    monkeypatch.setattr(s, "ModelBackend", boom)
    assert s.get_backend("model").name == "lexicon"
