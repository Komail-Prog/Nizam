# src/generator.py — المرحلة 3: التوليد المقيّد بالاستشهاد + بوابة الرفض
import os
import json
import time
from google import genai
from google.genai import errors as genai_errors
from dotenv import load_dotenv
from retriever import retrieve

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-2.5-flash"

REFUSAL_MESSAGE = "لا أستطيع الإجابة على هذا من نظام العمل"

SYSTEM_INSTRUCTION = """أنت مساعد متخصص في نظام العمل السعودي فقط.
يُعطى لك سؤال المستخدم ومجموعة من المواد النظامية المسترجَعة.
مهمتك: الإجابة بالاعتماد على هذه المواد وحدها، دون أي معرفة خارجية.

قواعد صارمة:
- أجب فقط مما ورد في المواد المعطاة. لا تستخدم أي معلومة من خارجها.
- إذا لم تُجب أيٌّ من المواد المعطاة عن السؤال، اجعل can_answer=false ولا تحاول التخمين.
- في used_articles ضع أرقام المواد التي استندت إليها فعلاً فقط (من المواد المعطاة).
- اكتب الإجابة بالعربية الفصحى، موجزة ودقيقة.

أعِد ردك حصراً بصيغة JSON صالحة بهذا الشكل، دون أي نص قبله أو بعده ودون علامات ```:
{"can_answer": true/false, "used_articles": [أرقام], "answer": "نص الإجابة"}"""


def build_context(articles: list) -> str:
    """يحوّل المواد المسترجَعة إلى نص يُمرَّر للنموذج."""
    blocks = []
    for a in articles:
        blocks.append(f"[المادة {a['article_number']}]\n{a['text']}")
    return "\n\n".join(blocks)


def answer(query: str, k: int = 3, max_retries: int = 3) -> dict:
    """يسترجع المواد ويسأل Gemini مع إعادة محاولة عند الأخطاء العابرة."""
    articles = retrieve(query, k=k)
    context = build_context(articles)

    user_prompt = f"""السؤال: {query}

المواد المسترجَعة:
{context}"""

    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            raw = json.loads(response.text)
            return {"raw": raw, "articles": articles}
        except (genai_errors.APIError, json.JSONDecodeError, Exception) as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # 1s ثم 2s ثم 4s
                print(f"  ⚠️ محاولة {attempt + 1} فشلت ({type(e).__name__})، إعادة بعد {wait}s…")
                time.sleep(wait)

    raise RuntimeError(f"فشل نداء Gemini بعد {max_retries} محاولات: {last_error}")

import re

def _normalize_article_numbers(used: list) -> list:
    """يستخرج أرقام المواد الصحيحة من أي صيغة يرجعها Gemini.
    يقبل: 107 (int) · "107" (str) · "المادة 107" · "المادة ١٠٧".
    يتجاهل أي عنصر لا يحوي رقماً.
    """
    normalized = []
    for item in used:
        if isinstance(item, int):
            normalized.append(item)
            continue
        s = str(item)
        # تحويل الأرقام العربية-الهندية إلى لاتينية
        s = s.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
        match = re.search(r"\d+", s)
        if match:
            normalized.append(int(match.group()))
    return normalized

def answer_gated(query: str, k: int = 3) -> dict:
    """الواجهة الحقيقية للمرحلة 3: تطبّق الحرّاس الثلاثة وتُرجع نتيجة نهائية."""
    result = answer(query, k=k)
    raw = result["raw"]
    articles = result["articles"]

    retrieved_map = {a["article_number"]: a for a in articles}

    # الحارس 1: قرار Gemini بعدم القدرة على الإجابة → رفض
    if not raw.get("can_answer", False):
        return {"answered": False, "message": REFUSAL_MESSAGE, "reason": "llm_cannot_answer"}

    used = _normalize_article_numbers(raw.get("used_articles", []))

    # الحارس 1-ب: ادّعى القدرة بلا مواد → رفض (تناقض)
    if not used:
        return {"answered": False, "message": REFUSAL_MESSAGE, "reason": "no_articles_cited"}

    # الحارس 2: رقم خارج المسترجَع = هلوسة → رفض
    hallucinated = [n for n in used if n not in retrieved_map]
    if hallucinated:
        return {"answered": False, "message": REFUSAL_MESSAGE,
                "reason": f"hallucinated_articles:{hallucinated}"}

    # الحارس 3: الاستشهادات من نص retrieve الرسمي، لا من Gemini
    citations = [{"article_number": n, "text": retrieved_map[n]["text"]} for n in used]

    return {"answered": True, "answer": raw["answer"], "citations": citations}


def _print_result(query: str, res: dict) -> None:
    """طباعة مقروءة للاختبار اليدوي."""
    print("=" * 70)
    print("السؤال:", query)
    if not res["answered"]:
        print("النتيجة: ⛔ رفض —", res["message"], f"({res['reason']})")
    else:
        print("النتيجة: ✅ إجابة")
        print("الجواب:", res["answer"])
        for c in res["citations"]:
            print(f"\n  📌 المادة {c['article_number']}:")
            print(f"  {c['text']}")


if __name__ == "__main__":
    answerable = [
        "كم مدة إجازة الوضع للمرأة العاملة؟",              # 151
        "ما مدة فترة التجربة القصوى للعامل؟",              # 53
        "هل يحق للعامل أجر عن ساعات العمل الإضافية؟",       # 107
        "متى يحق لصاحب العمل فسخ العقد دون مكافأة؟",        # 80
        "ما حقوق العامل عند إصابته بإصابة عمل؟",            # ~137
    ]
    unanswerable = [
        "ما عقوبة تجاوز السرعة على الطريق السريع؟",
        "ما حقوق المستأجر إذا امتنع المالك عن الصيانة؟",
        "كيف أجدد رخصة القيادة في السعودية؟",
    ]

    DELAY = 13  # ثوانٍ بين النداءات — الحدّ المجاني 5 طلبات/دقيقة

    print("\n########## أسئلة قابلة للإجابة (متوقَّع: ✅) ##########")
    for q in answerable:
        _print_result(q, answer_gated(q))
        time.sleep(DELAY)

    print("\n########## أسئلة غير قابلة (متوقَّع: ⛔ رفض) ##########")
    for i, q in enumerate(unanswerable):
        _print_result(q, answer_gated(q))
        if i < len(unanswerable) - 1:
            time.sleep(DELAY)