"""Rule-based question filters (Phase 2). The embedding-based filters live in the script."""
from __future__ import annotations

import re
from collections import Counter

STOPWORDS = frozenset("""a an the of in on at to for from by with and or is are was were be been do does did
how what which who whom whose when where why can could should would will i my me we our you your it its this
that these those as if then than so not no into out up about over use using used any some there their""".split())

CONTEXT_REFERENCES = re.compile(
    r"\b(the (above|following|given) (passage|text|code|example|section|document)|"
    r"(this|that|the) (passage|text|section|document|snippet|excerpt|article)|"
    r"in the (passage|text|example above)|according to the (passage|text|documentation provided))\b",
    re.I,
)


def normalise(q: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", q.lower())).strip()


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def content_words(q: str) -> list[str]:
    return [w for w in words(q) if w not in STOPWORDS]


def longest_common_run(question: str, passage: str) -> int:
    """Length (in words) of the longest word sequence shared by question and passage."""
    q, p = words(question), words(passage)
    if not q or not p:
        return 0
    # DP over word positions: O(len(q) * len(p)), fine for short texts
    best, prev = 0, [0] * (len(p) + 1)
    for i in range(1, len(q) + 1):
        cur = [0] * (len(p) + 1)
        for j in range(1, len(p) + 1):
            if q[i - 1] == p[j - 1]:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


def basic_reject_reason(q: str, passage: str, min_words: int, max_copy: int) -> str | None:
    """Return why a question should be dropped, or None if it passes the cheap rules."""
    if not q.endswith("?") and len(words(q)) < 8:
        return "not_a_question"
    if len(words(q)) < min_words:
        return "too_short"
    if len(content_words(q)) < 3:
        return "too_generic"
    if CONTEXT_REFERENCES.search(q):
        return "refers_to_passage"
    if longest_common_run(q, passage) >= max_copy:
        return "copies_passage"
    return None


def repeated_across_chunks(rows: list[dict], min_chunks: int = 3) -> set[str]:
    """Normalised questions that appear for >= min_chunks different chunks (too generic)."""
    chunks_by_q: dict[str, set[str]] = {}
    for r in rows:
        chunks_by_q.setdefault(normalise(r["question"]), set()).add(r["chunk_id"])
    return {q for q, ch in chunks_by_q.items() if len(ch) >= min_chunks}


def count_by(rows: list[dict], *keys: str) -> dict:
    return dict(Counter(tuple(r[k] for k in keys) if len(keys) > 1 else r[keys[0]] for r in rows))
