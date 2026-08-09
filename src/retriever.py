"""
Nizam — Phase 2 public interface.
One clean function the generation stage (Phase 3) calls:
    retrieve(query, k) -> list of article dicts (number, name, text, bab, score)
"""
from search_hybrid import hybrid_search, detect_article_number
from search_semantic import _load


def _article_payload(display_name):
    """Fetch full text + metadata for an article by its display_name."""
    _, collection = _load()
    res = collection.get(where={"display_name": display_name})
    if not res["ids"]:
        return None
    # an article may be split into chunks (article 2); join their texts
    metas = res["metadatas"]
    docs = res["documents"]
    # order chunks by id for stable text
    pairs = sorted(zip(res["ids"], docs), key=lambda p: p[0])
    full_text = " ".join(d for _, d in pairs)
    m = metas[0]
    return {
        "article_number": m["article_number"],
        "display_name": m["display_name"],
        "bab_number": m["bab_number"],
        "bab_title": m["bab_title"],
        "text": full_text,
    }


def retrieve(query: str, k: int = 3):
    """Return the top-k most relevant articles as full payloads for generation."""
    names, dbg = hybrid_search(query, k=k)
    results = []
    for name in names:
        payload = _article_payload(name)
        if payload:
            payload["retrieval"] = "article_lookup" if name in dbg["forced"] else "hybrid"
            results.append(payload)
    return results


if __name__ == "__main__":
    q = "كيف تحسب مكافأة نهاية الخدمة؟"
    print(f"❓ {q}\n" + "=" * 60)
    for i, art in enumerate(retrieve(q, k=3), 1):
        print(f"{i}. {art['display_name']} — باب {art['bab_number']}: {art['bab_title']}")
        print(f"   [{art['retrieval']}] {art['text'][:90]}...")
        print()