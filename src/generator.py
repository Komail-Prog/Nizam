# src/generator.py — المرحلة 3: التوليد المقيّد بالاستشهاد + بوابة الرفض
import os
import json
import time
from google import genai
from google.genai import errors as genai_errors
from dotenv import load_dotenv
from retriever import retrieve
from google.genai import types

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

# ==================== المرحلة 4: أداة حساب مكافأة نهاية الخدمة ====================

EOS_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="calculate_end_of_service",
            description=(
                "تحسب مكافأة نهاية الخدمة وفق نظام العمل السعودي (المواد 84، 85، 87). "
                "استدعِ هذه الأداة فقط عندما يطلب المستخدم حساب مبلغ المكافأة ويوفّر "
                "الأجر وعدد سنوات الخدمة. لا تستدعها للأسئلة العامة عن أحكام المكافأة "
                "التي لا تتضمن أرقاماً للحساب."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "last_wage": types.Schema(
                        type=types.Type.NUMBER,
                        description="الأجر الأخير للعامل بالريال (رقم واحد).",
                    ),
                    "years_of_service": types.Schema(
                        type=types.Type.NUMBER,
                        description="عدد سنوات الخدمة (يقبل الكسور، مثل 7.5).",
                    ),
                    "end_reason": types.Schema(
                        type=types.Type.STRING,
                        enum=["termination", "resignation", "resignation_special"],
                        description=(
                            "سبب انتهاء العلاقة: "
                            "'termination' إذا أنهى صاحب العمل العقد أو لم يُذكر السبب. "
                            "'resignation' إذا استقال العامل بإرادته. "
                            "'resignation_special' إذا كانت الاستقالة لقوة قاهرة، "
                            "أو العاملة تركت خلال 6 أشهر من الزواج أو 3 أشهر من الوضع."
                        ),
                    ),
                },
                required=["last_wage", "years_of_service", "end_reason"],
            ),
        )
    ]
)

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

from eos_calculator import calculate_eos  # ضعه مع الاستيرادات فوق لاحقاً

# نصوص المواد المرتبطة بالمكافأة — تُجلب من retrieve الرسمي لا من Gemini (نفس مبدأ المرحلة 3)
def _fetch_eos_citations(article_numbers: list) -> list:
    """يجلب نص كل مادة مكافأة من retrieve الرسمي، بضبط بالرقم."""
    citations = []
    for n in article_numbers:
        hits = retrieve(f"المادة {n} مكافأة نهاية الخدمة", k=3)
        match = next((h for h in hits if h["article_number"] == n), None)
        if match:
            citations.append({"article_number": n, "text": match["text"]})
    return citations


def _format_eos_answer(calc: dict) -> str:
    """يصيغ ردّاً عربياً واضحاً من ناتج calculate_eos — بلا نداء Gemini."""
    final = round(calc["final"], 2)
    base = round(calc["base"], 2)
    months = round(calc["months_of_base"], 2)
    wage = calc["inputs"]["last_wage"]
    years = calc["inputs"]["years_of_service"]

    lines = [
        "🧮 **نتيجة استرشادية** (وليست استشارة قانونية):",
        "",
        f"بناءً على أجر أخير قدره {wage:,.0f} ريال، ومدة خدمة {years} سنة:",
        f"• الأساس (المادة 84): {months} شهر × الأجر = {base:,.2f} ريال",
        f"• {calc['factor_reason']}",
        f"• **مكافأة نهاية الخدمة المستحقة (استرشادياً): {final:,.2f} ريال**",
    ]
    return "\n".join(lines)


def answer_with_tool(query: str, k: int = 3, max_retries: int = 3) -> dict:
    """المسار الحسابي: يعطي Gemini الأداة، يلتقط الاستدعاء، يحسب محلياً، يصيغ الرد.
    يرجع None إذا لم يستدعِ Gemini الأداة (أي أن السؤال ليس حسابياً)."""
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=query,
                config=genai.types.GenerateContentConfig(
                    tools=[EOS_TOOL],
                    temperature=0.0,
                ),
            )
            # هل استدعى Gemini الأداة؟
            parts = response.candidates[0].content.parts
            fn_call = next(
                (p.function_call for p in parts if getattr(p, "function_call", None)),
                None,
            )
            if fn_call is None:
                return None  # لم يستدعِ الأداة → ليس سؤالاً حسابياً

            args = dict(fn_call.args)
            calc = calculate_eos(
                last_wage=float(args["last_wage"]),
                years_of_service=float(args["years_of_service"]),
                end_reason=args["end_reason"],
            )
            citations = _fetch_eos_citations(calc["articles"])
            return {
                "answered": True,
                "answer": _format_eos_answer(calc),
                "citations": citations,
                "tool_used": "calculate_end_of_service",
                "tool_args": args,
            }
        except (genai_errors.APIError, Exception) as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  ⚠️ محاولة {attempt + 1} فشلت ({type(e).__name__})، إعادة بعد {wait}s…")
                time.sleep(wait)

    raise RuntimeError(f"فشل نداء الأداة بعد {max_retries} محاولات: {last_error}")

def answer_gated(query: str, k: int = 3) -> dict:
    """الواجهة الموحّدة: تجرّب الأداة الحسابية أولاً، ثم البوابة ثلاثية الحرّاس."""
    # المسار الحسابي (المرحلة 4): إن استدعى Gemini الأداة، نرجع نتيجتها فوراً
    tool_result = answer_with_tool(query, k=k)
    if tool_result is not None:
        return tool_result

    # المسار العادي (المرحلة 3): توليد مقيّد بالاستشهاد + بوابة رفض
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

