# Interview questions (with answers grounded in this project)

Two or three per phase. The answers use the real numbers and decisions from this repo, so you can speak about them from experience.
Read the README's "What the results mean" section first.

## Phase 1: corpus, chunking, split

**1. Why split by document instead of by chunk, and what would contaminated numbers look like?**
Neighbouring chunks of one page share terms, examples and overlapping text. If some are in train and some in test, the model has effectively
seen the answers, so test scores inflate and no longer measure generalisation to new documents. Here the split is by document, done before any
question exists, with a check that no document and no chunk body appears in two splits (FastAPI repeats code examples across pages, so
99 duplicates were removed first). Contaminated numbers would show up as a large train-to-test gain with a tiny train-to-val gap.

**2. Why were very long pages forced into train?**
Pydantic's validation-error catalogue alone was 31% of the test set. A single page can dominate and make the test score depend on one topic.
Capping eval documents at 40 chunks kept the largest test document at 9% of the test set.

**3. Why count chunk size with the embedding model's tokenizer?**
"350 tokens" must mean what the model sees. The model truncates at its max length, so words or characters would mis-estimate and
silently cut the end of long chunks.

## Phase 2: synthetic questions

**1. How do you stop an LLM from writing questions that just copy the passage?**
Prompt rules (own words, no 4+ word phrases) plus a hard filter: reject any question sharing a 6+ word run with its chunk (136 were rejected).

**2. What does the round-trip check do and what bias does it add?**
It keeps a question only if the base model retrieves its source chunk in the top 20. It removes vague or wrong questions (681 dropped) but also removes
the questions the base model finds hardest, which can favour the base model and shrink the apparent gain. It also leaves mostly "already easy"
training examples. Check: results on the unfiltered questions are reported and do not change the conclusions.

**3. Why did the test questions come from a different author than the training questions?**
To measure generalisation and not just agreement with the generator's style. It exposed that 5-7 points of the apparent gain were specific
to the training writer's phrasing.

## Phase 3: baselines and the evaluation harness

**1. Why build the harness before training?**
Every later number (validation each epoch, ablations, forgetting, RAG retrieval) goes through the same function, so comparisons are
apples to apples and a harness bug cannot be tuned around. One call encodes the corpus once and scores every setting.

**2. Explain Recall@k, MRR@10 and nDCG@10 for a single correct passage.**
Recall@k: is the correct passage in the top k. MRR@10: 1 / rank of the correct passage (0 if outside the top 10). nDCG@10: same idea with a log
discount, 1 / log2(rank + 1), normalised by the best possible score. With one correct passage, nDCG and MRR both reward rank 1 most.

**3. Your strongest baseline had Recall@10 = 0.998. What did that tell you before training?**
That there was almost no headroom at the top of the list; improvements could only appear in Recall@1 / MRR. It predicted the result for bge-small.

## Phase 4: hard negatives

**1. What is a false negative and how did you guard against it?**
A "negative" passage that actually answers the question; training on it pushes the model away from a correct answer. Guards: exclude
neighbours of the positive in the same document, exclude near-copies (cosine > 0.9), and drop candidates a cross-encoder scores close to the
positive. For bge-small this removed about 2,300 candidates the cross-encoder judged likely correct.

**2. Why mine negatives from train chunks only?**
Mining from val or test chunks would put test text into training (as negatives), leaking information about the evaluation corpus.

**3. Hard negatives made little difference here. Why might that be?**
The positives were already easy (round-trip filtered) and the questions are in a narrow style, so the loss was small even with harder
negatives. With one seed per ablation the measured differences (+0.4 nDCG) are inside the noise.

## Phase 5: fine-tuning

**1. How does MultipleNegativesRankingLoss work and why a batch sampler that avoids duplicates?**
Each question's positive is the right class among all passages in the batch (positives and hard negatives of every example act as negatives).
If the same chunk appears twice in a batch, one copy is a *false* in-batch negative, so the no-duplicates sampler removes that.

**2. You trained with gradient caching. Why, and does it change the result?**
Batch 32 with 96 passages did not fit in 4 GB (out-of-memory, 30+ seconds per step). Cached MNRL computes the same loss and gradients over
the full batch of 32 but runs the model in mini-batches of 8, so the maths is the same and only the memory use changes.

**3. Why validate every epoch and keep the best checkpoint, and why is the test set touched only at the end?**
Validation guards against overfitting by choosing the epoch; if you pick the epoch or hyperparameters on test, the test number becomes optimistic.
Here validation also picked which seed's model to publish and use for RAG.

## Phase 6: ablations

**1. Fine-tuning helped MiniLM by 8 points and did nothing for bge-small. How do you explain it?**
Headroom (0.76 vs 0.85) and generalisation: the training data teaches the generator's style and some real domain vocabulary. A weak
model gains both; a strong one already has the vocabulary and only the style gain remains, which does not transfer to differently written questions.

**2. How did you test whether the gain was real, not noise?**
Paired bootstrap over test queries on the per-query nDCG@10 (MiniLM +0.078, CI [+0.052, +0.103], 149 better / 63 worse; bge-small
−0.010, CI [−0.028, +0.008]) and three seeds for the main comparison (std about 0.003).

**3. What did the forgetting check show and how much weight should it get?**
Changes under half a point on SciFact and NFCorpus. With only 300 queries per set the noise is about ±3 points, so the correct statement
is "no detectable forgetting", not "no forgetting".

## Phase 7: end-to-end RAG

**1. Retrieval got better for MiniLM; did RAG answers get better?**
Not measured for MiniLM (the RAG test used bge-small, whose retrieval did not improve). For bge-small the answers were not better
(0.94 vs 0.98 correctness, p = 0.66), which is consistent with unchanged retrieval.

**2. What limited answer quality more than the embedder?**
The 0.5B generator: a third of its answers contained hallucinated specifics and it never produced inline citations. A stronger generator
would make embedder differences easier to see.

**3. How did you reduce bias in the manual scoring?**
The rubric was fixed first, answers were shown as X/Y in random order with the system key unopened until all 50 were scored, and the scores are
committed (`data/rag/score_blind.py`). Remaining weakness: a single judge who also wrote the references.

## Phase 8: packaging

**1. Which model did you publish and why that one?**
The MiniLM fine-tune, because it shows a robust improvement; the model card says bge-small off the shelf is still slightly stronger, so nobody is misled.

**2. What is in a good model card for a fine-tuned embedding model?**
Base model, data and how it was made, training setup, evaluation with the baseline next to it, intended use, and limits (synthetic data, small
test set, language, sequence length).

**3. What would you do next with another week?**
Get real or human-written questions (even 200 of them), generate harder questions with a stronger LLM, run more seeds for every ablation,
fine-tune a stronger generator for the RAG step, and re-test whether bge-small can still be improved.
