"""Extracts the words and short phrases people use about a company."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable

from .models import Company
from .stopwords import ARABIC, ENGLISH
from .text import fold, normalize_arabic, surface

_TOKEN = re.compile(r"[^\W\d_][\w'’-]*", re.UNICODE)
_POSSESSIVE = re.compile(r"['’]s$")
MAX_TERMS_PER_MENTION = 12
_ARABIC_STOP = {normalize_arabic(w) for w in ARABIC}


def _company_words(company: Company) -> set[str]:
    words = {company.name.casefold(), company.id}
    for alias in company.aliases:
        words.update(fold(alias).split())
    return words


def _keep(token: str, lang: str, exclude: set[str]) -> bool:
    key = fold(token)
    if key in exclude:
        return False
    if lang == "ar":
        # Arabic attaches "ال" (the) and "و" (and); check the bare word too.
        bare = key[2:] if key.startswith("ال") else key
        return len(bare) >= 3 and key not in _ARABIC_STOP and bare not in _ARABIC_STOP
    return len(key) >= 3 and key not in ENGLISH


def extract_terms(text: str, lang: str, company: Company) -> list[str]:
    """Unique terms in one text: single words plus two-word phrases of adjacent kept words."""
    exclude = _company_words(company)
    tokens = [_POSSESSIVE.sub("", surface(t)).strip("'’-") for t in _TOKEN.findall(text)]
    keep = [_keep(t, lang, exclude) for t in tokens]
    terms: list[str] = []
    for i, t in enumerate(tokens):
        if not keep[i]:
            continue
        terms.append(t)
        if i + 1 < len(tokens) and keep[i + 1]:
            terms.append(f"{t} {tokens[i + 1]}")
    return list(dict.fromkeys(terms))[: MAX_TERMS_PER_MENTION * 2]


def top_terms(term_lists: Iterable[list[str]], limit: int = 12, min_docs: int = 2) -> list[tuple[str, int]]:
    """Ranks terms by how many mentions use them. A phrase hides the single words inside it.

    Spelling variants (أبل / ابل) count as one term, shown in their most common spelling.
    """
    df: Counter[str] = Counter()
    spellings: dict[str, Counter[str]] = {}
    for terms in term_lists:
        keys = {}
        for t in terms:
            keys.setdefault(fold(t), t)
        df.update(keys.keys())
        for key, t in keys.items():
            spellings.setdefault(key, Counter())[t] += 1
    ranked = sorted(
        ((t, n) for t, n in df.items() if n >= min_docs),
        key=lambda tn: (-(tn[1] * (1.5 if " " in tn[0] else 1)), tn[0]),
    )
    chosen: list[tuple[str, int]] = []
    covered: set[str] = set()
    for term, n in ranked:
        if " " not in term and term in covered:
            continue
        if " " in term:
            covered.update(term.split())
        chosen.append((spellings[term].most_common(1)[0][0], n))
        if len(chosen) == limit:
            break
    return chosen
