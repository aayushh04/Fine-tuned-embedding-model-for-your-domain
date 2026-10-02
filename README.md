# Fine-Tuned Embedding Model for Domain Retrieval

Fine-tune a small open-source embedding model on synthetic question–passage pairs from a domain corpus, measure retrieval gains over the off-the-shelf base model on a held-out test set, and verify that end-to-end RAG answer quality improves too.

> Status: work in progress — Phase 1 (corpus) done.

**Domain:** the Python web-API stack — documentation of FastAPI, Pydantic and Starlette, pinned to release tags (FastAPI 0.115.12, Pydantic 2.11.7, Starlette 0.46.2) so the corpus is reproducible.

## Pipeline

| Phase | Description | Status |
|---|---|---|
| 1 | Corpus collection, chunking, document-level train/val/test split | ✅ |
| 2 | Synthetic question generation + filtering | ⬜ |
| 3 | Evaluation harness + off-the-shelf baselines | ⬜ |
| 4 | Hard negative mining (with false-negative guards) | ⬜ |
| 5 | Fine-tuning (MultipleNegativesRankingLoss) | ⬜ |
| 6 | Ablations: base vs FT, hard negatives, data size, base model, forgetting | ⬜ |
| 7 | End-to-end RAG evaluation | ⬜ |
| 8 | Packaging: Hugging Face model + model card, demo | ⬜ |

## Repo structure

```
configs/     config.yaml — seeds, model names, paths, hyperparameters
data/        raw/ processed/ synthetic/ triplets/ (gitignored)
src/         library code (chunking, generation, eval, mining, training, RAG)
scripts/     one entry-point script per phase
results/     runs.csv, tables/, figures/
notebooks/   analysis
app/         optional demo
```

## Results

### Phase 1 — corpus

| Split | Docs | Chunks |
|---|---|---|
| train | 111 | 1,449 |
| val | 24 | 172 |
| test | 37 | 425 |
| **total** | **172** | **2,046** |

- Chunks: 63–342 tokens (median 247), counted with the `bge-small-en-v1.5` tokenizer; structure-aware (never split mid-paragraph or mid-code-block unless the block itself is too long), ≤50 tokens overlap, each prefixed with a breadcrumb like `FastAPI > Request Body > Create your data model`.
- Split by **document**, stratified by library, balanced by chunk count. Docs with >40 chunks are forced into train so no single page dominates evaluation (largest test doc = 9% of test).
- 99 duplicate chunks removed (FastAPI reuses the same code example across pages); leakage checks: 0 docs in multiple splits, 0 duplicate chunk bodies across splits.

## Reproduce

```bash
py -3.11 -m venv .venv          # Python 3.11 recommended (torch/faiss wheels)
.venv\Scripts\activate           # Windows  (source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
python scripts/01_build_corpus.py   # -> data/processed/chunks.jsonl, doc_splits.json
```

All settings (sources, chunk sizes, split ratios, seed) live in `configs/config.yaml`. Rerunning produces byte-identical outputs.

## Limitations

- Duplicate detection is exact-match only; near-duplicates (e.g. the same example in two Python-version variants) can still cross splits.
- Only the first tab of each multi-version code example is kept (usually the newest Python syntax).
