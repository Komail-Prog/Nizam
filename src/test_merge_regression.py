"""
Nizam — Phase 5: regression test for answer_gated_merged (single-call merge).
Compares merged behavior against Phase-4 reference values.
USES GEMINI. ~6 calls total (merged path = 1 call each). Delay 13s.
Run from project root with .venv active:
    python src/test_merge_regression.py
"""
import time
from generator import answer_gated_merged

DELAY = 20

# الحالات المرجعية من المرحلة 4 (قيم مثبَّتة) + عيّنة رفض
CASES = [
    # (وصف، سؤال، تحقّق متوقّع)
    {
        "desc": "حسابي: فصل 10000 × 7 سنوات",
        "q": "فصلني صاحب العمل، راتبي 10000 وخدمتي 7 سنوات، كم مكافأتي؟",
        "expect_path": "tool",
        "expect_answered": True,
        "expect_contains": "45,000",   # القيمة المرجعية من المرحلة 4
    },
    {
        "desc": "حسابي: استقالة 8000 × 4 سنوات",
        "q": "استقلت، راتبي 8000 وخدمتي 4 سنوات، كم أستحق؟",
        "expect_path": "tool",
        "expect_answered": True,
        "expect_contains": "5,333",    # 5333.33 المرجعية
    },
    {
        "desc": "عام قابل: إجازة الوضع",
        "q": "كم مدة إجازة الوضع للمرأة العاملة؟",
        "expect_path": "json",
        "expect_answered": True,
        "expect_contains": None,
    },
    {
        "desc": "عام قابل: فسخ دون مكافأة",
        "q": "متى يحق لصاحب العمل فسخ العقد دون مكافأة؟",
        "expect_path": "json",
        "expect_answered": True,
        "expect_contains": None,
    },
    {
        "desc": "رفض: سؤال خارج النطاق (مرور)",
        "q": "ما عقوبة تجاوز السرعة على الطريق السريع؟",
        "expect_path": "json",
        "expect_answered": False,
        "expect_contains": None,
    },
]


def check(case, res):
    """يقارن النتيجة الفعلية بالمتوقّع، يرجع قائمة أخطاء (فارغة = نجاح)."""
    errors = []
    if res.get("path") != case["expect_path"]:
        errors.append(f"path: توقّع '{case['expect_path']}' لكن '{res.get('path')}'")
    if res.get("answered") != case["expect_answered"]:
        errors.append(f"answered: توقّع {case['expect_answered']} لكن {res.get('answered')}")
    if case["expect_contains"]:
        ans = res.get("answer", "")
        if case["expect_contains"] not in ans:
            errors.append(f"contains: '{case['expect_contains']}' غير موجود في الرد")
    return errors


def main():
    print(f"اختبار انحدار الدمج — {len(CASES)} حالات ≈ {len(CASES)} نداءات (نداء واحد لكل حالة).\n")
    passed = 0
    for i, case in enumerate(CASES):
        print("=" * 70)
        print(f"[{i+1}/{len(CASES)}] {case['desc']}")
        print(f"    السؤال: {case['q']}")
        try:
            res = answer_gated_merged(case["q"])
        except Exception as e:
            print(f"    ❌ استثناء: {type(e).__name__}: {e}")
            if i < len(CASES) - 1:
                time.sleep(DELAY)
            continue

        errors = check(case, res)
        if not errors:
            passed += 1
            print(f"    ✅ نجح  [path={res.get('path')}, answered={res.get('answered')}]")
            if res.get("answered"):
                print(f"    الرد: {res.get('answer','')[:120]}")
            else:
                print(f"    رفض: [{res.get('reason')}]")
        else:
            print(f"    ❌ فشل:")
            for e in errors:
                print(f"        - {e}")
            print(f"    الرد الكامل: path={res.get('path')}, answered={res.get('answered')}, "
                  f"reason={res.get('reason')}, answer={res.get('answer','')[:100]}")

        if i < len(CASES) - 1:
            time.sleep(DELAY)

    print("=" * 70)
    print(f"النتيجة: {passed}/{len(CASES)} نجحت")
    print("=" * 70)
    if passed == len(CASES):
        print("🎯 لا انحدار — الدمج حافظ على السلوك المرجعي. جاهز للتبديل.")
    else:
        print("⚠️ انحدار مكتشَف — لا نبدّل. نشخّص الفروق أعلاه.")


if __name__ == "__main__":
    main()