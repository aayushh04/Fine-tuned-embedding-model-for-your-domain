"""Phase 2a: generate raw synthetic questions for train/val chunks with a local LLM.

Test-split questions are NOT generated here: they are written by Claude and live in
data/synthetic/test_questions_claude.jsonl, so the test writer differs from the train writer.

Output: data/synthetic/raw_questions_local.jsonl  {chunk_id, doc_id, split, question, qtype}
The script resumes: chunks already present in the output are skipped.

Usage: python scripts/02_generate_questions.py [--splits train val] [--limit N]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch  # noqa: E402
from tqdm import tqdm  # noqa: E402

from src.data import load_chunks  # noqa: E402
from src.llm import LocalChat  # noqa: E402
from src.utils import DEFAULT_CONFIG, load_config, read_jsonl, set_seed  # noqa: E402

SYSTEM = (
    "You write search queries for a developer-documentation search engine. "
    "You are given one passage from the documentation of FastAPI, Pydantic or Starlette."
)

INSTRUCTIONS = """Write exactly 3 questions that a developer might type into a search box or chatbot, such that this passage contains the answer.

Rules:
- Question 1 is a FACTUAL question (what/which/does ...).
- Question 2 is a HOW-TO question (how do I ...).
- Question 3 is a COMPARISON or WHY/WHEN question (difference between, why, when should I ...).
- Each question must make sense on its own, with no passage in front of the reader. Name the library or feature it is about. Never say "the passage", "this text", "the example" or "the code above".
- Use your own words. Do not copy phrases of 4 or more words from the passage.
- Be specific to this passage; do not ask generic questions that many other pages could answer.

Answer with exactly three lines, formatted as:
1. <factual question>
2. <how-to question>
3. <comparison/why/when question>"""

EXAMPLE_PASSAGE = """FastAPI > Query Parameters > Optional parameters

The same way, you can declare optional query parameters, by setting their default to None:

```python
@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None):
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}
```

In this case, the function parameter q will be optional, and will be None by default."""

EXAMPLE_ANSWER = """1. What default value makes a query parameter optional in a FastAPI path operation?
2. How do I let clients leave out a query string argument in my endpoint?
3. Why does FastAPI treat a function argument as optional when it is assigned None?"""

QTYPES = ("factual", "how-to", "comparison")


def build_messages(chunk_text: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Passage:\n{EXAMPLE_PASSAGE}\n\n{INSTRUCTIONS}"},
        {"role": "assistant", "content": EXAMPLE_ANSWER},
        {"role": "user", "content": f"Passage:\n{chunk_text}\n\n{INSTRUCTIONS}"},
    ]


def parse_questions(reply: str) -> list[tuple[str, str]]:
    """Parse '1. ...' lines into (qtype, question) pairs, tolerating minor formatting drift."""
    out = []
    for m in re.finditer(r"^\s*([1-3])[.)]\s*(.+?)\s*$", reply, flags=re.M):
        q = re.sub(r"^<.*?>\s*", "", m.group(2)).strip().strip('"')
        if q.endswith("?") or len(q.split()) >= 4:
            out.append((QTYPES[int(m.group(1)) - 1], q))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--splits", nargs="+", default=["train", "val"])
    parser.add_argument("--limit", type=int, default=None, help="debug: only N chunks")
    args = parser.parse_args()
    cfg = load_config(args.config)
    scfg = cfg["synthetic"]
    set_seed(cfg["seed"])

    out_path = cfg["paths"]["synthetic_dir"] / "raw_questions_local.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = {r["chunk_id"] for r in read_jsonl(out_path)} if out_path.exists() else set()

    chunks = [c for c in load_chunks(cfg) if c["split"] in args.splits and c["chunk_id"] not in done]
    chunks.sort(key=lambda c: c["n_tokens"])  # similar lengths per batch -> less padding
    if args.limit:
        chunks = chunks[: args.limit]
    print(f"{len(chunks)} chunks to process ({len(done)} already done)")

    llm = LocalChat(scfg["local_llm"])
    bs = scfg["batch_size"]
    with open(out_path, "a", encoding="utf-8") as f:
        for i in tqdm(range(0, len(chunks), bs)):
            batch = chunks[i:i + bs]
            replies = llm.generate([build_messages(c["text"]) for c in batch],
                                   max_new_tokens=scfg["max_new_tokens"],
                                   temperature=scfg["temperature"])
            for c, reply in zip(batch, replies):
                for qtype, q in parse_questions(reply):
                    f.write(json.dumps({"chunk_id": c["chunk_id"], "doc_id": c["doc_id"],
                                        "split": c["split"], "question": q, "qtype": qtype,
                                        "writer": "qwen2.5-1.5b"}, ensure_ascii=False) + "\n")
            f.flush()
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
