---
title: Nizam
emoji: ⚖️
colorFrom: green
colorTo: gray
sdk: gradio
sdk_version: 6.24.0
app_file: app.py
pinned: false
license: mit
short_description: Arabic RAG for Saudi Labor Law with citations
---

# نظام · Nizam

**نظام** مساعد عربي يجيب عن أسئلة **نظام العمل السعودي** بالاستناد إلى المادة النظامية الدقيقة، ويرفض صراحةً ما هو خارج النطاق بدل أن يخمّن.

**Nizam** is an Arabic RAG assistant that answers questions about **Saudi Labor Law**, grounding every answer in the exact source article — and explicitly refusing out-of-scope questions instead of hallucinating.

🔗 **الديمو الحي · Live demo:** https://huggingface.co/spaces/Komail262/Nizam

> ⚠️ النتائج استرشادية للاطلاع فقط — وليست استشارة قانونية.
> Results are informational only — not legal advice.

---

## ما الذي يفعله · What it does

- **إجابات مقيّدة بالاستشهاد:** كل إجابة تُبنى حصراً على مواد مسترجَعة من النص، وتعرض رقم المادة ونصّها.
- **رفض آمن:** إذا لم تُجب المواد المسترجَعة عن السؤال، يرفض النظام صراحةً بدل التخمين.
- **أداة حساب:** حاسبة مكافأة نهاية الخدمة (المواد 84، 85، 87) تنطلق فقط عند أسئلة الحساب، موسومة «نتيجة استرشادية».

---

## كيف يعمل · Architecture

| الطبقة | التقنية |
|---|---|
| Retrieval | Hybrid: BM25 (lexical) + multilingual-e5-base (semantic) over ChromaDB |
| Chunking | وحدة التقطيع = المادة النظامية؛ كل chunk يحمل `{article_number, bab, text}` |
| Generation | Gemini 2.5 Flash، مقيّد بالمواد المسترجَعة عبر بوابة استشهاد ثلاثية الحرّاس |
| Tool | Function calling — حاسبة مكافأة نهاية الخدمة (نداء Gemini واحد يفرّع: أداة أو إجابة مستشهدة) |
| UI | Gradio (عربي RTL) على Hugging Face Spaces |

بوابة الاستشهاد ترفض الإجابة إذا: قال النموذج إنه لا يستطيع، أو لم يستشهد بأي مادة، أو استشهد بمادة غير موجودة في المسترجَع (منع الهلوسة).

---

## التقييم · Evaluation

قُيّم النظام على **مجموعة ذهبية من 40 سؤالاً** كُتبت يدوياً ومطابَقة حرفياً لنص نظام العمل (245 مادة)، موزّعة على ثلاث فئات تختبر ثلاثة سلوكيات: دقة الاسترجاع، الرفض الآمن، وأمانة التوليد.

| المقياس · Metric | النتيجة · Result |
|---|---|
| **hit@3** (أسئلة قابلة للإجابة، 28) | **92.9%** (26/28) |
| **الرفض الآمن · Safe refusal** (خارج النطاق، 7) | **100%** (7/7) |
| **الأمانة · Faithfulness** (عيّنة 12، حكم يدوي) | **صفر اختلاق في 91%** (10/11) |

**ملاحظات منهجية:**
- المقياس على `display_name` مُطبَّع (يميّز المواد المكرّرة: «79» عن «79 مكرر») — لا على رقم المادة وحده.
- الحالتان الفاشلتان في hit@3 (Q12 تصادم لفظي، Q21 مادة قصيرة مدفونة) **تُركتا موثّقتين لا مُجمَّلتين** — رُفض تجميل المقياس.
- faithfulness بحكم يدوي (لا LLM-judge) لكشف ما لا يمسكه مقياس آلي. النمط المكتشَف: **إغفال لا اختلاق** (5:1).

التفاصيل الكاملة (تشخيص كل فشل، قاعدة الحكم) في [`docs/eval/RESULTS.md`](docs/eval/RESULTS.md).

---

## التشغيل المحلي · Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
export GEMINI_API_KEY="your-key"  # Windows: $env:GEMINI_API_KEY="your-key"
python app.py
```

> **حصة الديمو:** المفتاح المجاني لـ Gemini محدود بـ 20 طلباً/يوم، مشتركة بين زوّار الديمو الحي. عند النفاد، يعرض النظام رسالة مهذّبة بدل خطأ.

---

## إخلاء المسؤولية · Disclaimer

هذا المشروع أداة **استرشادية** لأغراض العرض التقني، وليس مصدراً قانونياً. لا يُعتمد عليه في أي قرار قانوني أو تعاقدي. المرجع الرسمي الوحيد هو نظام العمل السعودي الصادر عن الجهات المختصة.
