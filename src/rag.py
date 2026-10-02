"""Minimal RAG pipeline: embed -> retrieve top-k from the full corpus -> generate a cited answer."""
from __future__ import annotations

import re

from src.llm import LocalChat
from src.retrieval import build_index, encode, search

SYSTEM = (
    "You answer developer questions about FastAPI, Pydantic and Starlette using ONLY the numbered passages "
    "provided. Cite the passages you used like [1] or [2][3] right after each claim. "
    "If the passages do not contain the answer, reply exactly: I cannot find this in the provided documentation. "
    "Keep the answer under 120 words."
)


class Retriever:
    """Dense retriever over a fixed list of chunks (FAISS inner-product index)."""

    def __init__(self, model, chunks: list[dict], query_prefix: str = ""):
        self.model, self.chunks, self.prefix = model, chunks, query_prefix
        self.index = build_index(encode(model, [c["text"] for c in chunks]))

    def retrieve(self, queries: list[str], k: int = 5) -> list[list[dict]]:
        _, ids = search(self.index, encode(self.model, queries, self.prefix), k)
        return [[self.chunks[j] for j in row] for row in ids]


def build_messages(question: str, passages: list[dict]) -> list[dict]:
    context = "\n\n".join(f"[{i}] {p['text']}" for i, p in enumerate(passages, 1))
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Passages:\n{context}\n\nQuestion: {question}\nAnswer:"}]


def answer_questions(llm: LocalChat, questions: list[str], retrieved: list[list[dict]],
                     batch_size: int = 4, max_new_tokens: int = 200) -> list[str]:
    out: list[str] = []
    for i in range(0, len(questions), batch_size):
        convs = [build_messages(q, ps) for q, ps in zip(questions[i:i + batch_size], retrieved[i:i + batch_size])]
        out.extend(llm.generate(convs, max_new_tokens=max_new_tokens, temperature=0.0))
    return out


def cited_ids(answer: str) -> list[int]:
    return [int(n) for n in re.findall(r"\[(\d+)\]", answer)]