# ==================== المرحلة 5: الدمج — نداء واحد بدل نداءين ====================

MERGED_SYSTEM_INSTRUCTION = """أنت مساعد متخصص في نظام العمل السعودي فقط.

لديك أداة واحدة: calculate_end_of_service لحساب مكافأة نهاية الخدمة.
- إذا طلب المستخدم حساب مبلغ مكافأة نهاية الخدمة وذكر الأجر وعدد سنوات الخدمة، استدعِ الأداة.
- لا تستدعِ الأداة للأسئلة العامة عن أحكام المكافأة التي لا تتضمن أرقاماً للحساب.

لأي سؤال آخر (لا يستدعي الأداة)، يُعطى لك سؤال المستخدم ومجموعة من المواد النظامية المسترجَعة.
مهمتك: الإجابة بالاعتماد على هذه المواد وحدها، دون أي معرفة خارجية.

قواعد صارمة للإجابة النصية:
- أجب فقط مما ورد في المواد المعطاة. لا تستخدم أي معلومة من خارجها.
- إذا لم تُجب أيٌّ من المواد المعطاة عن السؤال، اجعل can_answer=false ولا تحاول التخمين.
- في used_articles ضع أرقام المواد التي استندت إليها فعلاً فقط (من المواد المعطاة).
- اكتب الإجابة بالعربية الفصحى، موجزة ودقيقة.

عندما لا تستدعي الأداة، أعِد ردك حصراً بصيغة JSON صالحة بهذا الشكل، دون أي نص قبله أو بعده ودون علامات ```:
{"can_answer": true/false, "used_articles": [أرقام], "answer": "نص الإجابة"}"""

def _strip_json_fence(text: str) -> str:
    """يزيل غلاف markdown (```json ... ```) إن وُجد، ويُرجع JSON الصرف.
    يعمل أيضاً لو كان النص JSON صرفاً بلا غلاف (يُرجعه كما هو بعد strip)."""
    t = text.strip()
    if t.startswith("```"):
        # أزل أول سطر (```json أو ```) وآخر سطر (```)
        lines = t.split("\n")
        # أول سطر هو السياج الافتتاحي
        lines = lines[1:]
        # آخر سطر هو السياج الختامي إن كان ```
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    return t

def answer_gated_merged(query: str, k: int = 3, max_retries: int = 3) -> dict:
    """الواجهة الموحّدة المدمجة (المرحلة 5): نداء Gemini واحد.
    يعطي النموذج الأداة + تعليمات JSON + المواد المسترجَعة معاً.
    يفرّع على وجود function_call:
      - إن استدعى الأداة → حساب محلي (مسار المرحلة 4).
      - وإلا → JSON + البوابة ثلاثية الحرّاس (مسار المرحلة 3).
    لا تحذف answer_gated القديمة — هذه نسخة موازية للاختبار قبل التبديل."""
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
                    system_instruction=MERGED_SYSTEM_INSTRUCTION,
                    tools=[EOS_TOOL],
                    temperature=0.0,
                    # ملاحظة: لا نضع response_mime_type=json هنا،
                    # لأن وضع الأداة يتعارض معه. نتحقق من JSON يدوياً أدناه.
                ),
            )
            parts = response.candidates[0].content.parts

            # الفرع أ: هل استدعى الأداة؟
            fn_call = next(
                (p.function_call for p in parts if getattr(p, "function_call", None)),
                None,
            )
            if fn_call is not None:
                args = dict(fn_call.args)
                calc = calculate_eos(
                    last_wage=float(args["last_wage"]),
                    years_of_service=float(args["years_of_service"]),
                    end_reason=args["end_reason"],
                )
                citations = _fetch_eos_citations(calc["articles"])
                return {
                    "answered": True,
                    "answer": _format_eos_answer(calc),
                    "citations": citations,
                    "tool_used": "calculate_end_of_service",
                    "tool_args": args,
                    "path": "tool",
                }

            # الفرع ب: نص JSON → البوابة ثلاثية الحرّاس
            text = next((p.text for p in parts if getattr(p, "text", None)), None)
            if text is None:
                raise ValueError("لا function_call ولا نص في رد Gemini")
            raw = json.loads(_strip_json_fence(text))

            retrieved_map = {a["article_number"]: a for a in articles}

            if not raw.get("can_answer", False):
                return {"answered": False, "message": REFUSAL_MESSAGE,
                        "reason": "llm_cannot_answer", "path": "json"}

            used = _normalize_article_numbers(raw.get("used_articles", []))
            if not used:
                return {"answered": False, "message": REFUSAL_MESSAGE,
                        "reason": "no_articles_cited", "path": "json"}

            hallucinated = [n for n in used if n not in retrieved_map]
            if hallucinated:
                return {"answered": False, "message": REFUSAL_MESSAGE,
                        "reason": f"hallucinated_articles:{hallucinated}", "path": "json"}

            citations = [{"article_number": n, "text": retrieved_map[n]["text"]} for n in used]
            return {"answered": True, "answer": raw["answer"],
                    "citations": citations, "path": "json"}

        except (genai_errors.APIError, json.JSONDecodeError, Exception) as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  ⚠️ محاولة {attempt + 1} فشلت ({type(e).__name__})، إعادة بعد {wait}s…")
                time.sleep(wait)

    raise RuntimeError(f"فشل نداء الدمج بعد {max_retries} محاولات: {last_error}")