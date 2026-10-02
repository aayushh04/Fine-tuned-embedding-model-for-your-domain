"""Phase 7a: pick the ~50 test questions used for the end-to-end RAG comparison.

Stratified by question type, at most one question per test document where possible, seeded.
Writes data/rag/rag_questions.jsonl (id, question, gold chunk, gold text) and a human-readable
data/rag/rag_questions_to_answer.md used to write the reference answers.
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import chunks_by_id, load_chunks, load_questions  # noqa: E402
from src.utils import DEFAULT_CONFIG, load_config, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    args = parser.parse_args()
    cfg = load_config(args.config)
    n_total = cfg["rag"]["n_questions"]
    rng = random.Random(cfg["seed"])
    by_id = chunks_by_id(load_chunks(cfg))
    questions = [q for q in load_questions(cfg) if q["split"] == "test"]

    by_doc: dict[str, list[dict]] = defaultdict(list)
    for q in questions:
        by_doc[q["doc_id"]].append(q)
    docs = sorted(by_doc)
    rng.shuffle(docs)
    # one question per document, round-robin over question types so all types are represented
    wanted = ["factual", "how-to", "comparison"]
    picked, t = [], 0
    for d in docs:
        pool = [q for q in by_doc[d] if q["qtype"] == wanted[t % 3]] or by_doc[d]
        picked.append(rng.choice(pool))
        t += 1
        if len(picked) == n_total:
            break
    # test has fewer documents than n_total: take a second question (from a different chunk) in the largest docs
    if len(picked) < n_total:
        used_chunks = {q["positive_chunk_id"] for q in picked}
        extra_docs = sorted(by_doc, key=lambda d: (-len(by_doc[d]), d))
        for d in extra_docs:
            pool = [q for q in by_doc[d] if q["positive_chunk_id"] not in used_chunks]
            if pool and len(picked) < n_total:
                q = rng.choice(pool)
                picked.append(q)
                used_chunks.add(q["positive_chunk_id"])
    rows = [{"qid": f"r{i:02d}", "question": q["question"], "qtype": q["qtype"],
             "gold_chunk_id": q["positive_chunk_id"], "gold_text": by_id[q["positive_chunk_id"]]["text"]}
            for i, q in enumerate(picked)]
    out = cfg["paths"]["processed_dir"].parent / "rag"
    write_jsonl(out / "rag_questions.jsonl", rows)
    with open(out / "rag_questions_to_answer.md", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(f"## {r['qid']} ({r['qtype']})\n**Q:** {r['question']}\n\n**Gold passage ({r['gold_chunk_id']}):**\n\n{r['gold_text']}\n\n---\n\n")
    print(f"{len(rows)} questions, {len({r['gold_chunk_id'].split('#')[0] for r in rows})} distinct docs")


if __name__ == "__main__":
    main()
