"""Sentiment scoring with two interchangeable backends.

- "lexicon": VADER, English only, tiny and fast. Used in tests and as a fallback.
- "model":   a multilingual transformer that reads English and Arabic. Used by the scheduled run.

Both return (label, confidence) per text, or (None, None) when a text can't be scored.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from typing import Protocol

from .models import Label

log = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get(
    "MURMUR_SENTIMENT_MODEL", "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
)
Score = tuple[Label | None, float | None]


class Backend(Protocol):
    name: str

    def score(self, texts: Sequence[str], langs: Sequence[str]) -> list[Score]: ...


class LexiconBackend:
    name = "lexicon"

    def __init__(self) -> None:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        self._vader = SentimentIntensityAnalyzer()

    def score(self, texts: Sequence[str], langs: Sequence[str]) -> list[Score]:
        out: list[Score] = []
        for text, lang in zip(texts, langs, strict=True):
            if lang != "en":
                out.append((None, None))
                continue
            c = self._vader.polarity_scores(text)["compound"]
            label: Label = "positive" if c >= 0.05 else "negative" if c <= -0.05 else "neutral"
            out.append((label, round(abs(c), 3)))
        return out


class ModelBackend:
    name = "model"

    def __init__(self, model: str = DEFAULT_MODEL, batch_size: int = 32) -> None:
        from transformers import pipeline

        self._clf = pipeline("text-classification", model=model, truncation=True, max_length=256)
        self._batch = batch_size

    def score(self, texts: Sequence[str], langs: Sequence[str]) -> list[Score]:
        if not texts:
            return []
        results = self._clf(list(texts), batch_size=self._batch)
        out: list[Score] = []
        for r in results:
            label = str(r["label"]).lower()
            if label not in ("positive", "neutral", "negative"):
                out.append((None, None))
            else:
                out.append((label, round(float(r["score"]), 3)))  # type: ignore[arg-type]
        return out


def get_backend(name: str = "lexicon") -> Backend:
    if name == "model":
        try:
            return ModelBackend()
        except Exception as exc:  # missing extras, download failure, etc.
            log.warning("Sentiment model unavailable (%s); falling back to the lexicon.", exc)
    return LexiconBackend()
