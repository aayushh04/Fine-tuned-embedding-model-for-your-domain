# Fine-Tuned Embedding Model for Domain Retrieval

Fine-tune a small open-source embedding model on synthetic question–passage pairs from a domain corpus, measure retrieval gains over the off-the-shelf base model on a held-out test set, and verify that end-to-end RAG answer quality improves too.

> Status: work in progress — Phase 0 (project setup).

## Pipeline

| Phase | Description | Status |
|---|---|---|
| 1 | Corpus collection, chunking, document-level train/val/test split | ⬜ |
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

_To be filled in after Phase 3 onward._

## Reproduce

_To be filled in._

## Limitations

_To be filled in._
