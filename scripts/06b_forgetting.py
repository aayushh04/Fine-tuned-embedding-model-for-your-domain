"""Phase 6e: forgetting check on general-domain BEIR subsets (SciFact, NFCorpus).

Compares each base model with its fine-tuned versions on out-of-domain retrieval. A fall in nDCG@10 /
recall@10 on these sets means fine-tuning on FastAPI/Pydantic/Starlette questions cost general ability.

Data comes from the `mteb/<dataset>` repos on the Hugging Face Hub (BEIR corpus, queries, test qrels).
Relevance is binary (qrels score > 0) so nDCG@10 is not identical to the official graded BEIR number.

Usage: python scripts/06b_forgetting.py --runs bge-small_hn_100_s42 minilm_hn_100_s42
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from huggingface_hub import hf_hub_download  # noqa: E402

from src.retrieval import evaluate_retrieval, load_model  # noqa: E402
from src.utils import DEFAULT_CONFIG, append_csv_row, load_config, set_seed  # noqa: E402


def load_beir(name: str, max_queries: int, seed: int):
    get = lambda f: hf_hub_download(f"mteb/{name}", f, repo_type="dataset")
    corpus = {}
    for line in open(get("corpus.jsonl"), encoding="utf-8"):
        d = json.loads(line)
        corpus[str(d["_id"])] = (d.get("title", "") + ". " + d["text"]).strip(". ")
    queries = {str(d["_id"]): d["text"] for d in map(json.loads, open(get("queries.jsonl"), encoding="utf-8"))}
    qrels: dict[str, set[str]] = {}
    for line in open(get("qrels/test.tsv"), encoding="utf-8").read().splitlines()[1:]:
        qid, did, score = line.split("\t")
        if float(score) > 0 and qid in queries and did in corpus:
            qrels.setdefault(qid, set()).add(did)
    qids = sorted(qrels)
    import random
    random.Random(seed).shuffle(qids)
    qids = sorted(qids[:max_queries])
    return corpus, [queries[q] for q in qids], [qrels[q] for q in qids]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--runs", nargs="+", required=True, help="run names under models/ (their base model is parsed from the name)")
    args = parser.parse_args()
    cfg = load_config(args.config)
    fcfg = cfg["forgetting"]
    set_seed(cfg["seed"])

    out = cfg["paths"]["results_dir"] / "forgetting.csv"
    out.unlink(missing_ok=True)
    data = {d: load_beir(d, fcfg["max_queries"], cfg["seed"]) for d in fcfg["datasets"]}
    done_base = set()
    for run in args.runs:
        base = next(m for m in cfg["models"] if run.startswith(m + "_"))
        candidates = []
        if base not in done_base:
            candidates.append((f"{base} (base)", load_model(cfg["models"][base]), base))
            done_base.add(base)
        candidates.append((run, load_model(str(cfg["paths"]["models_dir"] / run / "final")), base))
        for label, model, b in candidates:
            model.max_seq_length = cfg["models"][b]["max_seq_length"]
            for dname, (corpus, queries, rel) in data.items():
                res = evaluate_retrieval(model, list(corpus), list(corpus.values()), queries, rel,
                                         query_prefix=cfg["models"][b]["query_prefix"], batch_size=64)
                row = {"model": label, "base": b, "dataset": dname, "n_queries": len(queries), "n_docs": len(corpus),
                       "ndcg@10": round(res.metrics["ndcg@10"], 4), "recall@10": round(res.metrics["recall@10"], 4),
                       "mrr@10": round(res.metrics["mrr@10"], 4)}
                append_csv_row(out, row)
                print(row)


if __name__ == "__main__":
    main()
