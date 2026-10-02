"""Phase 4: mine hard negatives for the TRAIN questions and build (question, positive, negative) triplets.

For each train question:
  1. retrieve the top-K over TRAIN chunks only (never val/test chunks) with the base model
  2. candidates = ranks [rank_min, K), minus the positive, minus chunks adjacent to the positive in the
     same document (they overlap with it), minus near-copies of the positive (cos(pos, cand) > max_pos_similarity)
  3. shortlist: a seeded random sample of at most `ce_shortlist` of the remaining candidates (keeps the
     cross-encoder cost bounded)
  4. false-negative guard: a cross-encoder scores (question, candidate) and (question, positive); a candidate
     is dropped if CE(q, cand) > CE(q, pos) - ce_margin, i.e. it looks like it answers the question about as
     well as the real positive
  5. sample one surviving candidate (seeded). If none survives, fall back to a random train chunk from a
     different document (flagged neg_kind="fallback") so every question yields a triplet.

Output: data/triplets/<model>_triplets.jsonl and results/phase4_negatives_report.json
Usage: python scripts/04_mine_negatives.py --model bge-small
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
from sentence_transformers import CrossEncoder  # noqa: E402

from src.data import load_chunks, load_questions  # noqa: E402
from src.retrieval import build_index, encode, load_model, search  # noqa: E402
from src.utils import DEFAULT_CONFIG, load_config, set_seed, write_jsonl  # noqa: E402


def chunk_number(chunk_id: str) -> int:
    return int(chunk_id.rsplit("#", 1)[1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--model", default="bge-small")
    args = parser.parse_args()
    cfg = load_config(args.config)
    ncfg = cfg["negatives"]
    set_seed(cfg["seed"])
    rng = random.Random(cfg["seed"])

    mcfg = cfg["models"][args.model]
    chunks = [c for c in load_chunks(cfg) if c["split"] == "train"]       # train pool only
    questions = [q for q in load_questions(cfg) if q["split"] == "train"]
    idx = {c["chunk_id"]: i for i, c in enumerate(chunks)}
    print(f"{len(questions)} train questions, {len(chunks)} train chunks")

    model = load_model(mcfg)
    doc_emb = encode(model, [c["text"] for c in chunks])
    q_emb = encode(model, [q["question"] for q in questions], mcfg["query_prefix"])
    _, ranked = search(build_index(doc_emb), q_emb, ncfg["mine_top_k"])
    del model

    reasons: Counter = Counter()
    candidates: list[list[int]] = []
    for qi, q in enumerate(questions):
        pos = idx[q["positive_chunk_id"]]
        pos_c = chunks[pos]
        keep = []
        for rank, j in enumerate(ranked[qi]):
            if rank < ncfg["rank_min"]:
                continue
            c = chunks[j]
            if j == pos:
                reasons["is_positive"] += 1
            elif c["doc_id"] == pos_c["doc_id"] and abs(chunk_number(c["chunk_id"]) - chunk_number(pos_c["chunk_id"])) <= 1:
                reasons["adjacent_to_positive"] += 1
            elif float(doc_emb[j] @ doc_emb[pos]) > ncfg["max_pos_similarity"]:
                reasons["too_similar_to_positive"] += 1
            else:
                keep.append(j)
        if len(keep) > ncfg["ce_shortlist"]:
            keep = rng.sample(keep, ncfg["ce_shortlist"])
        candidates.append(keep)

    # cross-encoder verification
    ce = CrossEncoder(ncfg["cross_encoder"], max_length=512)
    pairs, owners = [], []
    for qi, q in enumerate(questions):
        pairs.append((q["question"], chunks[idx[q["positive_chunk_id"]]]["text"]))
        owners.append((qi, -1))
        for j in candidates[qi]:
            pairs.append((q["question"], chunks[j]["text"]))
            owners.append((qi, j))
    print(f"scoring {len(pairs)} pairs with the cross-encoder ...")
    scores = ce.predict(pairs, batch_size=64, show_progress_bar=False)
    pos_score: dict[int, float] = {}
    cand_scores: dict[int, list[tuple[int, float]]] = {i: [] for i in range(len(questions))}
    for (qi, j), s in zip(owners, scores):
        (pos_score.__setitem__(qi, float(s)) if j == -1 else cand_scores[qi].append((j, float(s))))

    triplets, n_fallback, margins = [], 0, []
    for qi, q in enumerate(questions):
        ok = []
        for j, s in cand_scores[qi]:
            if s > pos_score[qi] - ncfg["ce_margin"]:
                reasons["likely_false_negative_by_cross_encoder"] += 1
            else:
                ok.append(j)
        pos = chunks[idx[q["positive_chunk_id"]]]
        if ok:
            j, kind = rng.choice(ok), "hard"
            margins.append(pos_score[qi] - dict(cand_scores[qi])[j])
        else:
            others = [k for k, c in enumerate(chunks) if c["doc_id"] != pos["doc_id"]]
            j, kind = rng.choice(others), "fallback"
            n_fallback += 1
        triplets.append({"question": q["question"], "positive_chunk_id": q["positive_chunk_id"],
                         "negative_chunk_id": chunks[j]["chunk_id"], "neg_kind": kind,
                         "neg_rank_in_base_model": (list(ranked[qi]).index(j) + 1) if j in ranked[qi] else None,
                         "doc_id": q["doc_id"], "split": "train", "writer": q.get("writer")})

    out = cfg["paths"]["triplets_dir"] / f"{args.model}_triplets.jsonl"
    write_jsonl(out, triplets)
    report = {"model": args.model, "n_triplets": len(triplets), "n_hard": len(triplets) - n_fallback,
              "n_fallback": n_fallback, "candidates_dropped": dict(reasons),
              "mean_ce_margin_pos_minus_neg": round(float(np.mean(margins)), 3) if margins else None,
              "mean_candidates_per_question_after_geometry_filters": round(float(np.mean([len(c) for c in candidates])), 1)}
    (cfg["paths"]["results_dir"] / f"phase4_negatives_report_{args.model}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
