"""Embedding + FAISS retrieval helpers and the evaluation harness (Phase 3).

One function, `evaluate_retrieval`, is used for every number in the project:
baselines, validation during training, ablations and the forgetting check.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

K_VALUES = (1, 5, 10)


def load_model(model_cfg: dict | str, device: Optional[str] = None) -> SentenceTransformer:
    """Load a model from a config entry (dict with hf_name/max_seq_length) or a path/name."""
    if isinstance(model_cfg, dict):
        model = SentenceTransformer(model_cfg["hf_name"], device=device)
        model.max_seq_length = model_cfg.get("max_seq_length", model.max_seq_length)
    else:
        model = SentenceTransformer(model_cfg, device=device)
    return model


def encode(model: SentenceTransformer, texts: Sequence[str], prefix: str = "",
           batch_size: int = 64) -> np.ndarray:
    """L2-normalised float32 embeddings (so inner product == cosine similarity)."""
    texts = [prefix + t for t in texts] if prefix else list(texts)
    emb = model.encode(texts, batch_size=batch_size, convert_to_numpy=True,
                       normalize_embeddings=True, show_progress_bar=False)
    return emb.astype("float32")


def build_index(doc_emb: np.ndarray) -> faiss.Index:
    index = faiss.IndexFlatIP(doc_emb.shape[1])
    index.add(doc_emb)
    return index


def search(index: faiss.Index, query_emb: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    k = min(k, index.ntotal)
    scores, ids = index.search(query_emb, k)
    return scores, ids


@dataclass
class RetrievalResult:
    metrics: dict[str, float]
    per_query: dict[str, np.ndarray]   # metric name -> per-query values (for bootstrap CIs)


def score_rankings(ranked_ids: np.ndarray, relevant: list[set[int]]) -> RetrievalResult:
    """Metrics from ranked doc indices. `relevant[i]` = set of correct doc indices for query i.

    With binary relevance and a single positive this is the standard definition:
      recall@k = any relevant doc in the top k          (== hit rate)
      MRR@10   = 1 / rank of the first relevant doc in the top 10 (0 if absent)
      nDCG@10  = DCG of the ranking / DCG of the ideal ranking
    """
    n = len(relevant)
    per = {f"recall@{k}": np.zeros(n) for k in K_VALUES}
    per["mrr@10"], per["ndcg@10"] = np.zeros(n), np.zeros(n)
    for i, rel in enumerate(relevant):
        hits = [int(d in rel) for d in ranked_ids[i][:10]]
        for k in K_VALUES:
            per[f"recall@{k}"][i] = float(any(hits[:k]))
        for rank, h in enumerate(hits, start=1):
            if h:
                per["mrr@10"][i] = 1.0 / rank
                break
        dcg = sum(h / math.log2(r + 1) for r, h in enumerate(hits, start=1))
        ideal = sum(1 / math.log2(r + 1) for r in range(1, min(len(rel), 10) + 1))
        per["ndcg@10"][i] = dcg / ideal if ideal else 0.0
    return RetrievalResult({m: float(v.mean()) for m, v in per.items()}, per)


def evaluate_retrieval(
    model: SentenceTransformer,
    corpus_ids: list[str],
    corpus_texts: list[str],
    queries: list[str],
    relevant_ids: list[set[str]],
    query_prefix: str = "",
    doc_prefix: str = "",
    batch_size: int = 64,
) -> RetrievalResult:
    """Embed corpus + queries with `model`, retrieve top 10 with FAISS, compute metrics."""
    id_to_idx = {cid: i for i, cid in enumerate(corpus_ids)}
    doc_emb = encode(model, corpus_texts, doc_prefix, batch_size)
    q_emb = encode(model, queries, query_prefix, batch_size)
    _, ranked = search(build_index(doc_emb), q_emb, 10)
    relevant = [{id_to_idx[c] for c in rel if c in id_to_idx} for rel in relevant_ids]
    return score_rankings(ranked, relevant)


def bootstrap_ci(per_query: np.ndarray, n_boot: int = 2000, seed: int = 0) -> tuple[float, float]:
    """95% bootstrap confidence interval of the mean over queries."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(per_query), size=(n_boot, len(per_query)))
    means = per_query[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired_bootstrap_pvalue(a: np.ndarray, b: np.ndarray, n_boot: int = 5000, seed: int = 0) -> float:
    """One-sided p-value for 'mean(b) <= mean(a)' using paired resampling of queries."""
    rng = np.random.default_rng(seed)
    diff = b - a
    idx = rng.integers(0, len(diff), size=(n_boot, len(diff)))
    return float((diff[idx].mean(axis=1) <= 0).mean())
