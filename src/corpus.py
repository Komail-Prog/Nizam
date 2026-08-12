from retriever import retrieve

for art in ["84", "85", "87", "88"]:
    hits = retrieve(f"مكافأة نهاية الخدمة المادة {art}", k=1)
    print("=" * 60)
    for h in hits:
        print(h["display_name"], "|", h["bab_title"])
        print(h["text"])