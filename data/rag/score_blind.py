"""Blind manual scores for the RAG comparison, written by Claude while reading data/rag/judge_sheet.md.

The sheet shows, per question, the reference answer and two answers labelled X and Y in random order; the key mapping
labels to systems (data/rag/blind_key.json) was NOT opened until all 50 questions were scored.

Rubric (fixed before scoring):
  correct (0-2): 2 = agrees with the reference on all key facts; 1 = partly correct / misses a key part / right idea but wrong
                 details; 0 = wrong, unrelated, or does not answer
  halluc  (0/1): 1 = states specifics that contradict the reference or look fabricated (invented API, wrong code, invented
                 claims); a plain refusal or a vague answer is not a hallucination
Note on truncation: answers are cut at 200 generated tokens; the sheet shows exactly what was generated.

Run: python data/rag/score_blind.py  -> writes data/rag/judge_scores.json
"""
import json
from pathlib import Path

# qid: (X_correct, X_halluc, Y_correct, Y_halluc)
S = {
    "r00": (2, 0, 2, 0), "r01": (0, 1, 2, 0), "r02": (1, 0, 0, 0), "r03": (0, 1, 2, 0), "r04": (0, 1, 0, 1),
    "r05": (1, 1, 1, 1), "r06": (1, 0, 1, 0), "r07": (2, 0, 2, 0), "r08": (1, 0, 1, 0), "r09": (2, 0, 2, 0),
    "r10": (1, 1, 1, 1), "r11": (0, 1, 1, 0), "r12": (1, 0, 0, 0), "r13": (0, 1, 1, 0), "r14": (1, 0, 1, 0),
    "r15": (2, 0, 2, 0), "r16": (2, 0, 2, 0), "r17": (0, 1, 0, 1), "r18": (2, 0, 2, 0), "r19": (0, 1, 0, 1),
    "r20": (2, 0, 2, 0), "r21": (1, 0, 1, 0), "r22": (1, 0, 1, 0), "r23": (0, 1, 0, 1), "r24": (0, 0, 0, 1),
    "r25": (0, 0, 1, 0), "r26": (0, 1, 0, 0), "r27": (2, 0, 1, 0), "r28": (1, 0, 0, 1), "r29": (2, 0, 0, 1),
    "r30": (1, 0, 2, 0), "r31": (1, 0, 2, 0), "r32": (1, 0, 0, 1), "r33": (2, 0, 2, 0), "r34": (2, 1, 2, 0),
    "r35": (2, 0, 2, 0), "r36": (1, 0, 0, 1), "r37": (2, 0, 0, 1), "r38": (2, 0, 0, 1), "r39": (2, 0, 2, 0),
    "r40": (0, 1, 0, 1), "r41": (1, 1, 1, 1), "r42": (1, 1, 0, 1), "r43": (2, 0, 0, 1), "r44": (0, 0, 0, 1),
    "r45": (2, 0, 0, 0), "r46": (0, 1, 1, 1), "r47": (0, 1, 1, 0), "r48": (0, 1, 0, 0), "r49": (1, 0, 1, 0),
}
assert len(S) == 50

if __name__ == "__main__":
    out = {q: {"X": {"correct": a, "halluc": b}, "Y": {"correct": c, "halluc": d}} for q, (a, b, c, d) in S.items()}
    Path(__file__).with_name("judge_scores.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(len(out), "questions scored")
