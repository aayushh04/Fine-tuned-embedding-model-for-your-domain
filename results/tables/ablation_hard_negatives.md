| model | training | seeds | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|---|---|---|---|---|---|---|---|
| bge-small | in-batch negatives only | 1 | 0.664 | 0.959 | 0.998 | 0.787 | 0.839 |
| bge-small | + mined hard negatives | 3 | 0.669 ± 0.006 | 0.960 ± 0.001 | 0.996 ± 0.002 | 0.790 ± 0.004 | 0.840 ± 0.003 |
| minilm | in-batch negatives only | 1 | 0.653 | 0.965 | 0.998 | 0.784 | 0.837 |
| minilm | + mined hard negatives | 1 | 0.666 | 0.957 | 0.998 | 0.789 | 0.841 |
