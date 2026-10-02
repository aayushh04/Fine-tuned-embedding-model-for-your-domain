"""Document-level train/val/test split and leakage checks.

The split happens on DOCUMENTS, before any questions are generated, so no text from a
test document can ever reach training (directly or via a near-identical chunk).
"""
from __future__ import annotations

import random
import re
from collections import defaultdict

SPLITS = ("train", "val", "test")


def split_documents(doc_sizes: dict[str, int], doc_source: dict[str, str],
                    ratios: dict[str, float], seed: int,
                    max_eval_doc_chunks: int | None = None) -> dict[str, str]:
    """Assign each doc to a split, stratified by source and balanced by chunk count.

    Docs differ a lot in length, so we target the ratios in *chunks*, not docs: walk a
    seeded shuffle of each source's docs and place each doc by the midpoint of its
    cumulative chunk range.

    Docs with more than `max_eval_doc_chunks` chunks always go to train (they lead the
    walk), so a single huge page can never dominate the val or test set.
    """
    assert abs(sum(ratios[s] for s in SPLITS) - 1.0) < 1e-6, "split ratios must sum to 1"
    bounds = (ratios["train"], ratios["train"] + ratios["val"])
    rng = random.Random(seed)
    is_big = lambda d: max_eval_doc_chunks is not None and doc_sizes[d] > max_eval_doc_chunks

    by_source: dict[str, list[str]] = defaultdict(list)
    for doc_id in sorted(doc_sizes):
        by_source[doc_source[doc_id]].append(doc_id)

    assignment: dict[str, str] = {}
    for source in sorted(by_source):
        docs = by_source[source]
        rng.shuffle(docs)
        docs = [d for d in docs if is_big(d)] + [d for d in docs if not is_big(d)]
        if sum(doc_sizes[d] for d in docs if is_big(d)) > bounds[0] * sum(doc_sizes[d] for d in docs):
            raise ValueError(f"{source}: forced-train docs exceed the train ratio; raise max_eval_doc_chunks")
        total, cum = sum(doc_sizes[d] for d in docs), 0
        for d in docs:
            mid = (cum + doc_sizes[d] / 2) / total
            assignment[d] = "train" if mid < bounds[0] else "val" if mid < bounds[1] else "test"
            cum += doc_sizes[d]
    return assignment


def normalise_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def check_leakage(chunks: list[dict]) -> dict:
    """Verify no doc spans two splits, and count chunk bodies duplicated across splits.

    Cross-split duplicates happen when two pages include the same code example; they act
    like test answers seen during training, so we report (and later drop) them.
    """
    doc_splits: dict[str, set] = defaultdict(set)
    body_splits: dict[str, set] = defaultdict(set)
    body_ids: dict[str, list] = defaultdict(list)
    for c in chunks:
        doc_splits[c["doc_id"]].add(c["split"])
        body = normalise_text(c["text"].split("\n\n", 1)[-1])
        body_splits[body].add(c["split"])
        body_ids[body].append(c["chunk_id"])

    docs_in_multiple = [d for d, s in doc_splits.items() if len(s) > 1]
    cross_dupes = [body_ids[b] for b, s in body_splits.items() if len(s) > 1]
    within_dupes = [body_ids[b] for b, s in body_splits.items() if len(s) == 1 and len(body_ids[b]) > 1]
    return {
        "docs_in_multiple_splits": docs_in_multiple,
        "cross_split_duplicate_groups": cross_dupes,
        "within_split_duplicate_groups": within_dupes,
    }
