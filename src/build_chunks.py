"""
Nizam — Phase 2: Build the unified chunk list for indexing.
Most articles = 1 chunk. Article 2 = 19 definition chunks (all number=2).
"""
import json
import re
from pathlib import Path

ARTICLES_PATH = Path("data/processed/articles.json")
OUT_PATH = Path("data/processed/chunks.json")

SPLIT_RE = re.compile(r'(?:^|(?<=\.\s))([^.:]{2,40}?):\s')
CONTINUATIONS = {"وتعد الخدمة مستمرة في الحالات الآتية", "ومن ذلك"}


def split_article2(text):
    """Split the definitions article into one chunk per term."""
    splits = []
    for m in SPLIT_RE.finditer(text):
        term = m.group(1).strip()
        if term in CONTINUATIONS:
            continue
        splits.append((m.start(), term))

    chunks = []
    # intro before first term (the "يقصد بالألفاظ..." line) + first term glued
    intro = text[:splits[0][0]].strip()
    for idx, (pos, term) in enumerate(splits):
        end = splits[idx + 1][0] if idx + 1 < len(splits) else len(text)
        chunk_text = text[pos:end].strip()
        if idx == 0 and intro:
            chunk_text = intro + " " + chunk_text  # keep the framing sentence
        chunks.append((term, chunk_text))
    return chunks


def build():
    articles = json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))
    chunks = []

    for art in articles:
        is_art2 = art["number"] == 2 and not art["is_mukarrar"]

        if is_art2:
            parts = split_article2(art["text"])
            for i, (term, ctext) in enumerate(parts, 1):
                chunks.append({
                    "chunk_id": f"{art['article_id']}_c{i:02d}",
                    "article_number": art["number"],
                    "display_name": art["display_name"],
                    "bab_number": art["bab_number"],
                    "bab_title": art["bab_title"],
                    "term": term,              # only art-2 chunks have this
                    "text": ctext,
                    "char_count": len(ctext),
                })
        else:
            chunks.append({
                "chunk_id": art["article_id"],
                "article_number": art["number"],
                "display_name": art["display_name"],
                "bab_number": art["bab_number"],
                "bab_title": art["bab_title"],
                "term": None,
                "text": art["text"],
                "char_count": art["char_count"],
            })

    OUT_PATH.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    # verification
    art2_chunks = [c for c in chunks if c["article_number"] == 2 and not c["chunk_id"].endswith("mukarrar")]
    over_512 = [c for c in chunks if c["char_count"] > 1000]
    print(f"✅ Total chunks       : {len(chunks)}")
    print(f"   From 245 articles  : (244 single + {len(art2_chunks)} from article 2)")
    print(f"   Chunks over 1000ch : {len(over_512)}  {[c['display_name'] for c in over_512]}")
    print(f"   Written to         : {OUT_PATH}")
    print("-" * 55)
    print("SAMPLE — article 2 chunks:")
    for c in art2_chunks[:3]:
        print(f"  {c['chunk_id']} [{c['term']}] {c['char_count']}ch")
    print("SAMPLE — regular articles:")
    for c in [x for x in chunks if x["article_number"] in (84, 109)][:2]:
        print(f"  {c['chunk_id']} ({c['display_name']}) {c['char_count']}ch")

if __name__ == "__main__":
    build()