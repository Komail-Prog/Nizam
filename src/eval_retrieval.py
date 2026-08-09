"""
Nizam — Phase 2 gate: measure hit@k on a known-answer question set.
Each case: question -> the article number(s) that correctly answer it.
"""
from search_hybrid import hybrid_search

# Ground truth: verified from the actual law text we inspected.
# A case passes if ANY expected article appears in the top-k results.
TEST_SET = [
    {"q": "كيف تحسب مكافأة نهاية الخدمة؟", "expected": [84]},
    {"q": "كم مكافأة نهاية الخدمة عند الاستقالة؟", "expected": [85]},
    {"q": "ما هي حالات فسخ العقد دون مكافأة؟", "expected": [80]},
    {"q": "ما مدة الإجازة السنوية؟", "expected": [109]},
    {"q": "ما هي أحكام الاستقالة؟", "expected": [79]},  # 79 mukarrar
    {"q": "ما تعريف الأجر الأساسي؟", "expected": [2]},
    {"q": "كم ساعات العمل اليومية؟", "expected": [98]},
    {"q": "ما حقوق المرأة العاملة في إجازة الوضع؟", "expected": [151]},
    {"q": "ما نص المادة 109؟", "expected": [109]},
    {"q": "ما عقوبة تشغيل حدث في عمل خطر؟", "expected": [161, 162]},
]


def article_num_from_name(name):
    """Extract the integer article number from a display_name."""
    import re
    m = re.search(r"\d+", name)
    return int(m.group()) if m else None


def evaluate(k=3):
    passed = 0
    print(f"{'#':<3} {'السؤال':<45} {'متوقّع':<12} {'top-k':<22} {'✓'}")
    print("=" * 95)
    for i, case in enumerate(TEST_SET, 1):
        names, _ = hybrid_search(case["q"], k=k)
        got_nums = [article_num_from_name(n) for n in names]
        hit = any(e in got_nums for e in case["expected"])
        passed += hit
        mark = "✅" if hit else "❌"
        exp = ",".join(map(str, case["expected"]))
        got = ",".join(str(n) for n in got_nums)
        print(f"{i:<3} {case['q'][:43]:<45} {exp:<12} {got:<22} {mark}")
    print("=" * 95)
    print(f"hit@{k}: {passed}/{len(TEST_SET)} = {passed/len(TEST_SET)*100:.0f}%")
    return passed


if __name__ == "__main__":
    evaluate(k=3)