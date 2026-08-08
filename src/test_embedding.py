import time
from sentence_transformers import SentenceTransformer

print("Loading multilingual-e5-base (first run downloads ~1.1GB)...")
t0 = time.time()
model = SentenceTransformer("intfloat/multilingual-e5-base")
print(f"Model loaded in {time.time() - t0:.1f}s")

# e5 REQUIRES prefixes: 'query:' for questions, 'passage:' for documents
query = "query: كم مدة الإجازة السنوية للعامل؟"
passages = [
    "passage: يستحق العامل عن كل عام إجازة سنوية لا تقل مدتها عن واحد وعشرين يومًا.",
    "passage: يحظر تشغيل الأحداث في الأعمال الخطرة.",
    "passage: مكافأة نهاية الخدمة أجر نصف شهر عن كل سنة من السنوات الخمس الأولى.",
]

t1 = time.time()
q_emb = model.encode(query, normalize_embeddings=True)
p_embs = model.encode(passages, normalize_embeddings=True)
print(f"Encoded 1 query + 3 passages in {time.time() - t1:.2f}s")
print(f"Embedding dimension: {q_emb.shape}")

# cosine similarity = dot product (already normalized)
import numpy as np
sims = p_embs @ q_emb
print("\nSimilarity to query (higher = more relevant):")
for p, s in sorted(zip(passages, sims), key=lambda x: -x[1]):
    print(f"  {s:.3f}  {p[9:60]}...")