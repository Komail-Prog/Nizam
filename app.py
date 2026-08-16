# app.py — واجهة نظام (Nizam): مساعد نظام العمل السعودي
# طبقة عرض Gradio عربية RTL. تستهلك answer_gated_merged كصندوق أسود.
# لا يحتوي هذا الملف أي منطق جوهري: لا استرجاع، لا بوابة، لا حساب.
import html
import os
import re
import sys

# src على الـ path حتى تعمل استيرادات generator المسطّحة (from retriever import ...)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import gradio as gr

# استيراد واحد عند الإقلاع — يحمّل e5 + ChromaDB مرة واحدة ويبقى محمّلاً.
# Gradio لا يعيد تشغيل السكربت مع كل تفاعل، فلا حاجة لأي تخزين مؤقّت.
from generator import answer_gated_merged, REFUSAL_MESSAGE

# ==================== الأسئلة الجاهزة ====================
SAMPLES = [
    ("🧮 حساب مكافأة", "فصلني صاحب العمل، راتبي 10000 وخدمتي 7 سنوات، كم مكافأتي؟"),
    ("📚 سؤال عام", "كم مدة إجازة الوضع للمرأة العاملة؟"),
    ("✅ خارج النطاق", "ما عقوبة تجاوز السرعة على الطريق السريع؟"),
]

QUOTA_MESSAGE = (
    "بلغ الديمو حدّه اليومي من الطلبات المجانية. "
    "جرّب مرة أخرى بعد عدة ساعات — أو شاهد الأمثلة في فيديو العرض بصفحة المشروع."
)


# ==================== أدوات عرض ====================
def _to_html(text: str) -> str:
    """الإجابات تعود بصيغة ماركداون خفيفة (**عريض** وأسطر جديدة).
    نهرّب HTML أولاً ثم نحوّل — حتى تظهر منسّقة دون تمرير وسوم من نص النموذج."""
    out = html.escape(str(text))
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out, flags=re.DOTALL)
    return out.replace("\n", "<br>")


def _panel(badge_class: str, badge_text: str, body_html: str) -> str:
    """شارة المسار + نص الإجابة داخل بطاقة واحدة."""
    return (
        f'<span class="nizam-badge {badge_class}">{badge_text}</span>'
        f'<div class="nizam-answer">{body_html}</div>'
    )


def _citations_html(citations: list) -> str:
    parts = []
    for cite in citations:
        number = html.escape(str(cite.get("article_number", "؟")))
        parts.append(
            f'<div class="nizam-cite-num">المادة {number}</div>'
            f'<div class="nizam-cite-text">{_to_html(cite.get("text", ""))}</div>'
        )
    return "".join(parts)


# ==================== المعالج ====================
def ask(query: str):
    """يُستدعى عند ضغط «اسأل» فقط. يرجع: (بطاقة الإجابة، الاستشهادات، حالة القسم)."""
    question = (query or "").strip()
    if not question:
        return (
            _panel("badge-refuse", "✍️ لا يوجد سؤال",
                   "اكتب سؤالك في الحقل أعلاه، أو اختر سؤالاً جاهزاً ثم اضغط «اسأل»."),
            "",
            gr.update(visible=False),
        )

    try:
        res = answer_gated_merged(question)
    except RuntimeError:
        # استُنفدت المحاولات (429) — الحصة اليومية. رسالة موجِّهة، لا traceback.
        return (
            _panel("badge-refuse", "⏳ الحصة اليومية", QUOTA_MESSAGE),
            "",
            gr.update(visible=False),
        )
    except Exception:
        return (
            _panel("badge-refuse", "⚠️ تعذّر الإكمال",
                   "تعذّر إكمال الطلب حالياً. أعد المحاولة بعد قليل."),
            "",
            gr.update(visible=False),
        )

    # مسار الرفض
    if not res.get("answered", False):
        return (
            _panel("badge-refuse", "↩︎ خارج النطاق",
                   _to_html(res.get("message", REFUSAL_MESSAGE))),
            "",
            gr.update(visible=False),
        )

    # إجابة — الشارة حسب المسار
    if res.get("path") == "tool":
        badge_class, badge_text = "badge-tool", "🧮 نتيجة حاسبة"
    else:
        badge_class, badge_text = "badge-cite", "📚 إجابة مستشهدة"

    panel = _panel(badge_class, badge_text, _to_html(res.get("answer", "")))

    citations = res.get("citations") or []
    if not citations:
        return panel, "", gr.update(visible=False)

    return (
        panel,
        _citations_html(citations),
        gr.update(visible=True, label=f"📎 المواد النظامية المستند إليها ({len(citations)})"),
    )


