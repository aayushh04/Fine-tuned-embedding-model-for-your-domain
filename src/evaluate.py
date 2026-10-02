"""Glue between data loading and the retrieval harness; shared by baselines, training and ablations."""
from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from src.retrieval import RetrievalResult, bootstrap_ci, build_index, encode, score_rankings, search

METRICS = ("recall@1", "recall@5", "recall@10", "mrr@10", "ndcg@10")


def eval_all(model: SentenceTransformer, chunks: list[dict], qsets: dict[str, list[dict]],
             query_prefix: str = "", settings: list[tuple[str, str, str]] | None = None
             ) -> dict[tuple[str, str, str], RetrievalResult]:
    """Evaluate `model` in many (question-set, split, corpus) settings while encoding everything only once.

    settings: list of (qset, split, corpus); corpus="split" indexes only that split's chunks (held-out corpus),
    corpus="all" indexes every chunk (realistic RAG corpus; train chunks act as distractors).
    Default: every question set x {val, test} x {split, all}.
    """
    if settings is None:
        settings = [(q, s, c) for q in qsets for s in ("val", "test") for c in ("split", "all")]
    doc_emb = encode(model, [c["text"] for c in chunks])
    cid_to_row = {c["chunk_id"]: i for i, c in enumerate(chunks)}
    q_emb = {name: encode(model, [q["question"] for q in qs], query_prefix) for name, qs in qsets.items()}

    results = {}
    for qset, split, corpus in settings:
        rows = [i for i, c in enumerate(chunks) if corpus == "all" or c["split"] == split]
        qidx = [i for i, q in enumerate(qsets[qset]) if q["split"] == split]
        if not qidx:
            continue
        row_pos = {r: p for p, r in enumerate(rows)}          # chunk row -> position in this index
        _, ranked = search(build_index(doc_emb[rows]), q_emb[qset][qidx], 10)
        relevant = [{row_pos[cid_to_row[qsets[qset][i]["positive_chunk_id"]]]} for i in qidx]
        results[(qset, split, corpus)] = score_rankings(ranked, relevant)
    return results


def result_row(res: RetrievalResult, with_ci: bool = False) -> dict:
    row = {m: round(res.metrics[m], 4) for m in METRICS}
    row["n_queries"] = len(res.per_query["mrr@10"])
    if with_ci:
        for m in ("recall@10", "ndcg@10"):
            lo, hi = bootstrap_ci(res.per_query[m])
            row[f"{m}_ci_lo"], row[f"{m}_ci_hi"] = round(lo, 4), round(hi, 4)
    return row


def per_query_array(res: RetrievalResult, metric: str) -> np.ndarray:
    return res.per_query[metric]


def save_per_query(results: dict, path) -> None:
    """Store per-query metric arrays (for paired significance tests): key = 'qset|split|corpus|metric'."""
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **{f"{q}|{s}|{c}|{m}": r.per_query[m] for (q, s, c), r in results.items() for m in METRICS})
