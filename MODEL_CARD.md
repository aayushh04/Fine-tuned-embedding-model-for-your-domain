---
language: en
license: mit
library_name: sentence-transformers
pipeline_tag: sentence-similarity
tags:
  - sentence-transformers
  - sentence-similarity
  - feature-extraction
  - retrieval
  - rag
  - fastapi
  - pydantic
  - starlette
base_model: sentence-transformers/all-MiniLM-L6-v2
---

# minilm-fastapi-docs

An **all-MiniLM-L6-v2** embedding model fine-tuned for retrieval over the documentation of **FastAPI, Pydantic and Starlette**.
It maps questions and documentation passages to 384-dimensional vectors (cosine similarity).

On held-out documents (never seen in training) it improves nDCG@10 from **0.763** to **0.841** and
Recall@1 from **0.571** to **0.666** over the off-the-shelf base model. See "Evaluation" for the full table and caveats.

## Usage

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("YOUR_HF_USERNAME/minilm-fastapi-docs")
query_prefix = ""            # keep the same instruction prefix the base model uses for queries
q = model.encode([query_prefix + "How do I make a query parameter optional in FastAPI?"], normalize_embeddings=True)
docs = model.encode(["Declare optional query parameters by setting their default to None ..."], normalize_embeddings=True)
print(q @ docs.T)
```

## Training data

* **Corpus:** docs of FastAPI 0.115.12, Pydantic 2.11.7 and Starlette 0.46.2 (markdown from the GitHub release tags), cleaned and
  chunked into 2046 passages of 63-342 tokens with a heading breadcrumb. Split **by document** into train / val / test
  (70 / 10 / 20 by chunk count) *before* any question was generated.
* **Synthetic questions:** 3 questions per chunk (factual / how-to / comparison) written by `Qwen2.5-0.5B-Instruct`, then filtered
  (too short or generic, copied phrases, duplicates, and a round-trip check that the base model retrieves the source chunk in its top 20).
  3352 training questions remained.
* **Hard negatives:** for each training question one chunk from the base model's ranks 10-50 (train documents only), excluding
  neighbours of the positive, near-copies of it, and anything a cross-encoder (`ms-marco-MiniLM-L-6-v2`) scored close to the positive.

## Training

`MultipleNegativesRankingLoss` (computed with gradient caching, mini-batch 8) on (question, positive, hard negative) triplets, 3 epochs max with the best epoch kept by
validation nDCG@10 (best here: epoch 2), learning rate 2e-05, batch size 32, 10% warm-up, fp32, seed 42, no duplicate chunks per batch.

## Evaluation

Test set: 461 questions over unseen documents, **written by Claude** (not by the model that wrote the training questions).
Index = the test chunks only (held-out corpus).

| model | recall@1 | recall@5 | recall@10 | mrr@10 | ndcg@10 |
|---|---|---|---|---|---|
| minilm (off the shelf) | 0.571 | 0.887 | 0.952 | 0.702 | 0.763 |
| **this model** | 0.666 | 0.957 | 0.998 | 0.789 | 0.841 |
| bge-small (off the shelf, for reference) | 0.685 | 0.952 | 0.998 | 0.802 | 0.851 |


Single training run (seed 42).

**Reading the table honestly:** this fine-tune brings a small, fast model most of the way to the stronger off-the-shelf bge-small on this domain; it does not beat it. Fine-tuning bge-small itself on the same data did not improve its score on the Claude-written test questions (it improved on validation questions written like the training data), so the gain is largest for weaker base models.

Details, ablations (hard negatives, data size, second base model),
the forgetting check and an end-to-end RAG evaluation are in the project README: https://github.com/aayushh04/Fine-tuned-embedding-model-for-your-domain

## Limitations

* Trained and evaluated on **synthetic** questions about three libraries' docs; real user questions are messier.
* Small test set (461 questions): differences of a point or two are within noise (see the confidence intervals in the repo).
* Tied to the documentation versions above; newer releases may reorganise or change behaviour.
* May lose some general-domain retrieval ability (see the forgetting check in the repo).
* English only. Max sequence length 384 tokens.
