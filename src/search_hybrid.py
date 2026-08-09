"""
Nizam — Phase 2: Hybrid search = article-number lookup + RRF(e5, BM25).
"""
import re
from search_semantic import semantic_search, _load
from search_lexical import LexicalIndex

RRF_K = 60

# Arabic-Indic digits → Latin, for number lookup
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

_lexical = None


def _get_lexical():
    global _lexical
    if _lexical is None:
        _lexical = LexicalIndex()
    return _lexical


def detect_article_number(query: str):
    """If the query explicitly asks for 'المادة N', return N, else None."""
    q = query.translate(_AR_DIGITS)
    m = re.search(r"الماد[هة]\s*\(?\s*(\d{1,3})", q)
    return int(m.group(1)) if m else None


def _rank_map(hits):
    """Map display_name -> best rank (1-based) from a hit list."""
    ranks = {}
    for i, h in enumerate(hits, 1):
        name = h["display_name"]
        if name not in ranks:      # keep best (first) rank per article
            ranks[name] = i
    return ranks


def hybrid_search(query: str, k: int = 5, pool: int = 10):
    # --- Path 1: direct article-number lookup ---
    num = detect_article_number(query)
    forced = []
    if num is not None:
        _, collection = _load()
        res = collection.get(where={"article_number": num})
        if res["ids"]:
            meta = res["metadatas"][0]
            forced.append(meta["display_name"])

    # --- Path 2: semantic + lexical, fused with RRF ---
    sem = semantic_search(query, k=pool)
    lex = _get_lexical().search(query, k=pool)

    sem_ranks = _rank_map(sem)
    lex_ranks = _rank_map(lex)

    all_names = set(sem_ranks) | set(lex_ranks)
    rrf = {}
    for name in all_names:
        score = 0.0
        if name in sem_ranks:
            score += 1.0 / (RRF_K + sem_ranks[name])
        if name in lex_ranks:
            score += 1.0 / (RRF_K + lex_ranks[name])
        rrf[name] = score

    fused = sorted(rrf, key=lambda n: rrf[n], reverse=True)

    # forced article first (dedup), then fused
    ordered = forced + [n for n in fused if n not in forced]
    return ordered[:k], {"forced": forced, "rrf": rrf, "sem": sem_ranks, "lex": lex_ranks}


if __name__ == "__main__":
    tests = [
        "كم مدة الإجازة السنوية للعامل؟",
        "متى يحق لصاحب العمل فصل العامل دون مكافأة؟",
        "ما نص المادة 109؟",
        "كيف تحسب مكافأة نهاية الخدمة؟",
        "ما تعريف الأجر الأساسي؟",
    ]
    for q in tests:
        names, dbg = hybrid_search(q, k=3)
        print("=" * 65)
        print(f"❓ {q}")
        if dbg["forced"]:
            print(f"   📌 article-number lookup: {dbg['forced']}")
        print("-" * 65)
        for i, name in enumerate(names, 1):
            s = dbg["rrf"].get(name, 0)
            tag = "📌" if name in dbg["forced"] else f"rrf={s:.4f}"
            print(f"  {i}. {name}  ({tag})")