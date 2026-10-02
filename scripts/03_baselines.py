"""Phase 3: evaluate off-the-shelf embedding models (the numbers to beat).

For each model, evaluates on val and test, in two settings:
  corpus=split  index only that split's chunks (held-out-corpus setting)  <- primary
  corpus=all    index all chunks (train chunks act as distractors)
and on two question sets: the filtered set (primary) and the unfiltered test set (round-trip
filter off), to check that the round-trip filter does not flatter the numbers.

Writes results/baselines.csv and results/tables/baselines.md.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import load_chunks, load_questions  # noqa: E402
from src.evaluate import eval_all, result_row, save_per_query  # noqa: E402
from src.retrieval import load_model  # noqa: E402
from src.utils import DEFAULT_CONFIG, load_config, set_seed  # noqa: E402


def markdown_table(rows: list[dict], cols: list[str]) -> str:
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "\n".join("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--models", nargs="+", default=None)
    args = parser.parse_args()
    cfg = load_config(args.config)
    set_seed(cfg["seed"])
    chunks = load_chunks(cfg)
    qsets = {"filtered": load_questions(cfg, "questions.jsonl"),
             "unfiltered": load_questions(cfg, "questions_all.jsonl")}

    rows = []
    for name in args.models or list(cfg["models"]):
        mcfg = cfg["models"][name]
        model = load_model(mcfg)
        results = eval_all(model, chunks, qsets, mcfg["query_prefix"])
        save_per_query(results, cfg["paths"]["results_dir"] / "per_query" / f"base_{name}.npz")
        for (qset, split, corpus), res in results.items():
            rows.append({"model": name, "split": split, "corpus": corpus, "qset": qset,
                         **result_row(res, with_ci=(split == "test"))})
            print(rows[-1])
        del model

    from src.utils import append_csv_row
    out_csv = cfg["paths"]["results_dir"] / "baselines.csv"
    out_csv.unlink(missing_ok=True)
    for r in rows:
        append_csv_row(out_csv, r)
    cols = ["model", "split", "corpus", "qset", "n_queries", "recall@1", "recall@5", "recall@10", "mrr@10", "ndcg@10"]
    tables = cfg["paths"]["results_dir"] / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    (tables / "baselines.md").write_text(markdown_table(rows, cols), encoding="utf-8")


if __name__ == "__main__":
    main()
