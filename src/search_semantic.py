"""
Nizam — Phase 2: Semantic search over the e5 / ChromaDB index.
"""
import chromadb
from sentence_transformers import SentenceTransformer

DB_DIR = "chroma_db"
COLLECTION = "labor_law"
MODEL_NAME = "intfloat/multilingual-e5-base"

_model = None
_collection = None


def _load():
    global _model, _collection
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
        client = chromadb.PersistentClient(path=DB_DIR)
        _collection = client.get_collection(COLLECTION)
    return _model, _collection


def semantic_search(query: str, k: int = 5):
    model, collection = _load()
    # e5 requires 'query:' prefix for questions
    q_emb = model.encode(f"query: {query}", normalize_embeddings=True)
    results = collection.query(query_embeddings=[q_emb.tolist()], n_results=k)

    hits = []
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i]
        hits.append({
            "display_name": meta["display_name"],
            "term": meta.get("term", ""),
            "distance": results["distances"][0][i],
            "text": results["documents"][0][i],
        })
    return hits


if __name__ == "__main__":
    test_queries = [
        "كم مدة الإجازة السنوية للعامل؟",
        "كيف تحسب مكافأة نهاية الخدمة؟",
        "ما هي حقوق العامل عند الاستقالة؟",
        "متى يحق لصاحب العمل فصل العامل دون مكافأة؟",
        "ما تعريف الأجر الأساسي؟",
    ]
    for q in test_queries:
        print("=" * 65)
        print(f"❓ {q}")
        print("-" * 65)
        for i, h in enumerate(semantic_search(q, k=3), 1):
            term = f" [{h['term']}]" if h["term"] else ""
            print(f"  {i}. {h['display_name']}{term}  (distance={h['distance']:.3f})")
            print(f"     {h['text'][:65]}...")