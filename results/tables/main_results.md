| model | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|---|---|---|---|---|---|
| minilm (off the shelf) | 0.571 | 0.887 | 0.952 | 0.702 | 0.763 |
| minilm fine-tuned (hard negs, 100%, n=1 seeds) | 0.666 | 0.957 | 0.998 | 0.789 | 0.841 |
|   Δ vs off the shelf | +0.095 | +0.069 | +0.045 | +0.087 | +0.078 |
| bge-small (off the shelf) | 0.685 | 0.952 | 0.998 | 0.802 | 0.851 |
| bge-small fine-tuned (hard negs, 100%, n=3 seeds) | 0.669 ± 0.006 | 0.960 ± 0.001 | 0.996 ± 0.002 | 0.790 ± 0.004 | 0.840 ± 0.003 |
|   Δ vs off the shelf | -0.017 | +0.007 | -0.002 | -0.013 | -0.010 |
| bge-base (off the shelf) | 0.662 | 0.952 | 0.991 | 0.788 | 0.839 |
