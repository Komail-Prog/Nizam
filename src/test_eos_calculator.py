"""اختبارات offline للحاسبة — صفر نداءات Gemini."""
import math
from eos_calculator import calculate_eos


def approx(a, b):
    return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6)


def test_termination_basic():
    # 10000 × 7 سنوات = (0.5×5 + 1×2) = 4.5 شهر → 45000
    r = calculate_eos(10000, 7, "termination")
    assert approx(r["final"], 45000)
    assert r["articles"] == [84]


def test_termination_under_five_years():
    # 8000 × 3 سنوات = 0.5×3 = 1.5 شهر → 12000
    r = calculate_eos(8000, 3, "termination")
    assert approx(r["final"], 12000)


def test_fractional_year():
    # أجزاء السنة بالنسبة: 10000 × 2.5 سنة = 0.5×2.5 = 1.25 شهر → 12500
    r = calculate_eos(10000, 2.5, "termination")
    assert approx(r["final"], 12500)


def test_resignation_under_two_years_no_gratuity():
    r = calculate_eos(10000, 1.5, "resignation")
    assert approx(r["final"], 0.0)
    assert r["factor"] == 0.0
    assert 85 in r["articles"]


def test_resignation_two_to_five_one_third():
    # base(10000,4) = 0.5×4=2 شهر → 20000 ؛ ×⅓ → 6666.67
    r = calculate_eos(10000, 4, "resignation")
    assert approx(r["base"], 20000)
    assert approx(r["final"], 20000 / 3.0)


def test_resignation_boundary_exactly_five_is_one_third():
    # Y=5 بالضبط → ثلث (لأن "لا تزيد على خمس" تشمل الخمس)
    r = calculate_eos(10000, 5, "resignation")
    assert approx(r["factor"], 1.0 / 3.0)


def test_resignation_between_five_and_ten_two_thirds():
    # base(10000,7) = 4.5 شهر → 45000 ؛ ×⅔ → 30000
    r = calculate_eos(10000, 7, "resignation")
    assert approx(r["base"], 45000)
    assert approx(r["final"], 30000)


def test_resignation_boundary_exactly_ten_is_full():
    # Y=10 بالضبط → كاملة
    r = calculate_eos(10000, 10, "resignation")
    assert approx(r["factor"], 1.0)
    # base(10000,10) = 0.5×5 + 1×5 = 7.5 شهر → 75000
    assert approx(r["final"], 75000)


def test_resignation_special_is_full():
    # حالة 87: استقالة لكن كاملة
    r = calculate_eos(10000, 4, "resignation_special")
    assert approx(r["factor"], 1.0)
    assert 87 in r["articles"]
    # base(10000,4)=20000 → كاملة → 20000
    assert approx(r["final"], 20000)


def test_negative_wage_raises():
    try:
        calculate_eos(-1, 5, "termination")
        assert False, "should have raised"
    except ValueError:
        pass


def test_unknown_reason_raises():
    try:
        calculate_eos(10000, 5, "quit")  # type: ignore
        assert False, "should have raised"
    except ValueError:
        pass