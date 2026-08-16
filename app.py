# app.py — واجهة نظام (Nizam): مساعد نظام العمل السعودي
# غلاف عرض Streamlit عربي RTL. يستهلك answer_gated_merged كصندوق أسود.
# لا يحتوي هذا الملف أي منطق جوهري: لا استرجاع، لا بوابة، لا حساب.
import html
import os
import re
import sys

# src على الـ path حتى تعمل استيرادات generator المسطّحة (from retriever import ...)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st

st.set_page_config(
    page_title="نظام — مساعد نظام العمل السعودي",
    page_icon="⚖️",
    layout="centered",
)

# ==================== التنسيق (RTL + هوية بصرية + تثبيت الوضع الفاتح) ====================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&family=Noto+Kufi+Arabic:wght@400;700&display=swap');

    :root {
        --nizam-green: #0B5D3B;
        --nizam-green-soft: #E8F2ED;
        --nizam-ink: #1A1A1A;
        --nizam-muted: #5A6B63;
    }

    /* إخفاء كروم Streamlit: زر Deploy، القائمة، شريط الأدوات، الفوتر.
       ملاحظة: لا نصفّر ارتفاع الهيدر (يسبب قصّاً علوياً) — نجعله شفافاً فقط. */
    #MainMenu, footer, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"],
    .stDeployButton, [data-testid="stAppDeployButton"] { display: none !important; }
    header[data-testid="stHeader"] { background: transparent !important; }

    /* خلفية بيضاء ثابتة — لا تتأثر بوضع dark عند الزائر */
    .stApp, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: #FFFFFF !important;
        color: var(--nizam-ink) !important;
    }

    /* اتجاه عربي كامل */
    .stApp, body, .block-container {
        direction: rtl;
        text-align: right;
        font-family: 'Tajawal', 'Noto Kufi Arabic', 'Segoe UI', sans-serif;
    }

    /* عمود متمركز أفقياً مع مساحة علوية مريحة */
    .block-container {
        max-width: 760px;
        margin: 0 auto;
        padding-top: 3rem;
        padding-bottom: 4rem;
    }

    /* الرأس */
    .nizam-header { text-align: center; margin-bottom: 1.4rem; }
    .nizam-title {
        font-family: 'Noto Kufi Arabic', 'Tajawal', sans-serif;
        font-size: 3rem; font-weight: 700; color: var(--nizam-green);
        margin: 0 0 0.4rem 0; line-height: 1.3;
    }
    .nizam-subtitle {
        font-size: 1.02rem; color: var(--nizam-muted); margin: 0;
        font-weight: 400; line-height: 1.9;
    }

    /* إخلاء المسؤولية — بند إلزامي، بارز */
    .nizam-disclaimer {
        background: #FFF7E6; border: 1px solid #F0D9A0;
        border-right: 5px solid #E6A700;
        color: #7A5A00; padding: 0.85rem 1.1rem; border-radius: 10px;
        font-size: 0.95rem; font-weight: 500; margin: 0 0 1.8rem 0;
        text-align: center;
    }

    .nizam-label {
        color: var(--nizam-muted); font-size: 0.92rem;
        font-weight: 500; margin-bottom: 0.45rem;
    }

    /* أزرار الأسئلة الجاهزة + زر اسأل */
    div.stButton > button, div.stFormSubmitButton > button {
        width: 100%; border-radius: 10px; border: 1px solid #DDE3E0;
        background: #FFFFFF; color: var(--nizam-ink);
        font-family: 'Tajawal', sans-serif; font-size: 0.94rem;
        padding: 0.55rem 0.4rem; transition: all 0.15s ease;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        border-color: var(--nizam-green); color: var(--nizam-green);
        background: var(--nizam-green-soft);
    }
    /* زر «اسأل» أساسي */
    div.stFormSubmitButton > button {
        background: var(--nizam-green); color: #FFFFFF;
        border-color: var(--nizam-green); font-weight: 700;
    }
    div.stFormSubmitButton > button:hover {
        background: #094B30; color: #FFFFFF; border-color: #094B30;
    }

    /* حقل الإدخال RTL */
    .stTextInput input {
        direction: rtl; text-align: right;
        font-family: 'Tajawal', sans-serif; font-size: 1rem;
        border-radius: 10px; background: #FFFFFF; color: var(--nizam-ink);
    }
    .stTextInput input:focus { border-color: var(--nizam-green) !important; }

    /* شارة المسار */
    .nizam-badge {
        display: inline-block; padding: 0.3rem 0.9rem; border-radius: 20px;
        font-size: 0.86rem; font-weight: 500; margin-bottom: 0.7rem;
    }
    .badge-tool   { background: #E8F2ED; color: #0B5D3B; }
    .badge-cite   { background: #E7F0FA; color: #12507E; }
    .badge-refuse { background: #FBEAEA; color: #9B2C2C; }

    /* صندوق الإجابة */
    .nizam-answer {
        background: #FAFBFA; border: 1px solid #E6EBE8; border-radius: 12px;
        padding: 1.2rem 1.4rem; font-size: 1.06rem; line-height: 2.05;
        color: var(--nizam-ink);
    }
    .nizam-question {
        color: var(--nizam-muted); font-size: 0.95rem; margin-bottom: 0.8rem;
    }
    .nizam-question b { color: var(--nizam-ink); font-weight: 700; }

    /* الاستشهادات */
    .stExpander { direction: rtl; text-align: right; border-radius: 10px; }
    .nizam-cite-num {
        color: var(--nizam-green); font-weight: 700; font-size: 0.98rem;
        margin-bottom: 0.25rem;
    }
    .nizam-cite-text {
        color: #444; line-height: 1.95; font-size: 0.95rem;
        padding-bottom: 0.9rem; margin-bottom: 0.9rem;
        border-bottom: 1px solid #EEE;
    }

    .nizam-footer {
        text-align: center; color: #9AA5A0; font-size: 0.82rem;
        margin-top: 3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================== تحميل المعمارية (مرة واحدة عبر كل الجلسات) ====================
@st.cache_resource(show_spinner="جارٍ تحميل النموذج والفهرس…")
def _load_engine():
    """أول استيراد يحمّل e5 + ChromaDB داخل generator/retriever."""
    from generator import answer_gated_merged, REFUSAL_MESSAGE

    return answer_gated_merged, REFUSAL_MESSAGE


@st.cache_data(show_spinner=False, ttl=3600, max_entries=64)
def _ask(query: str) -> dict:
    """نداء واحد لكل سؤال فريد. التخزين المؤقّت يحمي حصة Gemini اليومية:
    تكرار نفس السؤال لا يصرف نداءً جديداً (الحرارة 0.0 → النتيجة حتمية)."""
    engine, _ = _load_engine()
    return engine(query)


_, REFUSAL_MESSAGE = _load_engine()


# ==================== أدوات عرض ====================
def _to_html(text: str) -> str:
    """الإجابات تعود بصيغة ماركداون خفيفة (**عريض** وأسطر جديدة).
    نهرّب HTML أولاً ثم نحوّل — حتى تظهر داخل صندوق منسّق دون رموز نيئة."""
    out = html.escape(str(text))
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out, flags=re.DOTALL)
    return out.replace("\n", "<br>")


# ==================== الرأس ====================
st.markdown(
    """
    <div class="nizam-header">
        <div class="nizam-title">نظام</div>
        <p class="nizam-subtitle">مساعد يجيب عن أسئلة نظام العمل السعودي بالاستناد إلى المادة النظامية</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="nizam-disclaimer">⚠️ النتائج استرشادية للاطلاع فقط — وليست استشارة قانونية.</div>',
    unsafe_allow_html=True,
)

# ==================== حالة الجلسة ====================
st.session_state.setdefault("query_box", "")
st.session_state.setdefault("pending", None)  # سؤال بانتظار التنفيذ (يُستهلك مرة واحدة)
st.session_state.setdefault("result", None)  # آخر نتيجة معروضة

# ==================== الأسئلة الجاهزة — تُعبّئ الحقل فقط، لا تُنفّذ ====================
SAMPLES = [
    ("🧮 حساب مكافأة", "فصلني صاحب العمل، راتبي 10000 وخدمتي 7 سنوات، كم مكافأتي؟"),
    ("📚 سؤال عام", "كم مدة إجازة الوضع للمرأة العاملة؟"),
    ("✅ خارج النطاق", "ما عقوبة تجاوز السرعة على الطريق السريع؟"),
]

st.markdown('<div class="nizam-label">جرّب سؤالاً جاهزاً — ثم اضغط «اسأل»:</div>', unsafe_allow_html=True)
for col, (label, sample) in zip(st.columns(3), SAMPLES):
    if col.button(label, key=f"sample_{label}", use_container_width=True):
        st.session_state.query_box = sample
        st.rerun()

# ==================== الإدخال الحر ====================
with st.form("nizam_form", clear_on_submit=False, border=False):
    st.text_input(
        "سؤالك:",
        key="query_box",
        placeholder="مثال: متى يحق لصاحب العمل فسخ العقد دون مكافأة؟",
        label_visibility="collapsed",
    )
    if st.form_submit_button("اسأل", use_container_width=True):
        typed = st.session_state.query_box.strip()
        if typed:
            st.session_state.pending = typed

# ==================== التنفيذ: مرّة واحدة لكل ضغطة، لا عند إعادة الرسم ====================
if st.session_state.pending:
    question = st.session_state.pending
    st.session_state.pending = None  # استهلاك فوري — يمنع إعادة النداء عند أي rerun
    with st.spinner("جارٍ البحث في نظام العمل…"):
        try:
            st.session_state.result = {"q": question, "status": "ok", "res": _ask(question)}
        except RuntimeError:
            # استُنفدت المحاولات (429) — الحصة اليومية
            st.session_state.result = {"q": question, "status": "quota"}
        except Exception as exc:
            st.session_state.result = {"q": question, "status": "error", "err": type(exc).__name__}

# ==================== العرض ====================
state = st.session_state.result
if state:
    st.markdown("---")
    st.markdown(
        f'<div class="nizam-question"><b>السؤال:</b> {html.escape(state["q"])}</div>',
        unsafe_allow_html=True,
    )

    if state["status"] == "quota":
        st.markdown(
            '<span class="nizam-badge badge-refuse">⏳ الحصة اليومية</span>'
            '<div class="nizam-answer">بلغ الديمو حدّه اليومي من الطلبات المجانية. '
            'جرّب مرة أخرى بعد عدة ساعات — أو شاهد الأمثلة في فيديو العرض بصفحة المشروع.</div>',
            unsafe_allow_html=True,
        )
    elif state["status"] == "error":
        st.markdown(
            '<span class="nizam-badge badge-refuse">⚠️ تعذّر الإكمال</span>'
            '<div class="nizam-answer">تعذّر إكمال الطلب حالياً. أعد المحاولة بعد قليل.</div>',
            unsafe_allow_html=True,
        )
    else:
        res = state["res"]

        if not res.get("answered", False):
            st.markdown(
                '<span class="nizam-badge badge-refuse">↩︎ خارج النطاق</span>'
                f'<div class="nizam-answer">{_to_html(res.get("message", REFUSAL_MESSAGE))}</div>',
                unsafe_allow_html=True,
            )
        else:
            badge = (
                '<span class="nizam-badge badge-tool">🧮 نتيجة حاسبة</span>'
                if res.get("path") == "tool"
                else '<span class="nizam-badge badge-cite">📚 إجابة مستشهدة</span>'
            )
            st.markdown(
                f'{badge}<div class="nizam-answer">{_to_html(res.get("answer", ""))}</div>',
                unsafe_allow_html=True,
            )

            citations = res.get("citations") or []
            if citations:
                with st.expander(f"📎 المواد النظامية المستند إليها ({len(citations)})"):
                    for cite in citations:
                        st.markdown(
                            f'<div class="nizam-cite-num">المادة {html.escape(str(cite.get("article_number", "؟")))}</div>'
                            f'<div class="nizam-cite-text">{_to_html(cite.get("text", ""))}</div>',
                            unsafe_allow_html=True,
                        )

st.markdown(
    '<div class="nizam-footer">نظام · مشروع استرشادي لنظام العمل السعودي · للاطلاع فقط</div>',
    unsafe_allow_html=True,
)
