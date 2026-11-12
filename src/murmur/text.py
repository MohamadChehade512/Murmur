"""Text helpers shared by cleaning and keyword extraction (English and Arabic)."""

from __future__ import annotations

import html
import re
import unicodedata

_TAG = re.compile(r"<[^>]+>")
_URL = re.compile(r"https?://\S+|www\.\S+")
_WS = re.compile(r"\s+")
_ARABIC = re.compile(r"[؀-ۿ]")
_LATIN = re.compile(r"[A-Za-z]")
_DIACRITICS = re.compile(r"[ً-ْـ]")  # harakat and tatweel


def strip_html(text: str) -> str:
    text = _TAG.sub(" ", text.replace("<p>", "\n"))
    return _WS.sub(" ", html.unescape(text)).strip()


def remove_urls(text: str) -> str:
    return _URL.sub(" ", text)


def normalize_arabic(text: str) -> str:
    """Folds common spelling variants so the same word counts once."""
    text = _DIACRITICS.sub("", text)
    text = re.sub("[إأآا]", "ا", text)
    return text.replace("ى", "ي").replace("ة", "ه")


def detect_lang(text: str) -> str:
    """Script-based guess: good enough to split English from Arabic."""
    arabic, latin = len(_ARABIC.findall(text)), len(_LATIN.findall(text))
    if arabic and arabic >= latin * 0.5:
        return "ar"
    if latin:
        return "en"
    return "other"


def fold(text: str) -> str:
    """Matching key: case-folded, with Arabic spelling variants folded together."""
    return unicodedata.normalize("NFKC", normalize_arabic(text)).casefold()


def surface(text: str) -> str:
    """Display form: case-folded, Arabic diacritics removed, but real spelling kept."""
    return unicodedata.normalize("NFKC", _DIACRITICS.sub("", text)).casefold()
