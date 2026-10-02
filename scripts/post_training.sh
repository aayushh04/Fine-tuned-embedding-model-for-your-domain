#!/usr/bin/env bash
# Runs everything that needs the trained models, in order, once the ablation runs are finished.
#   bash scripts/post_training.sh        (run from the repo root; waits for $TEMP/queue.done)
set -u
cd "$(dirname "$0")/.."
PY=./.venv/Scripts/python.exe
export PYTHONIOENCODING=utf-8
LOG="${TEMP:-/tmp}"

until [ -f "$LOG/queue.done" ]; do sleep 20; done

# 1. same-writer (Qwen) questions for the TEST chunks, for the style-shift diagnostic
$PY scripts/02_generate_questions.py --splits test --out raw_questions_qwen_test.jsonl > "$LOG/style_gen.log" 2>&1

# 2. style-shift check over the main-config seeds
SEEDS=$($PY -c "import pandas as pd; r=pd.read_csv('results/runs.csv'); print(' '.join(r[(r.model=='bge-small')&(r.hard_negatives==True)&(r.frac==1.0)].run))")
$PY scripts/09_style_shift_check.py --runs $SEEDS > "$LOG/style_shift.log" 2>&1

# 3. forgetting check (bge-small best-by-validation run and the MiniLM run)
BEST=$($PY -c "import pandas as pd; r=pd.read_csv('results/runs.csv'); r=r[(r.model=='bge-small')&(r.hard_negatives==True)&(r.frac==1.0)]; print(r.sort_values('val_split_ndcg@10',ascending=False).iloc[0].run)")
echo "$BEST" > "$LOG/best_run.txt"
$PY scripts/06b_forgetting.py --runs "$BEST" minilm_hn_100_s42 > "$LOG/forgetting.log" 2>&1

# 4. RAG: base vs fine-tuned (best-by-validation run), blinded judging sheet
$PY scripts/07b_run_rag.py --base bge-small --ft-run "$BEST" > "$LOG/rag.log" 2>&1

# 5. tables and figures
$PY scripts/06c_make_report.py > "$LOG/report.log" 2>&1
echo POST_DONE > "$LOG/post.done"
