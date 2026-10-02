"""Phase 1: download docs -> clean -> chunk -> dedupe -> document-level split.

Outputs (in paths.processed_dir):
  chunks.jsonl        one row per chunk: chunk_id, doc_id, source, section, text, n_tokens, split
  doc_splits.json     doc_id -> split (the split is frozen here, before any questions exist)
  sample_chunks.md    random chunks to eyeball
and results/phase1_corpus_stats.json.

Usage: python scripts/01_build_corpus.py [--config configs/config.yaml]
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tokenizers import Tokenizer  # noqa: E402

from src.chunking import chunk_blocks, make_chunk_text, parse_blocks  # noqa: E402
from src.corpus import download_source, iter_docs  # noqa: E402
from src.splits import SPLITS, normalise_text, check_leakage, split_documents  # noqa: E402
from src.utils import DEFAULT_CONFIG, load_config, set_seed, write_jsonl  # noqa: E402


def title_from_path(path: str) -> str:
    stem = Path(path).stem
    if stem == "index":
        stem = Path(path).parent.name or "Overview"
    return stem.replace("-", " ").replace("_", " ").title()


def build_chunks(cfg: dict) -> list[dict]:
    ccfg = cfg["chunking"]
    tok = Tokenizer.from_pretrained(ccfg["tokenizer"])
    tok.no_truncation()
    count = lambda s: len(tok.encode(s, add_special_tokens=False).ids)

    chunks = []
    for source in cfg["corpus"]["sources"]:
        zip_path = download_source(source, cfg["paths"]["raw_dir"])
        n_docs, missing = 0, []
        for doc in iter_docs(source, zip_path, missing):
            blocks = parse_blocks(doc.text, default_title=title_from_path(doc.path))
            pieces = chunk_blocks(blocks, count, ccfg["chunk_size"], ccfg["overlap"], ccfg["min_tokens"])
            for i, (path, body) in enumerate(pieces):
                text = make_chunk_text(source["label"], path, body)
                chunks.append({
                    "chunk_id": f"{doc.doc_id}#{i:03d}",
                    "doc_id": doc.doc_id,
                    "source": doc.source,
                    "section": " > ".join(path),
                    "text": text,
                    "n_tokens": count(text),
                })
            n_docs += bool(pieces)
        print(f"[{source['name']}] {n_docs} docs with content")
        if missing:
            raise RuntimeError(f"[{source['name']}] {len(missing)} unresolved includes, e.g. {missing[:3]}")
    return chunks


def dedupe(chunks: list[dict]) -> tuple[list[dict], int]:
    """Keep one copy of each chunk body (pages that include the same code example)."""
    seen, kept = set(), []
    for c in sorted(chunks, key=lambda c: c["chunk_id"]):
        key = normalise_text(c["text"].split("\n\n", 1)[-1])
        if key not in seen:
            seen.add(key)
            kept.append(c)
    return kept, len(chunks) - len(kept)


def summarise(chunks: list[dict], n_dupes: int, leak: dict, cfg: dict) -> dict:
    toks = sorted(c["n_tokens"] for c in chunks)
    pct = lambda p: toks[min(len(toks) - 1, int(p / 100 * len(toks)))]
    per_split = {s: {"docs": len({c["doc_id"] for c in chunks if c["split"] == s}),
                     "chunks": sum(c["split"] == s for c in chunks)} for s in SPLITS}
    per_source = defaultdict(Counter)
    for c in chunks:
        per_source[c["source"]][c["split"]] += 1
    return {
        "n_chunks": len(chunks),
        "n_docs": len({c["doc_id"] for c in chunks}),
        "duplicates_removed": n_dupes,
        "tokens": {"min": toks[0], "p5": pct(5), "median": statistics.median(toks),
                   "p95": pct(95), "max": toks[-1], "total": sum(toks),
                   "over_chunk_size": sum(t > cfg["chunking"]["chunk_size"] for t in toks)},
        "per_split": per_split,
        "per_source": {s: dict(c) for s, c in per_source.items()},
        "leakage": {k: len(v) for k, v in leak.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    args = parser.parse_args()
    cfg = load_config(args.config)
    set_seed(cfg["seed"])
    out_dir = cfg["paths"]["processed_dir"]

    chunks = build_chunks(cfg)
    chunks, n_dupes = dedupe(chunks)

    doc_sizes = Counter(c["doc_id"] for c in chunks)
    doc_source = {c["doc_id"]: c["source"] for c in chunks}
    doc_split = split_documents(doc_sizes, doc_source, cfg["split"], cfg["seed"],
                                cfg["split"].get("max_eval_doc_chunks"))
    for c in chunks:
        c["split"] = doc_split[c["doc_id"]]

    leak = check_leakage(chunks)
    assert not leak["docs_in_multiple_splits"], "a document landed in more than one split"
    assert not leak["cross_split_duplicate_groups"], "duplicate chunk text across splits"

    write_jsonl(out_dir / "chunks.jsonl", chunks)
    (out_dir / "doc_splits.json").write_text(json.dumps(doc_split, indent=2, sort_keys=True), encoding="utf-8")

    sample = random.Random(cfg["seed"]).sample(chunks, k=min(10, len(chunks)))
    with open(out_dir / "sample_chunks.md", "w", encoding="utf-8") as f:
        for c in sample:
            f.write(f"## {c['chunk_id']}  ({c['split']}, {c['n_tokens']} tokens)\n\n{c['text']}\n\n---\n\n")

    stats = summarise(chunks, n_dupes, leak, cfg)
    results_dir = cfg["paths"]["results_dir"]
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "phase1_corpus_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
