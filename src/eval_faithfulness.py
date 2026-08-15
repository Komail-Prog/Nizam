"""
Nizam — Phase 5: faithfulness harness (manual judgment).
Two phases, separated on purpose:
  PHASE A (--run):   call answer_gated_merged for the 12 sample Qs, SAVE answers.
                     Uses Gemini (~12 calls, one per Q after the merge).
  PHASE B (--judge): print (question + official article text + system answer)
                     side-by-side so YOU judge ✅/⚠️/❌. Zero Gemini calls.
                     Re-runnable anytime; answers are cached.
Run from project root, .venv active:
    python src/eval_faithfulness.py --run      # today, spends quota
    python src/eval_faithfulness.py --judge     # anytime, no quota
"""
import json
import os
import sys
import time
from generator import answer_gated_merged
from retriever import retrieve

GOLDEN = os.path.join("docs", "eval", "golden_questions.json")
OUT = os.path.join("docs", "eval", "faithfulness_answers.json")
DELAY = 20  # هامش آمن للحصة (5/دقيقة)

# العيّنة المعتمدة — 8 عالية الخطورة + 4 متنوعة
SAMPLE_IDS = ["Q13", "Q12", "Q14", "Q15", "Q17", "Q08", "Q11", "Q19",
              "Q20", "Q23", "Q25", "Q05"]


def load_golden():
    with open(GOLDEN, encoding="utf-8") as f:
        return {q["id"]: q for q in json.load(f)}


def load_saved():
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def run():
    """PHASE A: استدعاء النظام للـ 12 سؤالاً وحفظ الإجابات (يصرف حصة)."""
    golden = load_golden()
    saved = load_saved()
    todo = [qid for qid in SAMPLE_IDS if qid not in saved]

    if not todo:
        print("كل الـ 12 محفوظة. شغّل --judge للحكم.")
        return
    print(f"سأشغّل {len(todo)} سؤالاً ≈ {len(todo)} نداء (نداء واحد لكل سؤال بعد الدمج). تباعد {DELAY}s.\n")

    for i, qid in enumerate(todo):
        q = golden[qid]
        print(f"[{qid}] {q['question']}")
        try:
            res = answer_gated_merged(q["question"])
        except Exception as e:
            print(f"    ❌ استثناء: {type(e).__name__}: {e}  — يُترك لإعادة لاحقة\n")
            if i < len(todo) - 1:
                time.sleep(DELAY)
            continue

        # نجلب نص المادة المتوقّعة رسمياً (الحقيقة التي نحكم عليها)
        expected_name = q["expected_display_names"][0]
        saved[qid] = {
            "id": qid,
            "question": q["question"],
            "expected_article": expected_name,
            "answered": res.get("answered"),
            "path": res.get("path"),
            "system_answer": res.get("answer") if res.get("answered") else f"[رفض: {res.get('reason')}]",
            "cited_articles": [c["article_number"] for c in res.get("citations", [])],
            "verdict": None,   # يملؤه الحكم اليدوي لاحقاً
            "note": "",
        }
        print(f"    ✅ حُفظ [path={res.get('path')}, answered={res.get('answered')}]\n")

        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(saved, f, ensure_ascii=False, indent=2)
        if i < len(todo) - 1:
            time.sleep(DELAY)

    print(f"حُفظ في {OUT}. شغّل --judge للحكم اليدوي.")


def judge():
    """PHASE B: عرض (سؤال + نص المادة الرسمي + إجابة النظام) للحكم اليدوي. صفر حصة."""
    golden = load_golden()
    saved = load_saved()
    if not saved:
        print("لا إجابات محفوظة. شغّل --run أولاً.")
        return

    for qid in SAMPLE_IDS:
        if qid not in saved:
            print(f"\n[{qid}] ⏳ غير مُشغَّل بعد.")
            continue
        rec = saved[qid]
        # نص المادة الرسمي من retrieve (الحقيقة المرجعية)
        expected = rec["expected_article"]
        hits = retrieve(rec["question"], k=3)
        official = next((h["text"] for h in hits if h["display_name"] == expected), None)
        if official is None:
            # احتياط: اجلبها بالاسم مباشرة
            official = "[لم تظهر المادة المتوقّعة في أعلى 3 — راجع hit@3]"

        print("\n" + "=" * 78)
        print(f"[{qid}] {rec['question']}")
        print(f"المادة المرجعية: {expected}  |  استشهد النظام بـ: {rec['cited_articles']}  |  path={rec['path']}")
        print("-" * 78)
        print("📖 النص الرسمي للمادة:")
        print(f"   {official}")
        print("-" * 78)
        print("🤖 إجابة النظام:")
        print(f"   {rec['system_answer']}")
        print("-" * 78)
        cur = rec.get("verdict")
        print(f"الحكم الحالي: {cur if cur else '— لم يُحكم بعد —'}")
        print("=" * 78)

    # ملخّص
    verdicts = [saved[q].get("verdict") for q in SAMPLE_IDS if q in saved]
    done = [v for v in verdicts if v]
    print(f"\nحُكم على {len(done)}/{len(SAMPLE_IDS)}.")
    if done:
        from collections import Counter
        c = Counter(done)
        print(f"  ✅ أمينة: {c.get('faithful',0)} | ⚠️ ناقصة: {c.get('partial',0)} | ❌ غير أمينة: {c.get('unfaithful',0)}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--run":
        run()
    elif mode == "--judge":
        judge()
    else:
        print("استخدم: --run (يصرف حصة) أو --judge (بلا حصة)")