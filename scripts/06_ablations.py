"""Phase 6: run the ablation grid by calling scripts/05_train.py once per configuration.

Grid (every cell is repeated for each seed in training.seeds, results are reported as mean +/- std):
  a) base vs fine-tuned          bge-small / hard negatives / 100% data   (vs the baselines)
  b) with vs without hard negs   bge-small and minilm, 100% data
  c) training-data size          bge-small / hard negatives / 25%, 50%, 100%
  d) two base models             bge-small vs minilm (same recipe)
Runs that already exist in results/runs.csv are skipped, so the script can be stopped and resumed.

Usage: python scripts/06_ablations.py [--only-seed 42] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils import DEFAULT_CONFIG, ROOT, load_config  # noqa: E402


def grid(seeds: list[int]) -> list[dict]:
    cells = [  # (tag, model, hard_negatives, frac)
        ("main", "bge-small", True, 1.0),
        ("no_hard_negatives", "bge-small", False, 1.0),
        ("data_size", "bge-small", True, 0.5),
        ("data_size", "bge-small", True, 0.25),
        ("second_model", "minilm", True, 1.0),
        ("second_model_no_hn", "minilm", False, 1.0),
    ]
    runs = []
    for seed in seeds:
        for tag, model, hn, frac in cells:
            name = f"{model}_{'hn' if hn else 'nohn'}_{round(frac * 100)}_s{seed}"
            runs.append({"name": name, "tag": tag, "model": model, "hn": hn, "frac": frac, "seed": seed})
    return runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--only-seed", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    cfg = load_config(args.config)
    seeds = [args.only_seed] if args.only_seed is not None else cfg["training"]["seeds"]

    runs_csv = cfg["paths"]["results_dir"] / "runs.csv"
    done = {r["run"] for r in csv.DictReader(open(runs_csv, encoding="utf-8"))} if runs_csv.exists() else set()
    todo = [r for r in grid(seeds) if r["name"] not in done]
    print(f"{len(todo)} runs to do, {len(done)} already done")
    for r in todo:
        cmd = [sys.executable, str(ROOT / "scripts" / "05_train.py"), "--model", r["model"], "--frac", str(r["frac"]),
               "--seed", str(r["seed"]), "--name", r["name"], "--tag", r["tag"]]
        if not r["hn"]:
            cmd.append("--no-hard-negatives")
        print(" ".join(cmd[1:]))
        if not args.dry_run:
            subprocess.run(cmd, check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
