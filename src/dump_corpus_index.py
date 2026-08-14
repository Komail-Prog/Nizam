"""
Nizam — Phase 5, Step 2: offline corpus index dump.
Zero Gemini calls. Verifies ingestion and produces the ground-truth
article list used to write the 40 golden questions.
Run from project root with .venv active:
    python src/dump_corpus_index.py
"""
import os
from collections import defaultdict
from search_semantic import _load


def main():
    _, collection = _load()
    res = collection.get(include=["metadatas", "documents"])
    ids, metas, docs = res["ids"], res["metadatas"], res["documents"]

    # group chunks by article (article 2 is split into multiple chunks)
    articles = defaultdict(lambda: {"chunks": 0, "chars": 0, "meta": None, "text": ""})
    for _id, m, d in zip(ids, metas, docs):
        a = articles[m["display_name"]]
        a["chunks"] += 1
        a["chars"] += len(d or "")
        a["text"] += (d or "") + " "
        if a["meta"] is None:
            a["meta"] = m

    # numeric sort where possible
    def sort_key(item):
        num = item[1]["meta"]["article_number"]
        try:
            return (0, int(num))
        except (ValueError, TypeError):
            return (1, str(num))

    ordered = sorted(articles.items(), key=sort_key)

    # ---- console health check (paste this back to me) ----
    sample_type = type(ordered[0][1]["meta"]["article_number"]).__name__
    multi = [(n, i["chunks"]) for n, i in ordered if i["chunks"] > 1]
    missing_bab = [n for n, i in ordered if not i["meta"].get("bab_title")]

    print("=" * 60)
    print(f"Total chunks in collection : {len(ids)}")
    print(f"Unique articles            : {len(articles)}")
    print(f"article_number type        : {sample_type}")
    print(f"Multi-chunk articles       : {multi if multi else 'none'}")
    print(f"Articles missing bab_title : {missing_bab if missing_bab else 'none'}")
    print("=" * 60)

    # ---- full index written to file (upload this back to me) ----
    out_dir = os.path.join("docs", "eval")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "corpus_index.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("| article_number | bab | bab_title | chars | snippet |\n")
        f.write("|---|---|---|---|---|\n")
        for name, info in ordered:
            m = info["meta"]
            snip = info["text"][:110].replace("\n", " ").replace("|", "／").strip()
            f.write(f"| {m['article_number']} | {m['bab_number']} | {m['bab_title']} | {info['chars']} | {snip}… |\n")
    print(f"Wrote index → {out_path}  ({len(ordered)} articles)")


if __name__ == "__main__":
    main()