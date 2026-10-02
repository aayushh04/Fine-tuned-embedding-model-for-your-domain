"""Phase 2b: convert the Claude-written test questions (TSV) into JSONL with real chunk IDs.

The TSV (data/synthetic/test_questions_claude.tsv) has lines `tNNN|type|question`, where tNNN
is the index of the chunk in the *sorted list of test-split chunk_ids*. This script resolves
the keys, validates them and writes data/synthetic/raw_questions_claude.jsonl.

These questions were written by Claude (Sonnet 5.5) while reading each test chunk, so the test
writer is different from the train writer (Qwen2.5-1.5B-Instruct).
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import load_chunks  # noqa: E402
from src.utils import DEFAULT_CONFIG, load_config, write_jsonl  # noqa: E402

QTYPES = {"f": "factual", "h": "how-to", "c": "comparison"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    args = parser.parse_args()
    cfg = load_config(args.config)
    syn = cfg["paths"]["synthetic_dir"]

    test_chunks = sorted((c for c in load_chunks(cfg) if c["split"] == "test"), key=lambda c: c["chunk_id"])
    key_to_chunk = {f"t{i:03d}": c for i, c in enumerate(test_chunks)}

    rows, bad = [], []
    for n, line in enumerate((syn / "test_questions_claude.tsv").read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("|", 2)
        if len(parts) != 3 or parts[0] not in key_to_chunk or parts[1] not in QTYPES:
            bad.append((n, line[:80]))
            continue
        key, qt, question = parts
        c = key_to_chunk[key]
        rows.append({"chunk_id": c["chunk_id"], "doc_id": c["doc_id"], "split": "test",
                     "question": question.strip(), "qtype": QTYPES[qt], "writer": "claude"})
    if bad:
        raise SystemExit(f"{len(bad)} malformed lines, e.g. {bad[:3]}")

    n = write_jsonl(syn / "raw_questions_claude.jsonl", rows)
    covered = len({r["chunk_id"] for r in rows})
    print(f"{n} questions covering {covered}/{len(test_chunks)} test chunks")
    print("types:", dict(Counter(r["qtype"] for r in rows)))


if __name__ == "__main__":
    main()
