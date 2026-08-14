"""
Nizam — Phase 5: hit@3 harness for the 28 answerable golden questions.
Retrieval only — ZERO Gemini calls. All 28 queries run in one batch.
Matching is done on normalized display_name (handles mukarrar + whitespace/diacritics).
Run from project root with .venv active:
    python src/eval_hitk.py
"""
import json
import os
from retriever import retrieve
from eval_normalize import normalize_name

GOLDEN = os.path.join("docs", "eval", "golden_questions.json")
K = 3


def load_answerable():
    with open(GOLDEN, encoding="utf-8") as f:
        data = json.load(f)
    return [q for q in data if q["category"] == "answerable"]


def evaluate():
    questions = load_answerable()
    hits = 0
    misses = []
    per_q = []

    for q in questions:
        results = retrieve(q["question"], k=K)
        retrieved_names = [normalize_name(r["display_name"]) for r in results]
        expected = {normalize_name(n) for n in q["expected_display_names"]}

        is_hit = any(rn in expected for rn in retrieved_names)
        hits += 1 if is_hit else 0

        # keep raw (un-normalized) names for human-readable reporting
        raw_retrieved = [r["display_name"] for r in results]
        per_q.append({
            "id": q["id"],
            "hit": is_hit,
            "expected": q["expected_display_names"][0],
            "retrieved": raw_retrieved,
        })
        if not is_hit:
            misses.append((q["id"], q["question"], q["expected_display_names"][0], raw_retrieved))

    total = len(questions)
    rate = hits / total if total else 0.0

    # ---- per-question table ----
    print("=" * 78)
    print(f"{'ID':<5}{'HIT':<6}{'EXPECTED':<18}RETRIEVED (top-3)")
    print("-" * 78)
    for r in per_q:
        mark = "✅" if r["hit"] else "❌"
        print(f"{r['id']:<5}{mark:<6}{r['expected']:<18}{' | '.join(r['retrieved'])}")
    print("=" * 78)
    print(f"hit@{K} = {hits}/{total} = {rate:.1%}")
    print("=" * 78)

    # ---- miss deep-dive (the log-worthy part) ----
    if misses:
        print("\n### MISSES — deep dive (for dev-log) ###")
        for qid, question, exp, got in misses:
            print(f"\n[{qid}] {question}")
            print(f"   expected : {exp}")
            print(f"   retrieved: {got}")
            print(f"   diagnosis: expected article was NOT in top-{K} → retrieval-layer miss")
    else:
        print("\nNo misses. 🎯")

    return rate, per_q


if __name__ == "__main__":
    evaluate()