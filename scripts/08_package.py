"""Phase 8: build the model card and (optionally) push the fine-tuned model to the Hugging Face Hub.

  python scripts/08_package.py card                       # writes models/<run>/final/README.md and MODEL_CARD.md
  python scripts/08_package.py push --repo-id USER/NAME   # needs HF_TOKEN in the environment (a write token)

The published run is chosen by VALIDATION nDCG@10 among the main configuration's seeds (never by test score).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from src.utils import DEFAULT_CONFIG, load_config  # noqa: E402

CARD = """---
language: en
license: mit
library_name: sentence-transformers
pipeline_tag: sentence-similarity
tags:
  - sentence-transformers
  - sentence-similarity
  - feature-extraction
  - retrieval
  - rag
  - fastapi
  - pydantic
  - starlette
base_model: {hf_name}
---

# {title}

An **{base_model}** embedding model fine-tuned for retrieval over the documentation of **FastAPI, Pydantic and Starlette**.
It maps questions and documentation passages to {dim}-dimensional vectors (cosine similarity).

On held-out documents (never seen in training) it improves nDCG@10 from **{base_ndcg}** to **{ft_ndcg}** and
Recall@1 from **{base_r1}** to **{ft_r1}** over the off-the-shelf base model. See "Evaluation" for the full table and caveats.