# ==================== التنسيق ====================
CSS = """
:root {
    --nizam-green: #0B5D3B;
    --nizam-green-soft: #E8F2ED;
    --nizam-ink: #1A1A1A;
    --nizam-muted: #5A6B63;
}

/* عمود متمركز + اتجاه عربي كامل + خلفية فاتحة */
.gradio-container {
    direction: rtl !important;
    font-family: 'Tajawal', 'Noto Kufi Arabic', 'Segoe UI', sans-serif !important;
    max-width: 820px !important;
    margin: 0 auto !important;
    background: #FFFFFF !important;
    color: var(--nizam-ink) !important;
    padding-top: 1.5rem !important;
}
.gradio-container * { font-family: inherit; }
footer { display: none !important; }

/* الرأس */
#nizam-header { text-align: center; margin-bottom: 1.2rem; }
#nizam-header .nizam-title {
    font-family: 'Noto Kufi Arabic', 'Tajawal', sans-serif;
    font-size: 3rem; font-weight: 700; color: var(--nizam-green);
    margin: 0 0 0.4rem 0; line-height: 1.3;
}
#nizam-header .nizam-subtitle {
    font-size: 1.02rem; color: var(--nizam-muted); margin: 0; line-height: 1.9;
}

/* إخلاء المسؤولية — بند إلزامي، بارز */
#nizam-disclaimer .nizam-disclaimer {
    background: #FFF7E6; border: 1px solid #F0D9A0;
    border-right: 5px solid #E6A700;
    color: #7A5A00; padding: 0.85rem 1.1rem; border-radius: 10px;
    font-size: 0.95rem; font-weight: 500; text-align: center;
    margin-bottom: 1.4rem;
}

.nizam-hint { color: var(--nizam-muted); font-size: 0.92rem; margin-bottom: 0.3rem; }

/* الأزرار */
button.nizam-sample {
    border-radius: 10px !important; border: 1px solid #DDE3E0 !important;
    background: #FFFFFF !important; color: var(--nizam-ink) !important;
    font-size: 0.94rem !important; font-weight: 500 !important;
}
button.nizam-sample:hover {
    border-color: var(--nizam-green) !important; color: var(--nizam-green) !important;
    background: var(--nizam-green-soft) !important;
}
button.nizam-ask {
    background: var(--nizam-green) !important; color: #FFFFFF !important;
    border: 1px solid var(--nizam-green) !important;
    font-weight: 700 !important; border-radius: 10px !important;
}
button.nizam-ask:hover { background: #094B30 !important; border-color: #094B30 !important; }

/* حقل الإدخال */
#nizam-input textarea, #nizam-input input {
    direction: rtl !important; text-align: right !important;
    font-size: 1rem !important; border-radius: 10px !important;
    background: #FFFFFF !important; color: var(--nizam-ink) !important;
}

/* شارة المسار */
.nizam-badge {
    display: inline-block; padding: 0.3rem 0.9rem; border-radius: 20px;
    font-size: 0.86rem; font-weight: 500; margin-bottom: 0.7rem;
}
.badge-tool   { background: #E8F2ED; color: #0B5D3B; }
.badge-cite   { background: #E7F0FA; color: #12507E; }
.badge-refuse { background: #FBEAEA; color: #9B2C2C; }

/* بطاقة الإجابة */
.nizam-answer {
    background: #FAFBFA; border: 1px solid #E6EBE8; border-radius: 12px;
    padding: 1.2rem 1.4rem; font-size: 1.06rem; line-height: 2.05;
    color: var(--nizam-ink);
}

/* الاستشهادات */
.nizam-cite-num {
    color: var(--nizam-green); font-weight: 700; font-size: 0.98rem;
    margin-bottom: 0.25rem;
}
.nizam-cite-text {
    color: #444; line-height: 1.95; font-size: 0.95rem;
    padding-bottom: 0.9rem; margin-bottom: 0.9rem; border-bottom: 1px solid #EEE;
}

#nizam-footer { text-align: center; color: #9AA5A0; font-size: 0.82rem; margin-top: 2rem; }
"""

HEAD = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Tajawal:wght@400;500;700&family=Noto+Kufi+Arabic:wght@400;700&display=swap">'
)

# تثبيت الوضع الفاتح مهما كان إعداد الزائر
FORCE_LIGHT_JS = """
() => {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'light') {
        url.searchParams.set('__theme', 'light');
        window.location.replace(url.href);
    }
}
"""


# ==================== بناء الواجهة ====================
with gr.Blocks(title="نظام — مساعد نظام العمل السعودي", analytics_enabled=False) as demo:
    gr.HTML(
        '<div class="nizam-title">نظام</div>'
        '<p class="nizam-subtitle">مساعد يجيب عن أسئلة نظام العمل السعودي '
        "بالاستناد إلى المادة النظامية</p>",
        elem_id="nizam-header",
    )
    gr.HTML(
        '<div class="nizam-disclaimer">⚠️ النتائج استرشادية للاطلاع فقط '
        "— وليست استشارة قانونية.</div>",
        elem_id="nizam-disclaimer",
    )

    gr.HTML('<div class="nizam-hint">جرّب سؤالاً جاهزاً — ثم اضغط «اسأل»:</div>')
    with gr.Row():
        sample_buttons = [
            gr.Button(label, elem_classes="nizam-sample") for label, _ in SAMPLES
        ]

    query_box = gr.Textbox(
        label="سؤالك",
        placeholder="مثال: متى يحق لصاحب العمل فسخ العقد دون مكافأة؟",
        lines=2,
        elem_id="nizam-input",
    )
    ask_button = gr.Button("اسأل", variant="primary", elem_classes="nizam-ask")

    answer_html = gr.HTML()
    with gr.Accordion("📎 المواد النظامية المستند إليها", open=False, visible=False) as cites_box:
        citations_html = gr.HTML()

    gr.HTML(
        "نظام · مشروع استرشادي لنظام العمل السعودي · للاطلاع فقط",
        elem_id="nizam-footer",
    )

    # أزرار الأسئلة تملأ الحقل فقط — لا تنفّذ. ضغطة عابرة لا تصرف من الحصة.
    for button, (_, sample) in zip(sample_buttons, SAMPLES):
        button.click(lambda s=sample: s, inputs=None, outputs=query_box)

    outputs = [answer_html, citations_html, cites_box]
    ask_button.click(ask, inputs=query_box, outputs=outputs)
    query_box.submit(ask, inputs=query_box, outputs=outputs)


if __name__ == "__main__":
    # ملاحظة Gradio 6: css/theme/js/head تُمرَّر إلى launch() لا إلى Blocks().
    demo.launch(css=CSS, head=HEAD, js=FORCE_LIGHT_JS, theme=gr.themes.Soft())
