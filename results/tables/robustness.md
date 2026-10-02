| model | setting | base nDCG@10 | fine-tuned nDCG@10 | base Recall@1 | fine-tuned Recall@1 |
|---|---|---|---|---|---|
| bge-small | held-out corpus, filtered questions (primary) | 0.851 | 0.840 ± 0.003 | 0.685 | 0.669 ± 0.006 |
| bge-small | all chunks indexed, filtered questions | 0.795 | 0.790 ± 0.003 | 0.605 | 0.602 ± 0.008 |
| bge-small | held-out corpus, unfiltered questions | 0.817 | 0.819 ± 0.003 | 0.654 | 0.642 ± 0.006 |
| minilm | held-out corpus, filtered questions (primary) | 0.763 | 0.841 | 0.571 | 0.666 |
| minilm | all chunks indexed, filtered questions | 0.682 | 0.785 | 0.492 | 0.584 |
| minilm | held-out corpus, unfiltered questions | 0.737 | 0.818 | 0.546 | 0.639 |
