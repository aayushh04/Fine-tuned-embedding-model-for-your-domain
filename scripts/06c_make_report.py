"""Phase 6c: turn results/*.csv into the markdown tables and figures used in the README.

Reads  results/baselines.csv, results/runs.csv, results/forgetting.csv, results/per_query/*.npz
Writes results/tables/*.md and results/figures/*.png

Primary setting everywhere: TEST split, held-out corpus (only test chunks indexed), filtered questions.
Robustness settings (all-chunks index, unfiltered questions) are reported in their own table.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.retrieval import paired_bootstrap_pvalue  # noqa: E402
from src.utils import DEFAULT_CONFIG, load_config  # noqa: E402

METRICS = ["recall@1", "recall@5", "recall@10", "mrr@10", "ndcg@10"]
LABELS = {"recall@1": "Recall@1", "recall@5": "Recall@5", "recall@10": "Recall@10", "mrr@10": "MRR@10", "ndcg@10": "nDCG@10"}

# reference palette (dataviz skill): categorical slots 1-3 on the light chart surface
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": INK, "font.family": "sans-serif", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True,
    "grid.color": GRID, "grid.linewidth": 0.8,
})


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    return out + "\n".join("| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)) + "\n"


def pm(values: pd.Series) -> str:
    """mean +/- std (population-of-seeds, ddof=1 when n>1)."""
    v = values.astype(float)
    return f"{v.mean():.3f} ± {v.std(ddof=1):.3f}" if len(v) > 1 else f"{v.mean():.3f}"


def runs_for(runs: pd.DataFrame, model: str, hn: bool, frac: float) -> pd.DataFrame:
    return runs[(runs.model == model) & (runs.hard_negatives == hn) & (runs.frac == frac)]


def base_row(base: pd.DataFrame, model: str, split="test", corpus="split", qset="filtered") -> pd.Series:
    return base[(base.model == model) & (base.split == split) & (base.corpus == corpus) & (base.qset == qset)].iloc[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    args = parser.parse_args()
    cfg = load_config(args.config)
    res_dir = cfg["paths"]["results_dir"]
    tables, figs = res_dir / "tables", res_dir / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)

    base = pd.read_csv(res_dir / "baselines.csv")
    runs = pd.read_csv(res_dir / "runs.csv")
    fts = [m for m in ("bge-small", "minilm") if not runs_for(runs, m, True, 1.0).empty]

    # ---------------------------------------------------------------- (a)+(d) base vs fine-tuned, two base models
    rows = []
    for m in cfg["models"]:
        b = base_row(base, m)
        rows.append({"model": f"{m} (off the shelf)", **{LABELS[k]: f"{b[k]:.3f}" for k in METRICS}})
        r = runs_for(runs, m, True, 1.0)
        if not r.empty:
            rows.append({"model": f"{m} fine-tuned (hard negs, 100%, n={len(r)} seeds)",
                         **{LABELS[k]: pm(r[f"test_split_{k}"]) for k in METRICS}})
            rows.append({"model": f"  Δ vs off the shelf", **{LABELS[k]: f"{r[f'test_split_{k}'].mean() - b[k]:+.3f}" for k in METRICS}})
    (tables / "main_results.md").write_text(md_table(pd.DataFrame(rows)), encoding="utf-8")

    # significance: seed-averaged fine-tuned per-query scores vs base, paired bootstrap over test queries
    sig = []
    for m in fts:
        b = np.load(res_dir / "per_query" / f"base_{m}.npz")
        key = "filtered|test|split|ndcg@10"
        ft = np.mean([np.load(res_dir / "per_query" / f"{n}.npz")[key] for n in runs_for(runs, m, True, 1.0).run], axis=0)
        diff = ft - b[key]
        rng = np.random.default_rng(0)
        boots = diff[rng.integers(0, len(diff), size=(5000, len(diff)))].mean(axis=1)
        sig.append({"model": m, "n_test_queries": len(diff), "mean Δ nDCG@10": f"{diff.mean():+.3f}",
                    "95% CI": f"[{np.percentile(boots, 2.5):+.3f}, {np.percentile(boots, 97.5):+.3f}]",
                    "p (FT not better)": f"{paired_bootstrap_pvalue(b[key], ft):.4f}",
                    "queries better / worse": f"{int((diff > 0).sum())} / {int((diff < 0).sum())}"})
    if sig:
        (tables / "significance.md").write_text(md_table(pd.DataFrame(sig)), encoding="utf-8")

    # ---------------------------------------------------------------- (b) hard negatives
    rows = []
    for m in fts:
        for hn, label in ((False, "in-batch negatives only"), (True, "+ mined hard negatives")):
            r = runs_for(runs, m, hn, 1.0)
            if not r.empty:
                rows.append({"model": m, "training": label, "seeds": len(r),
                             **{LABELS[k]: pm(r[f"test_split_{k}"]) for k in METRICS}})
    if rows:
        (tables / "ablation_hard_negatives.md").write_text(md_table(pd.DataFrame(rows)), encoding="utf-8")

    # ---------------------------------------------------------------- (c) data size
    rows, curve = [], {}
    for frac in (0.25, 0.5, 1.0):
        r = runs_for(runs, "bge-small", True, frac)
        if not r.empty:
            rows.append({"train fraction": f"{int(frac * 100)}%", "train examples": int(r.n_train_examples.iloc[0]), "seeds": len(r),
                         **{LABELS[k]: pm(r[f"test_split_{k}"]) for k in METRICS}})
            curve[frac] = r["test_split_ndcg@10"].astype(float)
    if rows:
        b = base_row(base, "bge-small")
        rows.insert(0, {"train fraction": "0% (off the shelf)", "train examples": 0, "seeds": "-", **{LABELS[k]: f"{b[k]:.3f}" for k in METRICS}})
        (tables / "ablation_data_size.md").write_text(md_table(pd.DataFrame(rows)), encoding="utf-8")

    # ---------------------------------------------------------------- robustness (all-chunks index, unfiltered questions)
    rows = []
    for m in fts:
        r = runs_for(runs, m, True, 1.0)
        for label, col, brow in (("held-out corpus, filtered questions (primary)", "test_split", base_row(base, m)),
                                 ("all chunks indexed, filtered questions", "test_all", base_row(base, m, corpus="all")),
                                 ("held-out corpus, unfiltered questions", "test_unfiltered", base_row(base, m, qset="unfiltered"))):
            rows.append({"model": m, "setting": label, "base nDCG@10": f"{brow['ndcg@10']:.3f}",
                         "fine-tuned nDCG@10": pm(r[f"{col}_ndcg@10"]), "base Recall@1": f"{brow['recall@1']:.3f}",
                         "fine-tuned Recall@1": pm(r[f"{col}_recall@1"])})
    if rows:
        (tables / "robustness.md").write_text(md_table(pd.DataFrame(rows)), encoding="utf-8")

    # ---------------------------------------------------------------- (e) forgetting
    fpath = res_dir / "forgetting.csv"
    if fpath.exists():
        f = pd.read_csv(fpath)
        rows = []
        for b in f.base.unique():
            ref = f[(f.base == b) & f.model.str.endswith("(base)")].set_index("dataset")
            for _, r in f[(f.base == b) & ~f.model.str.endswith("(base)")].iterrows():
                for ds in ref.index:
                    if r.dataset == ds:
                        rows.append({"base model": b, "dataset": ds, "off-the-shelf nDCG@10": f"{ref.loc[ds, 'ndcg@10']:.3f}",
                                     "fine-tuned nDCG@10": f"{r['ndcg@10']:.3f}", "Δ": f"{r['ndcg@10'] - ref.loc[ds, 'ndcg@10']:+.3f}",
                                     "off-the-shelf Recall@10": f"{ref.loc[ds, 'recall@10']:.3f}", "fine-tuned Recall@10": f"{r['recall@10']:.3f}",
                                     "Δ ": f"{r['recall@10'] - ref.loc[ds, 'recall@10']:+.3f}", "run": r.model})
        (tables / "forgetting.md").write_text(md_table(pd.DataFrame(rows)), encoding="utf-8")

    make_figures(base, runs, fts, curve, figs)
    print("tables:", sorted(p.name for p in tables.glob("*.md")))
    print("figures:", sorted(p.name for p in figs.glob("*.png")))


def make_figures(base: pd.DataFrame, runs: pd.DataFrame, fts: list[str], curve: dict, figs: Path) -> None:
    # Figure 1: base vs fine-tuned for each fine-tuned model (grouped bars, direct value labels)
    if fts:
        fig, axes = plt.subplots(1, len(fts), figsize=(5.6 * len(fts), 4.2), sharey=True, squeeze=False)
        x, w = np.arange(len(METRICS)), 0.38
        for ax, m in zip(axes[0], fts):
            b = base_row(base, m)
            r = runs_for(runs, m, True, 1.0)
            bv = [b[k] for k in METRICS]
            fv = [r[f"test_split_{k}"].astype(float).mean() for k in METRICS]
            fe = [r[f"test_split_{k}"].astype(float).std(ddof=1) if len(r) > 1 else 0 for k in METRICS]
            ax.bar(x - w / 2 - 0.01, bv, w, color=BLUE, label="Off the shelf")
            ax.bar(x + w / 2 + 0.01, fv, w, color=ORANGE, yerr=fe, error_kw={"ecolor": INK2, "lw": 1, "capsize": 3}, label="Fine-tuned")
            for xi, v in zip(x - w / 2 - 0.01, bv):
                ax.text(xi, v + 0.012, f"{v:.2f}", ha="center", va="bottom", fontsize=8, color=INK2)
            for xi, v, e in zip(x + w / 2 + 0.01, fv, fe):
                ax.text(xi, v + e + 0.012, f"{v:.2f}", ha="center", va="bottom", fontsize=8, color=INK2)
            ax.set_xticks(x, [LABELS[k] for k in METRICS])
            ax.set_ylim(0, 1.05)
            ax.set_title(m, loc="left", fontsize=11, color=INK)
            ax.grid(axis="x", visible=False)
        axes[0][0].set_ylabel("score (test set)")
        axes[0][0].legend(frameon=False, loc="lower right")
        fig.suptitle("Retrieval on held-out documents: off the shelf vs fine-tuned", x=0.01, ha="left", fontsize=12)
        fig.tight_layout()
        fig.savefig(figs / "base_vs_finetuned.png", dpi=160)
        plt.close(fig)

    # Figure 2: training-data size (bge-small), mean +/- std band vs off-the-shelf line
    if curve:
        fig, ax = plt.subplots(figsize=(5.8, 3.8))
        xs = sorted(curve)
        mu = np.array([curve[f].mean() for f in xs])
        sd = np.array([curve[f].std(ddof=1) if len(curve[f]) > 1 else 0 for f in xs])
        ax.plot([f * 100 for f in xs], mu, color=BLUE, lw=2, marker="o", ms=7, label="Fine-tuned (hard negatives)")
        ax.fill_between([f * 100 for f in xs], mu - sd, mu + sd, color=BLUE, alpha=0.15, lw=0)
        b = base_row(base, "bge-small")["ndcg@10"]
        ax.axhline(b, color=ORANGE, lw=2, ls=(0, (5, 3)), label="Off the shelf")
        ax.set_xticks([25, 50, 100], ["25%", "50%", "100%"])
        ax.set_xlabel("share of training questions used")
        ax.set_ylabel("nDCG@10 (test)")
        ax.set_title("bge-small: more training data", loc="left", fontsize=11)
        ax.legend(frameon=False, loc="lower right")
        fig.tight_layout()
        fig.savefig(figs / "data_size.png", dpi=160)
        plt.close(fig)

    # Figure 3: hard negatives on/off
    rows = [(m, hn, runs_for(runs, m, hn, 1.0)["test_split_ndcg@10"].astype(float)) for m in fts for hn in (False, True)]
    if rows and all(len(r[2]) for r in rows):
        fig, ax = plt.subplots(figsize=(5.6, 3.8))
        x, w = np.arange(len(fts)), 0.36
        for j, (hn, color, label) in enumerate(((False, BLUE, "In-batch negatives only"), (True, ORANGE, "+ mined hard negatives"))):
            vals = [runs_for(runs, m, hn, 1.0)["test_split_ndcg@10"].astype(float) for m in fts]
            mu = [v.mean() for v in vals]
            sd = [v.std(ddof=1) if len(v) > 1 else 0 for v in vals]
            ax.bar(x + (j - 0.5) * (w + 0.02), mu, w, color=color, yerr=sd, error_kw={"ecolor": INK2, "lw": 1, "capsize": 3}, label=label)
            for xi, v, e in zip(x + (j - 0.5) * (w + 0.02), mu, sd):
                ax.text(xi, v + e + 0.01, f"{v:.3f}", ha="center", va="bottom", fontsize=8, color=INK2)
        ax.set_xticks(x, fts)
        ax.set_ylim(0, 1.0)
        ax.set_ylabel("nDCG@10 (test)")
        ax.set_title("Do hard negatives help?", loc="left", fontsize=11)
        ax.legend(frameon=False, loc="lower right")
        ax.grid(axis="x", visible=False)
        fig.tight_layout()
        fig.savefig(figs / "hard_negatives.png", dpi=160)
        plt.close(fig)


if __name__ == "__main__":
    main()
