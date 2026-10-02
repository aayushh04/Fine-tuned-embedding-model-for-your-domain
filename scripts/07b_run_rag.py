"""Phase 7b: run the same RAG pipeline with the base and the fine-tuned embedder.

Everything except the embedder is identical (same corpus = ALL chunks, same top-5, same generator,
greedy decoding). Writes:
  results/rag_outputs.jsonl      full outputs for both systems + automatic metrics per question
  data/rag/judge_sheet.md        blinded sheet (answers labelled X / Y in random order) for manual scoring
  data/rag/blind_key.json        which label is which system (do not open before scoring)

Automatic metrics per question: hit@5 (gold chunk among the 5 retrieved), cites_gold (answer cites the
gold passage), valid_citations (every [n] points to a retrieved passage), refused ("cannot find"),
answer_sim (cosine between the answer and the reference answer, bge-base).

Usage: python scripts/07b_run_rag.py --base bge-small --ft-run bge-small_hn_100_s42
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

from src.data import load_chunks  # noqa: E402
from src.llm import LocalChat  # noqa: E402
from src.rag import Retriever, answer_questions, cited_ids  # noqa: E402
from src.retrieval import encode, load_model  # noqa: E402
from src.utils import DEFAULT_CONFIG, load_config, read_jsonl, set_seed, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--base", default="bge-small")
    parser.add_argument("--ft-run", required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    rcfg = cfg["rag"]
    set_seed(cfg["seed"])
    rag_dir = cfg["paths"]["processed_dir"].parent / "rag"

    rows = list(read_jsonl(rag_dir / "rag_questions.jsonl"))
    refs = {r["qid"]: r["answer"] for r in read_jsonl(rag_dir / "reference_answers.jsonl")}
    assert all(r["qid"] in refs for r in rows), "missing reference answers"
    chunks = load_chunks(cfg)
    questions = [r["question"] for r in rows]
    prefix = cfg["models"][args.base]["query_prefix"]

    systems = {"base": load_model(cfg["models"][args.base]),
               "finetuned": load_model(str(cfg["paths"]["models_dir"] / args.ft_run / "final"))}
    retrieved = {}
    for name, model in systems.items():
        model.max_seq_length = cfg["models"][args.base]["max_seq_length"]
        retrieved[name] = Retriever(model, chunks, prefix).retrieve(questions, rcfg["top_k"])
    del systems
    torch.cuda.empty_cache()

    llm = LocalChat(rcfg["generator"])
    answers = {n: answer_questions(llm, questions, retrieved[n], max_new_tokens=rcfg["max_new_tokens"]) for n in retrieved}
    del llm
    torch.cuda.empty_cache()

    sim_model = load_model(cfg["models"]["bge-base"])
    ref_emb = encode(sim_model, [refs[r["qid"]] for r in rows])
    out = []
    for i, r in enumerate(rows):
        rec = {"qid": r["qid"], "question": r["question"], "qtype": r["qtype"],
               "gold_chunk_id": r["gold_chunk_id"], "reference": refs[r["qid"]]}
        for n in retrieved:
            ids = [c["chunk_id"] for c in retrieved[n][i]]
            cites = cited_ids(answers[n][i])
            ans_emb = encode(sim_model, [answers[n][i]])
            rec[n] = {"retrieved": ids, "answer": answers[n][i], "hit@5": r["gold_chunk_id"] in ids,
                      "cites_gold": any(1 <= c <= len(ids) and ids[c - 1] == r["gold_chunk_id"] for c in cites),
                      "valid_citations": bool(cites) and all(1 <= c <= len(ids) for c in cites),
                      "refused": "cannot find this" in answers[n][i].lower(),
                      "answer_sim": round(float(ans_emb[0] @ ref_emb[i]), 4)}
        out.append(rec)
    write_jsonl(cfg["paths"]["results_dir"] / "rag_outputs.jsonl", out)

    # blinded judging sheet
    rng = random.Random(cfg["seed"])
    key, lines = {}, ["# RAG judging sheet (blinded)\n"]
    for rec in out:
        order = ["base", "finetuned"]
        rng.shuffle(order)
        key[rec["qid"]] = {"X": order[0], "Y": order[1]}
        lines.append(f"## {rec['qid']} ({rec['qtype']})\n**Question:** {rec['question']}\n\n**Reference:** {rec['reference']}\n\n"
                     f"**Answer X:** {rec[order[0]]['answer']}\n\n**Answer Y:** {rec[order[1]]['answer']}\n\n---\n")
    (rag_dir / "judge_sheet.md").write_text("\n".join(lines), encoding="utf-8")
    (rag_dir / "blind_key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    print({n: sum(r[n]["hit@5"] for r in out) for n in ("base", "finetuned")}, "gold hits@5 out of", len(out))


if __name__ == "__main__":
    main()
