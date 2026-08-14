"""
Nizam — Phase 5: refusal-path harness for unanswerable questions.
USES GEMINI (2 calls per question). Runs in batches to respect the 20/day quota.
Results accumulate in docs/eval/refusal_results.json — already-run IDs are skipped.
Run from project root with .venv active:
    python src/eval_refusal.py Q29 Q30 Q31 Q32      # today's batch
    python src/eval_refusal.py Q33 Q34 Q35          # tomorrow's batch
"""
import json
import os
import sys
import time
from generator import answer_gated_merged

GOLDEN = os.path.join("docs", "eval", "golden_questions.json")
OUT = os.path.join("docs", "eval", "refusal_results.json")
DELAY = 13  # نفس تباعد generator.py — الحدّ 5 طلبات/دقيقة


def load_golden():
    with open(GOLDEN, encoding="utf-8") as f:
        return json.load(f)


def load_prev():
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def main(target_ids):
    golden = {q["id"]: q for q in load_golden() if q["category"] == "unanswerable"}
    done = load_prev()

    todo = [qid for qid in target_ids if qid in golden and qid not in done]
    skipped = [qid for qid in target_ids if qid in done]
    invalid = [qid for qid in target_ids if qid not in golden]

    if invalid:
        print(f"⚠️ تجاهل معرّفات ليست unanswerable: {invalid}")
    if skipped:
        print(f"↩️  مُشغَّلة مسبقاً (تُتخطّى): {skipped}")
    if not todo:
        print("لا جديد لتشغيله في هذه الدفعة.")
    else:
        est_calls = len(todo) * 2
        print(f"سأشغّل {len(todo)} سؤالاً ≈ {est_calls} نداء Gemini. تباعد {DELAY}s.\n")

    for i, qid in enumerate(todo):
        q = golden[qid]
        print(f"[{qid}] {q['question']}")
        res = answer_gated_merged(q["question"])
        refused = (res.get("answered") is False)
        record = {
            "id": qid,
            "question": q["question"],
            "refused": refused,
            "reason": res.get("reason") if refused else None,
            "leaked_answer": None if refused else res.get("answer", "")[:200],
        }
        done[qid] = record
        mark = "✅ رفض صحيح" if refused else "❌ أجاب (تسريب)"
        print(f"    → {mark}" + (f"  [{record['reason']}]" if refused else ""))
        if not refused:
            print(f"    ⚠️ سرّب: {record['leaked_answer']}")
        print()

        # اكتب بعد كل سؤال (حماية من انقطاع منتصف الدفعة)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(done, f, ensure_ascii=False, indent=2)

        if i < len(todo) - 1:
            time.sleep(DELAY)

    # ملخّص تراكمي
    all_unans = [q for q in load_golden() if q["category"] == "unanswerable"]
    run = [done[q["id"]] for q in all_unans if q["id"] in done]
    if run:
        good = sum(1 for r in run if r["refused"])
        print("=" * 60)
        print(f"إجمالي المُشغَّل: {len(run)}/{len(all_unans)}  |  رفض صحيح: {good}/{len(run)}")
        print("=" * 60)


if __name__ == "__main__":
    ids = sys.argv[1:]
    if not ids:
        print("مرّر معرّفات الأسئلة، مثال: python src/eval_refusal.py Q29 Q30 Q31 Q32")
        sys.exit(1)
    main(ids)