"""Loading chunks / questions and building evaluation corpora."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from src.utils import read_jsonl


def load_chunks(cfg: dict) -> list[dict]:
    return list(read_jsonl(cfg["paths"]["processed_dir"] / "chunks.jsonl"))


def load_questions(cfg: dict, name: str = "questions.jsonl") -> list[dict]:
    return list(read_jsonl(cfg["paths"]["synthetic_dir"] / name))


def eval_inputs(chunks: list[dict], questions: list[dict], split: str,
                corpus: str = "split") -> tuple[list[str], list[str], list[str], list[set[str]]]:
    """Build (corpus_ids, corpus_texts, queries, relevant_ids) for one split.

    corpus="split": index only that split's chunks (held-out-corpus setting).
    corpus="all":   index every chunk (realistic RAG setting; train chunks act as distractors).
    """
    pool = [c for c in chunks if corpus == "all" or c["split"] == split]
    qs = [q for q in questions if q["split"] == split]
    return ([c["chunk_id"] for c in pool], [c["text"] for c in pool],
            [q["question"] for q in qs], [{q["positive_chunk_id"]} for q in qs])


def chunks_by_id(chunks: list[dict]) -> dict[str, dict]:
    return {c["chunk_id"]: c for c in chunks}


def group_by(rows: list[dict], key: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        out[r[key]].append(r)
    return out
