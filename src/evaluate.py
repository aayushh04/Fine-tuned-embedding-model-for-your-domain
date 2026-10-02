"""Glue between data loading and the retrieval harness; shared by baselines, training and ablations."""
from __future__ import annotations

from typing import Optional

from sentence_transformers import SentenceTransformer

from src.data import eval_inputs
from src.retrieval import RetrievalResult, bootstrap_ci, evaluate_retrieval

METRICS = ("recall@1", "recall@5", "recall@10", "mrr@10", "ndcg@10")


def eval_split(model: SentenceTransformer, chunks: list[dict], questions: list[dict], split: str,
               corpus: str = "split", query_prefix: str = "") -> RetrievalResult:
    """Evaluate `model` on one split. corpus='split' indexes only that split's chunks; 'all' indexes everything."""
    ids, texts, queries, rel = eval_inputs(chunks, questions, split, corpus)
    return evaluate_retrieval(model, ids, texts, queries, rel, query_prefix=query_prefix)


def result_row(res: RetrievalResult, with_ci: bool = False) -> dict:
    row = {m: round(res.metrics[m], 4) for m in METRICS}
    row["n_queries"] = len(res.per_query["mrr@10"])
    if with_ci:
        for m in ("recall@10", "ndcg@10"):
            lo, hi = bootstrap_ci(res.per_query[m])
            row[f"{m}_ci_lo"], row[f"{m}_ci_hi"] = round(lo, 4), round(hi, 4)
    return row
