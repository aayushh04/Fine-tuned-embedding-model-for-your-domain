"""Phase 2c: filter raw questions -> data/synthetic/questions.jsonl.

Filters, in order (each drop is counted in results/phase2_filter_report.json):
  1. rule-based: not a question / too short / too generic / refers to "the passage" / copies a
     >=N-word run from the chunk
  2. exact duplicates, and the same question appearing for >=3 different chunks (generic)
  3. near-duplicates (embedding cosine > threshold) within the same chunk
  4. round-trip check: the base model (filter_model) must retrieve the source chunk in its
     top-K over the FULL corpus (same strictness for every split)

Outputs:
  questions.jsonl       questions that passed everything  {question, positive_chunk_id, doc_id, split, ...}
  questions_all.jsonl   questions that passed 1-3, with `rt_rank` (for the unfiltered-test robustness check)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src.data import chunks_by_id, load_chunks  # noqa: E402
from src.filters import basic_reject_reason, normalise, repeated_across_chunks  # noqa: E402
from src.retrieval import build_index, encode, load_model, search  # noqa: E402
from src.utils import DEFAULT_CONFIG, load_config, read_jsonl, set_seed, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    args = parser.parse_args()
    cfg = load_config(args.config)
    scfg = cfg["synthetic"]
    set_seed(cfg["seed"])
    syn = cfg["paths"]["synthetic_dir"]

    chunks = load_chunks(cfg)
    by_id = chunks_by_id(chunks)
    raw = list(read_jsonl(syn / "raw_questions_local.jsonl")) + list(read_jsonl(syn / "raw_questions_claude.jsonl"))
    for r in raw:  # sanity: the split recorded with the question must match the chunk's split
        assert by_id[r["chunk_id"]]["split"] == r["split"], f"split mismatch for {r['chunk_id']}"
    report: dict = {"raw": Counter((r["split"], r["writer"]) for r in raw), "dropped": defaultdict(Counter)}

    def drop(r: dict, reason: str) -> None:
        report["dropped"][reason][(r["split"], r["writer"])] += 1

    # 1. rule-based
    stage1 = []
    for r in raw:
        why = basic_reject_reason(r["question"], by_id[r["chunk_id"]]["text"],
                                  scfg["min_question_words"], scfg["max_copy_ngram"])
        (drop(r, why) if why else stage1.append(r))

    # 2. exact duplicates + generic (same question for many chunks)
    generic = repeated_across_chunks(stage1)
    seen, stage2 = set(), []
    for r in stage1:
        key = (r["chunk_id"], normalise(r["question"]))
        if normalise(r["question"]) in generic:
            drop(r, "generic_repeated_across_chunks")
        elif key in seen:
            drop(r, "exact_duplicate")
        else:
            seen.add(key)
            stage2.append(r)

    # 3. near-duplicates within a chunk, 4. round-trip: both need embeddings
    model = load_model(cfg["models"][scfg["filter_model"]])
    prefix = cfg["models"][scfg["filter_model"]]["query_prefix"]
    q_emb = encode(model, [r["question"] for r in stage2], prefix)
    by_chunk: dict[str, list[int]] = defaultdict(list)
    for i, r in enumerate(stage2):
        by_chunk[r["chunk_id"]].append(i)
    keep = np.ones(len(stage2), dtype=bool)
    for idxs in by_chunk.values():
        for a_pos, a in enumerate(idxs):
            if not keep[a]:
                continue
            for b in idxs[a_pos + 1:]:
                if keep[b] and float(q_emb[a] @ q_emb[b]) > scfg["dup_threshold"]:
                    keep[b] = False
                    drop(stage2[b], "near_duplicate_in_chunk")
    stage3 = [(i, r) for i, r in enumerate(stage2) if keep[i]]

    doc_emb = encode(model, [c["text"] for c in chunks])
    chunk_ids = [c["chunk_id"] for c in chunks]
    _, ranked = search(build_index(doc_emb), q_emb[[i for i, _ in stage3]], scfg["roundtrip_top_k"])
    all_rows, final = [], []
    for (_, r), top in zip(stage3, ranked):
        top_ids = [chunk_ids[j] for j in top]
        rank = top_ids.index(r["chunk_id"]) + 1 if r["chunk_id"] in top_ids else None
        row = {"question": r["question"], "positive_chunk_id": r["chunk_id"], "doc_id": r["doc_id"],
               "split": r["split"], "qtype": r["qtype"], "writer": r["writer"], "rt_rank": rank}
        all_rows.append(row)
        if rank is None:
            drop(r, "failed_roundtrip")
        else:
            final.append(row)

    write_jsonl(syn / "questions_all.jsonl", all_rows)
    write_jsonl(syn / "questions.jsonl", final)

    flat = lambda c: {f"{k[0]}/{k[1]}": v for k, v in sorted(c.items())}
    out = {"raw": flat(report["raw"]),
           "dropped": {reason: flat(c) for reason, c in report["dropped"].items()},
           "kept": flat(Counter((r["split"], r["writer"]) for r in final)),
           "kept_by_qtype": flat(Counter((r["split"], r["qtype"]) for r in final)),
           "chunks_with_question": {s: len({r["positive_chunk_id"] for r in final if r["split"] == s})
                                    for s in ("train", "val", "test")},
           "questions_per_split": dict(Counter(r["split"] for r in final))}
    (cfg["paths"]["results_dir"] / "phase2_filter_report.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
