"""
Nizam — Phase 5 probe: verify display_name is present in the REAL retrieve() output,
and that it distinguishes mukarrar articles. Zero Gemini calls (retrieval only).
Run from project root with .venv active:
    python src/probe_display_name.py
"""
from retriever import retrieve  # adjust module name if your file differs


def show(query, k=3):
    print("=" * 70)
    print(f"QUERY: {query}")
    print("=" * 70)
    results = retrieve(query, k=k)
    for i, r in enumerate(results, 1):
        # print the RAW keys so we see exactly what retrieve emits
        print(f"[{i}] keys = {list(r.keys())}")
        print(f"     article_number = {r.get('article_number')!r}  (type {type(r.get('article_number')).__name__})")
        print(f"     display_name   = {r.get('display_name')!r}")
        print(f"     retrieval      = {r.get('retrieval')!r}")
        print(f"     text[:70]      = {r.get('text','')[:70]!r}")
        print()


if __name__ == "__main__":
    # 1) A query that SHOULD hit the mukarrar version (resignation auto-accept after 30 days)
    show("إذا قدمت استقالتي ولم يرد صاحب العمل خلال ثلاثين يوماً هل تعتبر مقبولة؟")

    # 2) A query that SHOULD hit the ORIGINAL 79 (contract ends by death)
    show("هل ينتهي عقد العمل بوفاة العامل؟")