from search_hybrid import hybrid_search

q = "كم مدة الإجازة السنوية للعامل؟"
names, dbg = hybrid_search(q, k=10)

print(f"❓ {q}")
print("-" * 50)
for i, n in enumerate(names, 1):
    score = dbg["rrf"].get(n, 0)
    mark = " ← 109!" if "109" in n else ""
    print(f"  {i}. {n}  (rrf={score:.4f}){mark}")

# explicit rank of 109
rank_109 = next((i for i, n in enumerate(names, 1) if "109" in n), "not found")
print("-" * 50)
print(f"المادة 109 في المركز: {rank_109}")