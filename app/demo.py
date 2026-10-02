"""Gradio demo: base vs fine-tuned retrieval, side by side.

Run:  python app/demo.py --ft-model models/bge-small_hn_100_s42/final
      python app/demo.py --ft-model <your-hf-username>/bge-small-fastapi-docs   (after pushing to the Hub)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gradio as gr  # noqa: E402

from src.data import load_chunks  # noqa: E402
from src.rag import Retriever  # noqa: E402
from src.retrieval import load_model  # noqa: E402
from src.utils import DEFAULT_CONFIG, load_config  # noqa: E402

EXAMPLES = [
    "How do I make a query parameter optional in FastAPI?",
    "Why does Pydantic coerce the string '123' into an int?",
    "How do I run code on app startup and shutdown?",
    "What is the difference between response_model and the return type annotation?",
    "How can I send a response header from a path operation?",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--base", default="bge-small")
    parser.add_argument("--ft-model", required=True, help="path or Hub id of the fine-tuned model")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    cfg = load_config(args.config)
    mcfg = cfg["models"][args.base]
    chunks = load_chunks(cfg)

    retrievers = {}
    for label, source in (("Base", mcfg), ("Fine-tuned", args.ft_model)):
        model = load_model(source)
        model.max_seq_length = mcfg["max_seq_length"]
        retrievers[label] = Retriever(model, chunks, mcfg["query_prefix"])

    def search(query: str) -> tuple[str, str]:
        out = []
        for label in ("Base", "Fine-tuned"):
            hits = retrievers[label].retrieve([query], args.top_k)[0]
            out.append("\n\n".join(f"**{i}. {c['chunk_id']}**\n\n{c['text'][:500]}…" for i, c in enumerate(hits, 1)))
        return out[0], out[1]

    with gr.Blocks(title="Base vs fine-tuned retrieval") as demo:
        gr.Markdown("# Base vs fine-tuned embeddings\nTop passages from the FastAPI / Pydantic / Starlette docs.")
        box = gr.Textbox(label="Question", placeholder="Ask about FastAPI, Pydantic or Starlette")
        with gr.Row():
            left, right = gr.Markdown(label="Base"), gr.Markdown(label="Fine-tuned")
        gr.Examples(EXAMPLES, inputs=box)
        box.submit(search, box, [left, right])
    demo.launch()


if __name__ == "__main__":
    main()