## Usage

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("{repo_id}")
query_prefix = "{query_prefix}"            # keep the same instruction prefix the base model uses for queries
q = model.encode([query_prefix + "How do I make a query parameter optional in FastAPI?"], normalize_embeddings=True)
docs = model.encode(["Declare optional query parameters by setting their default to None ..."], normalize_embeddings=True)
print(q @ docs.T)
```

## Training data

* **Corpus:** docs of FastAPI 0.115.12, Pydantic 2.11.7 and Starlette 0.46.2 (markdown from the GitHub release tags), cleaned and
  chunked into {n_chunks} passages of 63-342 tokens with a heading breadcrumb. Split **by document** into train / val / test
  (70 / 10 / 20 by chunk count) *before* any question was generated.
* **Synthetic questions:** 3 questions per chunk (factual / how-to / comparison) written by `Qwen2.5-0.5B-Instruct`, then filtered
  (too short or generic, copied phrases, duplicates, and a round-trip check that the base model retrieves the source chunk in its top 20).
  {n_train_q} training questions remained.
* **Hard negatives:** for each training question one chunk from the base model's ranks 10-50 (train documents only), excluding
  neighbours of the positive, near-copies of it, and anything a cross-encoder (`ms-marco-MiniLM-L-6-v2`) scored close to the positive.

## Training

`MultipleNegativesRankingLoss` (computed with gradient caching, mini-batch 8) on (question, positive, hard negative) triplets, {epochs} epochs max with the best epoch kept by
validation nDCG@10 (best here: epoch {best_epoch}), learning rate {lr}, batch size {batch_size}, 10% warm-up, fp32, seed {seed}, no duplicate chunks per batch.

## Evaluation

Test set: {n_test_q} questions over unseen documents, **written by Claude** (not by the model that wrote the training questions).
Index = the test chunks only (held-out corpus).

{results_table}

{seed_note}

{context_note}

Details, ablations (hard negatives, data size, second base model),
the forgetting check and an end-to-end RAG evaluation are in the project README: {repo_url}

## Limitations

* Trained and evaluated on **synthetic** questions about three libraries' docs; real user questions are messier.
* Small test set ({n_test_q} questions): differences of a point or two are within noise (see the confidence intervals in the repo).
* Tied to the documentation versions above; newer releases may reorganise or change behaviour.
* May lose some general-domain retrieval ability (see the forgetting check in the repo).
* English only. Max sequence length 384 tokens.
"""


def best_run(runs: pd.DataFrame, model: str) -> pd.Series:
    r = runs[(runs.model == model) & (runs.hard_negatives == True) & (runs.frac == 1.0)]  # noqa: E712
    return r.sort_values("val_split_ndcg@10", ascending=False).iloc[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["card", "push"])
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--model", default="bge-small")
    parser.add_argument("--repo-id", default="YOUR_HF_USERNAME/bge-small-fastapi-docs")
    parser.add_argument("--repo-url", default="https://github.com/aayushh04/Fine-tuned-embedding-model-for-your-domain")
    args = parser.parse_args()
    cfg = load_config(args.config)
    res = cfg["paths"]["results_dir"]
    runs, base = pd.read_csv(res / "runs.csv"), pd.read_csv(res / "baselines.csv")
    run = best_run(runs, args.model)
    mcfg = cfg["models"][args.model]
    b = base[(base.model == args.model) & (base.split == "test") & (base.corpus == "split") & (base.qset == "filtered")].iloc[0]
    sel = runs[(runs.model == args.model) & (runs.hard_negatives == True) & (runs.frac == 1.0)]  # noqa: E712
    cols = ["recall@1", "recall@5", "recall@10", "mrr@10", "ndcg@10"]
    table = "| model | " + " | ".join(cols) + " |\n|---|" + "---|" * len(cols) + "\n"
    table += f"| {args.model} (off the shelf) | " + " | ".join(f"{b[c]:.3f}" for c in cols) + " |\n"
    if len(sel) > 1:
        fmt = lambda c: f"{sel[f'test_split_{c}'].mean():.3f} ± {sel[f'test_split_{c}'].std(ddof=1):.3f}"
    else:
        fmt = lambda c: f"{sel[f'test_split_{c}'].iloc[0]:.3f}"
    table += "| **this model** | " + " | ".join(fmt(c) for c in cols) + " |\n"
    ref = base[(base.model == "bge-small") & (base.split == "test") & (base.corpus == "split") & (base.qset == "filtered")].iloc[0]
    table += "| bge-small (off the shelf, for reference) | " + " | ".join(f"{ref[c]:.3f}" for c in cols) + " |\n"
    seed_note = f"Mean ± std over {len(sel)} training seeds." if len(sel) > 1 else f"Single training run (seed {int(run.seed)})."
    context_note = ("**Reading the table honestly:** this fine-tune brings a small, fast model most of the way to the stronger "
                    "off-the-shelf bge-small on this domain; it does not beat it. Fine-tuning bge-small itself on the same data "
                    "did not improve its score on the Claude-written test questions (it improved on validation questions written "
                    "like the training data), so the gain is largest for weaker base models.")
    card = CARD.format(
        hf_name=mcfg["hf_name"], base_model=mcfg["hf_name"].split("/")[-1], title=args.repo_id.split("/")[-1],
        dim=384, repo_id=args.repo_id, repo_url=args.repo_url, query_prefix=mcfg["query_prefix"],
        base_ndcg=f"{b['ndcg@10']:.3f}", ft_ndcg=f"{sel['test_split_ndcg@10'].mean():.3f}",
        base_r1=f"{b['recall@1']:.3f}", ft_r1=f"{sel['test_split_recall@1'].mean():.3f}",
        n_chunks=2046, n_train_q=int(run.n_train_examples), n_test_q=int(b.n_queries), epochs=int(run.epochs_max),
        best_epoch=int(run.best_epoch), lr=run.lr, batch_size=int(run.batch_size), seed=int(run.seed),
        results_table=table, seed_note=seed_note, context_note=context_note)
    model_dir = cfg["paths"]["models_dir"] / run.run / "final"
    (model_dir / "README.md").write_text(card, encoding="utf-8")
    (res.parent / "MODEL_CARD.md").write_text(card, encoding="utf-8")
    print(f"model card written for run {run.run} (val nDCG@10 {run['val_split_ndcg@10']:.3f})")

    if args.action == "push":
        from huggingface_hub import HfApi
        token = os.environ.get("HF_TOKEN")
        if not token:
            raise SystemExit("Set HF_TOKEN (a Hugging Face *write* token) first.")
        api = HfApi(token=token)
        api.create_repo(args.repo_id, exist_ok=True)
        api.upload_folder(folder_path=str(model_dir), repo_id=args.repo_id, ignore_patterns=["checkpoints/*"])
        print(f"pushed to https://huggingface.co/{args.repo_id}")


if __name__ == "__main__":
    main()
