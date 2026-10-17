"""Data access and conservative, context-dependent matching for PurePersian.

No LLM calls or text rewriting are performed here. The API only proposes options.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from importlib.resources import files

_DIACRITICS = frozenset(chr(code) for code in range(0x064B, 0x0660)) | {"\u0670"}
_TRANSLATION = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه", "ـ": ""})
_GUIDANCE = (
    "پیشنهادها وابسته به بافت‌اند. هیچ جایگزینی را بدون بررسی معنی و آهنگ جمله خودکار اجرا نکنید. "
    "اصطلاح‌های فنی، نام‌های خاص، معنای تخصصی و درجهٔ قطعیت را حفظ کنید. "
    "این فرهنگ گواه قطعی دربارهٔ ریشه‌شناسی یا هم‌معنایی کامل واژه‌ها نیست."
)


def normalize(text: str) -> str:
    """Normalize common Arabic/Persian keyboard differences and diacritics."""
    text = unicodedata.normalize("NFC", text).translate(_TRANSLATION)
    text = "".join(ch for ch in text if ch not in _DIACRITICS)
    return " ".join(text.replace("\u200c", " ").casefold().split())


def _text_index(text: str) -> tuple[str, list[int]]:
    """Map normalized text positions back to original positions."""
    result: list[str] = []
    indices: list[int] = []
    for pos, char in enumerate(unicodedata.normalize("NFC", text)):
        if char in _DIACRITICS or char == "ـ":
            continue
        out = char.translate(_TRANSLATION).casefold()
        if char == "\u200c" or char.isspace():
            out = " "
        for normalized in out:
            result.append(normalized)
            indices.append(pos)
    return "".join(result), indices


@lru_cache(maxsize=1)
def catalog() -> dict:
    data = json.loads(files("purepersian_mcp").joinpath("lexicon.json").read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0.0" or not isinstance(data.get("entries"), list):
        raise ValueError("Invalid PurePersian lexicon schema")
    return data


def stats() -> dict:
    data = catalog()
    return {
        "schema_version": data["schema_version"],
        "language": data["language"],
        "entry_count": len(data["entries"]),
        "unique_term_count": len({normalize(x["term"]) for x in data["entries"]}),
        "categories": dict(Counter(x["category"] for x in data["entries"])),
        "source_of_truth": data["source_of_truth"],
        "guidance": _GUIDANCE,
    }


def categories() -> list[dict]:
    counts = Counter(row["category"] for row in catalog()["entries"])
    return [{"name": name, "count": count} for name, count in counts.items()]


def lookup(term: str) -> dict:
    needle = normalize(term)
    if not needle:
        return {"query": term, "matches": [], "guidance": _GUIDANCE}
    exact = [row for row in catalog()["entries"] if normalize(row["term"]) == needle]
    # Reverse lookups are deliberately labelled, not misrepresented as synonyms.
    reverse = [
        row for row in catalog()["entries"]
        if normalize(row["term"]) != needle
        and any(normalize(word) == needle for word in row["equivalents"])
    ]
    return {
        "query": term,
        "matches": [{**row, "matched_on": "term"} for row in exact]
        + [{**row, "matched_on": "equivalent_reverse"} for row in reverse],
        "guidance": _GUIDANCE,
    }


def search(query: str, limit: int = 10, category: str = "") -> dict:
    needle = normalize(query)
    if not needle:
        return {"query": query, "total": 0, "results": [], "guidance": _GUIDANCE}
    category_n = normalize(category) if category else ""
    scored: list[tuple[int, dict]] = []
    for row in catalog()["entries"]:
        if category_n and category_n not in normalize(row["category"]):
            continue
        term = normalize(row["term"])
        equivalents = [normalize(x) for x in row["equivalents"]]
        english = normalize(row["english"])
        if needle == term:
            score = 100
        elif needle in equivalents:
            score = 95
        elif term.startswith(needle) or any(x.startswith(needle) for x in equivalents):
            score = 85
        elif needle in term or any(needle in x for x in equivalents):
            score = 75
        elif needle in english:
            score = 60
        elif needle in normalize(row["usage"]):
            score = 25
        else:
            continue
        scored.append((score, row))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["term"], pair[1]["id"]))
    return {
        "query": query,
        "total": len(scored),
        "results": [{**row, "match_score": score} for score, row in scored[:max(1, min(50, limit))]],
        "guidance": _GUIDANCE,
    }


def inspect(text: str, limit: int = 20) -> dict:
    """Identify *candidate* matches, never rewrite or claim to infer context."""
    if len(text) > 8000:
        raise ValueError("Input text exceeds 8000 characters")
    indexed, pos_map = _text_index(text)
    candidates: list[tuple[int, int, dict]] = []
    for row in catalog()["entries"]:
        term = normalize(row["term"])
        if not term:
            continue
        pattern = r"(?<!\w)" + re.escape(term).replace(r"\ ", r" +") + r"(?!\w)"
        for match in re.finditer(pattern, indexed):
            start = pos_map[match.start()]
            end = pos_map[match.end() - 1] + 1
            while end < len(text) and text[end] in _DIACRITICS:
                end += 1
            candidates.append((start, end, row))

    # Prefer long expressions over substrings, but keep distinct senses
    # when the same source term appears in more than one category.
    candidates.sort(key=lambda item: (item[0], -(item[1] - item[0]), item[2]["id"]))
    result: list[dict] = []
    spans: list[tuple[int, int]] = []
    for start, end, row in candidates:
        if any(a < end and start < b and (start, end) != (a, b) for a, b in spans):
            continue
        if (start, end) not in spans:
            spans.append((start, end))
        result.append({
            "start": start,
            "end": end,
            "original": text[start:end],
            "term": row["term"],
            "equivalents": row["equivalents"],
            "usage": row["usage"],
            "category": row["category"],
            "source": row["source"],
            "review_status": row["review_status"],
            "requires_context_review": True,
        })
        if len(result) >= max(1, min(50, limit)):
            break
    return {
        "matches": result,
        "match_count": len(result),
        "auto_rewritten": False,
        "guidance": _GUIDANCE,
    }


def guide() -> str:
    return (
        "# PurePersian — agent usage policy\n"
        "1. Use lookup_term for exact or reverse lookups; use search_terms for discovery.\n"
        "2. inspect_text returns possible matches, NOT a rewritten sentence.\n"
        "3. Preserve meaning, tense, modality, register, and specialist terminology.\n"
        "4. Explain ambiguous alternatives and ask when context is essential.\n"
        "5. Treat legacy items as unverified proposals; never label all entries fully synonymous.\n"
        "6. Keep proper names, user quotations, and code identifiers intact unless explicitly asked.\n"
        "7. Always attribute an entry to the relevant source (.tex) when presenting it.\n"
    )
