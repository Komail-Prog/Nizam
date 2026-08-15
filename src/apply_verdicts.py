"""
Nizam — Phase 5: apply manual faithfulness verdicts to the saved answers.
Zero Gemini calls. Writes verdict + note into faithfulness_answers.json.
Run from project root:
    python src/apply_verdicts.py
"""
import json
import os

OUT = os.path.join("docs", "eval", "faithfulness_answers.json")

VERDICTS = {
    "Q13": ("faithful",   "ذكر الأساس 21 والتدرّج 30؛ إغفال الفقرة 2 خارج نطاق السؤال"),
    "Q12": ("refused",    "miss استرجاعي (م6 أزاحت م98) انحدر إلى رفض آمن لا هلوسة"),
    "Q14": ("partial",    "ذكر 50% لكن أغفل الفقرة 3: ساعات العطل تُعد إضافية"),
    "Q15": ("partial",    "90 يوماً صحيح لكن أغفل شرط (مهنة أخرى)؛ استشهد بـ53 لا 54"),
    "Q17": ("faithful",   "تطابق شبه كامل: 10-15 شاملة عيد الأضحى + شرط السنتين"),
    "Q08": ("partial",    "ذكر 25 عاملاً+4% لكن أغفل الالتزام الإبلاغي لمكتب العمل"),
    "Q11": ("partial",    "ذكر 4+6 أسابيع لكن أغفل حظر التشغيل 6 أسابيع بعد الوضع"),
    "Q19": ("faithful",   "نقل المادة كاملة؛ الاختبار المعاكس نجح (لا تفصيل ملفّق)"),
    "Q20": ("unfaithful", "أضاف حالات السفن من م182 داخل إجابة م80؛ استشهد [80,182] - تلوّث المرحلة4"),
    "Q23": ("partial",    "الجوهر صحيح لكن أغفل تأجيل 60 والعدول 7؛ استشهد [79] لا [79 مكرر]"),
    "Q25": ("faithful",   "عدّد الجزاءات الستة كاملة بقيود المدة"),
    "Q05": ("faithful",   "نقل الجوهر بأمانة: ديون ممتازة+امتياز+مبلغ معجّل"),
}


def main():
    with open(OUT, encoding="utf-8") as f:
        saved = json.load(f)

    applied, missing = [], []
    for qid, (verdict, note) in VERDICTS.items():
        if qid in saved:
            saved[qid]["verdict"] = verdict
            saved[qid]["note"] = note
            applied.append(qid)
        else:
            missing.append(qid)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=2)

    print(f"طُبّق الحكم على {len(applied)} سؤالاً.")
    if missing:
        print(f"⚠️ غير موجود في المحفوظ: {missing}")

    # ملخّص
    from collections import Counter
    c = Counter(saved[q]["verdict"] for q in saved if saved[q].get("verdict"))
    answered = c["faithful"] + c["partial"] + c["unfaithful"]
    print("=" * 50)
    print(f"✅ أمينة    : {c['faithful']}")
    print(f"⚠️ ناقصة    : {c['partial']}")
    print(f"❌ غير أمينة: {c['unfaithful']}")
    print(f"↩️ رفض      : {c['refused']}  (خارج القياس)")
    print("=" * 50)
    print(f"faithfulness: {c['faithful']}/{answered} أمينة تماماً | إغفال:اختلاق = {c['partial']}:{c['unfaithful']}")


if __name__ == "__main__":
    main()