"""Phase 7c: unblind the manual judgements and aggregate the RAG comparison.

Reads data/rag/judge_scores.json:  {"r00": {"X": {"correct": 0-2, "halluc": 0/1}, "Y": {...}}, ...}
Rubric (stated before scoring):
  correct (0-2): 2 = agrees with the reference on all key facts; 1 = partly correct / misses a key part;
                 0 = wrong, unrelated, or refuses to answer
  halluc  (0/1): 1 = states specifics that contradict the reference or look fabricated (a refusal is not a hallucination)
Writes results/rag_summary.json and results/tables/rag.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from src.retrieval import bootstrap_ci, paired_bootstrap_pvalue  # noqa: E402
from src.utils import DEFAULT_CONFIG, load_config, read_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    args = parser.parse_args()
    cfg = load_config(args.config)
    rag_dir = cfg["paths"]["processed_dir"].parent / "rag"
    key = json.loads((rag_dir / "blind_key.json").read_text(encoding="utf-8"))
    scores = json.loads((rag_dir / "judge_scores.json").read_text(encoding="utf-8"))
    outputs = {r["qid"]: r for r in read_jsonl(cfg["paths"]["results_dir"] / "rag_outputs.jsonl")}

    per: dict[str, dict[str, list]] = {s: {"correct": [], "halluc": [], "hit@5": [], "cites_gold": [],
                                           "valid_citations": [], "refused": [], "answer_sim": []}
                                       for s in ("base", "finetuned")}
    for qid in sorted(outputs):
        for label, system in key[qid].items():
            per[system]["correct"].append(scores[qid][label]["correct"])
            per[system]["halluc"].append(scores[qid][label]["halluc"])
            for m in ("hit@5", "cites_gold", "valid_citations", "refused", "answer_sim"):
                per[system][m].append(float(outputs[qid][system][m]))
    summary = {}
    for system, d in per.items():
        summary[system] = {m: round(float(np.mean(v)), 3) for m, v in d.items()}
        summary[system]["correct_ci95"] = [round(x, 3) for x in bootstrap_ci(np.array(d["correct"], dtype=float))]
    base_c, ft_c = np.array(per["base"]["correct"], dtype=float), np.array(per["finetuned"]["correct"], dtype=float)
    summary["paired"] = {"n": len(base_c), "ft_better": int((ft_c > base_c).sum()), "base_better": int((ft_c < base_c).sum()),
                         "ties": int((ft_c == base_c).sum()),
                         "p_one_sided_ft_not_better": round(paired_bootstrap_pvalue(base_c, ft_c), 4)}
    (cfg["paths"]["results_dir"] / "rag_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    cols = ["correct", "halluc", "hit@5", "cites_gold", "valid_citations", "refused", "answer_sim"]
    md = "| system | " + " | ".join(cols) + " |\n|" + "---|" * (len(cols) + 1) + "\n"
    for s in ("base", "finetuned"):
        md += f"| {s} | " + " | ".join(str(summary[s][c]) for c in cols) + " |\n"
    tables = cfg["paths"]["results_dir"] / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    (tables / "rag.md").write_text(md, encoding="utf-8")
    print(md)
    print(summary["paired"])


if __name__ == "__main__":
    main()
