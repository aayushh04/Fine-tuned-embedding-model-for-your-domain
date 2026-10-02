"""Phase 5: fine-tune an embedding model with MultipleNegativesRankingLoss.

Examples
  python scripts/05_train.py --model bge-small --name bge-small_hn_100_s42
  python scripts/05_train.py --model bge-small --no-hard-negatives --frac 0.5 --seed 43 --name bge-small_nohn_50_s43

* Training data: filtered TRAIN questions only (val/test chunks are never seen). With hard negatives each
  example is (question, positive, negative), otherwise (question, positive).
* Loss = MultipleNegativesRankingLoss computed with gradient caching (CachedMultipleNegativesRankingLoss):
  mathematically the same loss over the full batch of 32, but the forward/backward pass runs in mini-batches
  so it fits in 4 GB of GPU memory.
* In-batch negatives come for free from MNRL; the NO_DUPLICATES batch sampler prevents the same chunk
  appearing twice in a batch (which would create false in-batch negatives).
* Validation: IR evaluator on the VAL split (val chunks as corpus) after every epoch; the best epoch is kept.
* After training the best checkpoint is evaluated on val and test with the project harness and one row is
  appended to results/runs.csv (with per-epoch validation curves in results/epochs.csv).
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch  # noqa: E402
from datasets import Dataset  # noqa: E402
from sentence_transformers import SentenceTransformerTrainer, SentenceTransformerTrainingArguments  # noqa: E402
from sentence_transformers.evaluation import InformationRetrievalEvaluator  # noqa: E402
from sentence_transformers.losses import CachedMultipleNegativesRankingLoss  # noqa: E402
from sentence_transformers.training_args import BatchSamplers  # noqa: E402

from src.data import chunks_by_id, load_chunks, load_questions  # noqa: E402
from src.evaluate import eval_all, result_row, save_per_query  # noqa: E402
from src.retrieval import load_model  # noqa: E402
from src.utils import DEFAULT_CONFIG, append_csv_row, load_config, read_jsonl, set_seed  # noqa: E402


def build_train_dataset(cfg: dict, model_name: str, use_hn: bool, frac: float, seed: int) -> tuple[Dataset, dict]:
    prefix = cfg["models"][model_name]["query_prefix"]
    by_id = chunks_by_id(load_chunks(cfg))
    if use_hn:
        rows = list(read_jsonl(cfg["paths"]["triplets_dir"] / f"{model_name}_triplets.jsonl"))
    else:
        rows = [q for q in load_questions(cfg) if q["split"] == "train"]
    assert all(by_id[r["positive_chunk_id"]]["split"] == "train" for r in rows), "non-train chunk in training data"
    random.Random(seed).shuffle(rows)
    rows = rows[: max(1, round(len(rows) * frac))]
    data = {"anchor": [prefix + r["question"] for r in rows],
            "positive": [by_id[r["positive_chunk_id"]]["text"] for r in rows]}
    if use_hn:
        assert all(by_id[r["negative_chunk_id"]]["split"] == "train" for r in rows)
        data["negative"] = [by_id[r["negative_chunk_id"]]["text"] for r in rows]
    info = {"n_train_examples": len(rows), "n_fallback_negatives": sum(r.get("neg_kind") == "fallback" for r in rows)}
    return Dataset.from_dict(data), info


def build_val_evaluator(cfg: dict, model_name: str) -> InformationRetrievalEvaluator:
    prefix = cfg["models"][model_name]["query_prefix"]
    chunks = [c for c in load_chunks(cfg) if c["split"] == "val"]
    qs = [q for q in load_questions(cfg) if q["split"] == "val"]
    return InformationRetrievalEvaluator(
        queries={f"q{i}": prefix + q["question"] for i, q in enumerate(qs)},
        corpus={c["chunk_id"]: c["text"] for c in chunks},
        relevant_docs={f"q{i}": {q["positive_chunk_id"]} for i, q in enumerate(qs)},
        mrr_at_k=[10], ndcg_at_k=[10], accuracy_at_k=[1, 5, 10], precision_recall_at_k=[10],
        name="val", show_progress_bar=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--model", default="bge-small")
    parser.add_argument("--no-hard-negatives", action="store_true")
    parser.add_argument("--frac", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--tag", default="", help="free-text label stored in runs.csv (e.g. the ablation it belongs to)")
    args = parser.parse_args()
    cfg = load_config(args.config)
    tcfg = cfg["training"]
    seed = args.seed if args.seed is not None else cfg["seed"]
    epochs = args.epochs or tcfg["epochs"]
    lr = args.lr or tcfg["lr"]
    use_hn = not args.no_hard_negatives
    name = args.name or f"{args.model}_{'hn' if use_hn else 'nohn'}_{round(args.frac * 100)}_s{seed}"
    set_seed(seed)

    mcfg = cfg["models"][args.model]
    model = load_model(mcfg)
    train_ds, info = build_train_dataset(cfg, args.model, use_hn, args.frac, seed)
    evaluator = build_val_evaluator(cfg, args.model)
    out_dir = cfg["paths"]["models_dir"] / name
    use_fp16 = tcfg["fp16"] and torch.cuda.is_available()

    train_args = SentenceTransformerTrainingArguments(
        output_dir=str(out_dir / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=tcfg["batch_size"],
        per_device_eval_batch_size=64,
        learning_rate=lr,
        warmup_ratio=tcfg["warmup_ratio"],
        weight_decay=tcfg["weight_decay"],
        fp16=use_fp16,
        batch_sampler=BatchSamplers.NO_DUPLICATES,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="eval_val_cosine_ndcg@10",
        greater_is_better=True,
        logging_steps=10,
        seed=seed, data_seed=seed,
        report_to="none",
    )
    trainer = SentenceTransformerTrainer(
        model=model, args=train_args, train_dataset=train_ds,
        loss=CachedMultipleNegativesRankingLoss(model, mini_batch_size=tcfg["mini_batch_size"]),
        evaluator=evaluator,
    )
    t0 = time.time()
    trainer.train()
    minutes = (time.time() - t0) / 60

    # per-epoch validation curve
    curve = [h for h in trainer.state.log_history if "eval_val_cosine_ndcg@10" in h]
    best_epoch = max(curve, key=lambda h: h["eval_val_cosine_ndcg@10"])["epoch"]
    for h in curve:
        append_csv_row(cfg["paths"]["results_dir"] / "epochs.csv",
                       {"run": name, "epoch": h["epoch"], "val_ndcg@10": round(h["eval_val_cosine_ndcg@10"], 4),
                        "val_mrr@10": round(h["eval_val_cosine_mrr@10"], 4),
                        "val_recall@10": round(h["eval_val_cosine_recall@10"], 4),
                        "is_best": h["epoch"] == best_epoch})
    model.save(str(out_dir / "final"))

    # final evaluation with the shared harness (test is touched exactly once per finished run)
    chunks = load_chunks(cfg)
    qf, qa = load_questions(cfg, "questions.jsonl"), load_questions(cfg, "questions_all.jsonl")
    row = {"run": name, "tag": args.tag, "model": args.model, "hard_negatives": use_hn, "frac": args.frac,
           "seed": seed, "epochs_max": epochs, "best_epoch": best_epoch, "lr": lr, "batch_size": tcfg["batch_size"],
           "fp16": use_fp16, "train_minutes": round(minutes, 1), **info}
    res = eval_all(model, chunks, {"filtered": qf, "unfiltered": qa}, mcfg["query_prefix"],
                   settings=[("filtered", s, c) for s in ("val", "test") for c in ("split", "all")]
                   + [("unfiltered", "test", "split")])
    save_per_query(res, cfg["paths"]["results_dir"] / "per_query" / f"{name}.npz")
    for (qset, split, corpus), r in res.items():
        prefix_name = f"{split}_{corpus}" if qset == "filtered" else f"{split}_unfiltered"
        row.update({f"{prefix_name}_{k}": v for k, v in result_row(r).items() if k != "n_queries"})
    append_csv_row(cfg["paths"]["results_dir"] / "runs.csv", row)
    print({k: v for k, v in row.items() if k.startswith("test_split") or k in ("run", "best_epoch", "train_minutes")})


if __name__ == "__main__":
    main()
