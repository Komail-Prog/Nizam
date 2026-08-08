"""
Nizam — Phase 2: Build the e5 semantic index in ChromaDB.
"""
import json
import time
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = Path("data/processed/chunks.json")
DB_DIR = "chroma_db"
COLLECTION = "labor_law"
MODEL_NAME = "intfloat/multilingual-e5-base"


def build_index():
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(chunks)} chunks")

    print("Loading e5-base...")
    model = SentenceTransformer(MODEL_NAME)

    # e5 requires 'passage:' prefix for documents
    texts = [f"passage: {c['text']}" for c in chunks]

    print("Encoding (this runs once)...")
    t0 = time.time()
    embeddings = model.encode(
        texts, normalize_embeddings=True, show_progress_bar=True, batch_size=32
    )
    print(f"Encoded {len(texts)} chunks in {time.time() - t0:.1f}s")

    # fresh ChromaDB collection
    client = chromadb.PersistentClient(path=DB_DIR)
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION, metadata={"hnsw:space": "cosine"}
    )

    # Chroma metadata values must be str/int/float/bool — no None, no nested
    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=[e.tolist() for e in embeddings],
        documents=[c["text"] for c in chunks],
        metadatas=[{
            "article_number": c["article_number"],
            "display_name": c["display_name"],
            "bab_number": c["bab_number"],
            "bab_title": c["bab_title"],
            "term": c["term"] if c["term"] else "",
        } for c in chunks],
    )

    print(f"✅ Indexed {collection.count()} chunks in ChromaDB → {DB_DIR}/")


if __name__ == "__main__":
    build_index()