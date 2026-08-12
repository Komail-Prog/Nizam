"""End-of-service gratuity calculator (Saudi Labor Law, Articles 84/85/87).

دالة نقية بلا أي نداء شبكة — تُختبر offline بالكامل.
القاعدة مستخرجة حرفياً من نص المواد في الـ corpus.
"""
from typing import Literal

EndReason = Literal["termination", "resignation", "resignation_special"]


def calculate_eos(
    last_wage: float,
    years_of_service: float,
    end_reason: EndReason,
) -> dict:
    """تحسب مكافأة نهاية الخدمة وفق المواد 84 و85 و87.

    Args:
        last_wage: الأجر الأخير (رقم واحد جاهز، لا يُفكَّك).
        years_of_service: سنوات الخدمة كرقم عشري (أجزاء السنة بالنسبة).
        end_reason: أحد "termination" / "resignation" / "resignation_special".

    Returns:
        dict فيه: base, factor, factor_reason, final, والمواد المستشهَد بها.
    """
    if last_wage < 0:
        raise ValueError("last_wage must be non-negative")
    if years_of_service < 0:
        raise ValueError("years_of_service must be non-negative")
    if end_reason not in ("termination", "resignation", "resignation_special"):
        raise ValueError(f"unknown end_reason: {end_reason}")

    Y = years_of_service

    # --- الأساس: المادة 84 ---
    first_five = min(Y, 5.0)
    beyond_five = max(Y - 5.0, 0.0)
    months = 0.5 * first_five + 1.0 * beyond_five
    base = last_wage * months

    # --- المعامل: المادة 85 (استقالة) / 84 (إنهاء) / 87 (استثناء) ---
    articles = [84]

    if end_reason == "termination":
        factor = 1.0
        factor_reason = "إنهاء من صاحب العمل — المكافأة كاملة (المادة 84)."

    elif end_reason == "resignation_special":
        factor = 1.0
        factor_reason = "استقالة بحكم استثنائي (قوة قاهرة أو زواج/وضع للعاملة) — كاملة (المادة 87)."
        articles.append(87)

    else:  # resignation
        articles.append(85)
        if Y < 2:
            factor = 0.0
            factor_reason = "استقالة بخدمة أقل من سنتين — لا تُستحق مكافأة (المادة 85)."
        elif Y <= 5:
            factor = 1.0 / 3.0
            factor_reason = "استقالة بخدمة من سنتين إلى خمس سنوات — يُستحق ثلث المكافأة (المادة 85)."
        elif Y < 10:
            factor = 2.0 / 3.0
            factor_reason = "استقالة بخدمة أكثر من خمس وأقل من عشر سنوات — يُستحق ثلثا المكافأة (المادة 85)."
        else:
            factor = 1.0
            factor_reason = "استقالة بخدمة عشر سنوات فأكثر — المكافأة كاملة (المادة 85)."

    final = base * factor

    return {
        "base": base,
        "months_of_base": months,
        "factor": factor,
        "factor_reason": factor_reason,
        "final": final,
        "articles": articles,
        "inputs": {
            "last_wage": last_wage,
            "years_of_service": years_of_service,
            "end_reason": end_reason,
        },
    }