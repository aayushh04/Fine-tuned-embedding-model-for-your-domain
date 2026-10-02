"""Diagnostic: is the fine-tuning gain specific to the question WRITER's style?

Training/validation questions were written by Qwen2.5-0.5B; the primary test questions by Claude. This script also
scores the models on Qwen-written questions for the SAME unseen test chunks (generated with
`02_generate_questions.py --splits test --out raw_questions_qwen_test.jsonl`), filtered with the same rules
(cheap rules + round-trip), and compares base vs fine-tuned on both writers' test questions.

If fine-tuning helps on the Qwen-written test questions but not on the Claude-written ones, the model learned the
generator's question style rather than only the domain.

Writes results/style_shift.csv and results/tables/style_shift.md
Usage: python scripts/09_style_shift_check.py --runs bge-small_hn_100_s42 bge-small_hn_100_s43 ...
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src.data import chunks_by_id, load_chunks, load_questions  # noqa: E402
from src.evaluate import METRICS, eval_all  # noqa: E402
from src.filters import basic_reject_reason, normalise  # noqa: E402
from src.retrieval import bootstrap_ci, build_index, encode, load_model, search  # noqa: E402
from src.utils import DEFAULT_CONFIG, append_csv_row, load_config, read_jsonl  # noqa: E402


def filtered_qwen_test_questions(cfg: dict, chunks: list[dict], base_model) -> list[dict]:
    scfg = cfg["synthetic"]
    by_id = chunks_by_id(chunks)
    rows, seen = [], set()
    for r in read_jsonl(cfg["paths"]["synthetic_dir"] / "raw_questions_qwen_test.jsonl"):
        key = (r["chunk_id"], normalise(r["question"]))
        if key in seen or basic_reject_reason(r["question"], by_id[r["chunk_id"]]["text"],
                                              scfg["min_question_words"], scfg["max_copy_ngram"]):
            continue
        seen.add(key)
        rows.append({"question": r["question"], "positive_chunk_id": r["chunk_id"], "doc_id": r["doc_id"],
                     "split": "test", "qtype": r["qtype"], "writer": "qwen"})
    # same round-trip rule as the main filter: the base model must retrieve the source chunk in its top-K (over ALL chunks)
    mcfg = cfg["models"][scfg["filter_model"]]
    q_emb = encode(base_model, [r["question"] for r in rows], mcfg["query_prefix"])
    _, ranked = search(build_index(encode(base_model, [c["text"] for c in chunks])), q_emb, scfg["roundtrip_top_k"])
    ids = [c["chunk_id"] for c in chunks]
    return [r for r, top in zip(rows, ranked) if r["positive_chunk_id"] in {ids[j] for j in top}]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--model", default="bge-small")
    parser.add_argument("--runs", nargs="+", required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    mcfg = cfg["models"][args.model]
    chunks = load_chunks(cfg)

    base = load_model(mcfg)
    qwen_q = filtered_qwen_test_questions(cfg, chunks, base)
    claude_q = [q for q in load_questions(cfg) if q["split"] == "test"]
    qsets = {"claude_written": claude_q, "qwen_written": qwen_q}
    print({k: len(v) for k, v in qsets.items()}, "test questions")
    settings = [(q, "test", "split") for q in qsets]

    out_csv = cfg["paths"]["results_dir"] / "style_shift.csv"
    out_csv.unlink(missing_ok=True)
    per_model = {"base": eval_all(base, chunks, qsets, mcfg["query_prefix"], settings)}
    del base
    for run in args.runs:
        model = load_model(str(cfg["paths"]["models_dir"] / run / "final"))
        model.max_seq_length = mcfg["max_seq_length"]
        per_model[run] = eval_all(model, chunks, qsets, mcfg["query_prefix"], settings)
        del model

    for name, res in per_model.items():
        for (qset, _, _), r in res.items():
            append_csv_row(out_csv, {"model": name, "questions": qset, "n": len(r.per_query["mrr@10"]),
                                     **{m: round(r.metrics[m], 4) for m in METRICS}})

    lines = ["| questions | n | base nDCG@10 | fine-tuned nDCG@10 (mean of runs) | Δ | 95% CI of Δ | base Recall@1 | fine-tuned Recall@1 | Δ |",
             "|---|---|---|---|---|---|---|---|---|"]
    for qset in qsets:
        b = per_model["base"][(qset, "test", "split")]
        fts = [per_model[r][(qset, "test", "split")] for r in args.runs]
        ft_nd = np.mean([f.per_query["ndcg@10"] for f in fts], axis=0)
        diff = ft_nd - b.per_query["ndcg@10"]
        lo, hi = bootstrap_ci(diff)
        r1b, r1f = b.metrics["recall@1"], np.mean([f.metrics["recall@1"] for f in fts])
        lines.append(f"| {qset} | {len(diff)} | {b.metrics['ndcg@10']:.3f} | {ft_nd.mean():.3f} | {diff.mean():+.3f} | "
                     f"[{lo:+.3f}, {hi:+.3f}] | {r1b:.3f} | {r1f:.3f} | {r1f - r1b:+.3f} |")
    (cfg["paths"]["results_dir"] / "tables" / "style_shift.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
