# Architecture

This project has two halves: an **offline pipeline** that builds a better embedding model, and an **evaluation layer** that
proves (or disproves) that it is better, first for retrieval and then inside a RAG system.

## End-to-end pipeline

```mermaid
flowchart TD
    CFG[/"configs/config.yaml<br/>seeds, models, paths, hyperparameters"/]

    subgraph P1["Phase 1 - corpus"]
        A1["Pinned doc releases<br/>FastAPI 0.115.12, Pydantic 2.11.7, Starlette 0.46.2"] --> A2["Clean markdown<br/>expand code includes, drop site syntax"]
        A2 --> A3["Structure-aware chunks<br/>63-342 tokens, heading breadcrumb, light overlap"]
        A3 --> A4["Split BY DOCUMENT<br/>train 70% / val 10% / test 20%"]
    end

    subgraph P2["Phase 2 - synthetic questions"]
        B1["train + val chunks<br/>Qwen2.5-0.5B writes 3 questions each"]
        B2["test chunks<br/>questions written by Claude"]
        B1 --> B3
        B2 --> B3["Filters: too short / generic / copied phrases /<br/>duplicates / round-trip (source chunk in base top-20)"]
    end

    subgraph P3["Phase 3 - baselines"]
        C1["Eval harness: FAISS, Recall@1/5/10, MRR@10, nDCG@10"]
        C2["Off-the-shelf: all-MiniLM-L6-v2, bge-small, bge-base"]
    end

    subgraph P4["Phase 4 - hard negatives (train chunks only)"]
        D1["Base model top-50<br/>sample from ranks 10-50"]
        D2["False-negative guards:<br/>neighbours of the positive, near-copies,<br/>cross-encoder says it answers the question"]
        D1 --> D2 --> D3["Triplets: question, positive, hard negative"]
    end

    subgraph P5["Phase 5 - fine-tuning"]
        E1["MultipleNegativesRankingLoss (gradient-cached)<br/>lr 2e-5, warm-up, 3 epochs, fp32"]
        E2["Validate every epoch on VAL<br/>keep the best checkpoint"]
        E1 --> E2
    end

    subgraph P6["Phase 6 - ablations (TEST split)"]
        F1["base vs fine-tuned"]
        F2["with vs without hard negatives"]
        F3["25% / 50% / 100% training data"]
        F4["two base models"]
        F5["forgetting check on BEIR SciFact + NFCorpus"]
    end

    subgraph P7["Phase 7 - RAG"]
        G1["Retrieve top-5 from ALL chunks"] --> G2["Qwen2.5-0.5B answers with [n] citations"]
        G2 --> G3["50 test questions, reference answers,<br/>blind manual scoring + automatic metrics"]
    end

    CFG -.-> P1
    A4 --> B1
    A4 --> B2
    B3 --> C1
    C2 --> C1
    B3 -- "train questions" --> D1
    D3 --> E1
    B3 -- "val questions" --> E2
    E2 --> F1
    C1 --> F1
    E2 --> G1
    G3 --> H["Phase 8: README, model card, Hugging Face push, Gradio demo"]
    F5 --> H
    F1 --> H
```

## Data flow and the leakage rules

| Rule | Where it is enforced |
|---|---|
| Split by **document** before any question exists | `scripts/01_build_corpus.py` writes `doc_splits.json`; Phase 2 asserts every question's split matches its chunk's split |
| No duplicate chunk text across splits | `src/splits.py: check_leakage` fails the build if one appears |
| Hard negatives come from **train chunks only** | `scripts/04_mine_negatives.py` builds its index from `split == "train"` |
| Training data contains train chunks only | `scripts/05_train.py` asserts it before training |
| Validation picks the checkpoint, test is read once per finished run | `scripts/05_train.py` |
| The published model is chosen by **validation** score, not test | `scripts/08_package.py: best_run` |
| Train and test questions have different authors | train/val: Qwen2.5-0.5B-Instruct, test: Claude |

## Module map

| Path | Responsibility |
|---|---|
| `configs/config.yaml` | every setting: sources, chunking, split ratios, models, filters, mining, training, RAG |
| `src/corpus.py` | download release zips, strip doc-site markup, expand code includes |
| `src/chunking.py` | block parser and structure-aware chunk packer |
| `src/splits.py` | document-level split and leakage checks |
| `src/filters.py` | rule-based question filters |
| `src/retrieval.py` | embedding, FAISS index, metrics (Recall@k, MRR, nDCG), bootstrap tests |
| `src/evaluate.py` | one `eval_all` call evaluates a model in every setting while encoding the corpus once |
| `src/llm.py`, `src/rag.py` | local LLM wrapper and the retrieve-then-generate pipeline |
| `scripts/01_..08_*` | one entry point per phase; each reads files and writes files, so any phase can be re-run alone |
| `data/` | the hand-off between phases (small files tracked in git, raw downloads ignored) |
| `results/` | CSV logs, tables, figures |

## The evaluation settings

Every model is evaluated on the test questions in two retrieval settings and two question sets:

* **Held-out corpus (primary):** only the test chunks are indexed. This isolates how well the model handles documents it never saw.
* **All chunks indexed:** the whole corpus is the index, so training chunks act as distractors. This is the realistic RAG setting.
* **Filtered questions (primary):** questions that passed the round-trip check against the base model.
* **Unfiltered questions:** the same questions before the round-trip filter, as a check that the filter does not flatter the numbers.

## Hardware notes (why some choices look unusual)

The project was built on a laptop GTX 1650 (4 GB). Measured on that card: fp16 matrix multiplication ran at 0.17 TFLOPS, bf16 at
0.8 and fp32 at 1.4. So everything runs in **fp32**, the LLM used for question generation and answering is the 0.5B model (the
largest that fits in fp32), and training uses **gradient caching** (`CachedMultipleNegativesRankingLoss`, mini-batch 8) to keep the
effective batch size of 32 within memory. These are speed and memory choices; the loss and the data are unchanged.
