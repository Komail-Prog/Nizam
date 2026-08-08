import json
import re
from pathlib import Path

articles = json.loads(Path("data/processed/articles.json").read_text(encoding="utf-8"))
art2 = next(a for a in articles if a["number"] == 2 and not a["is_mukarrar"])
text = art2["text"]

# Split points: a short term (2-40 chars, no period/colon inside) followed by ':'
# that begins a new definition (preceded by start or ". ")
SPLIT_RE = re.compile(r'(?:^|(?<=\.\s))([^.:]{2,40}?):\s')

# Phrases that look like terms but are CONTINUATIONS — must not start a new chunk
CONTINUATIONS = {"وتعد الخدمة مستمرة في الحالات الآتية", "ومن ذلك"}

# Find all candidate split positions
splits = []
for m in SPLIT_RE.finditer(text):
    term = m.group(1).strip()
    if term in CONTINUATIONS:
        continue                       # skip: keep glued to previous definition
    splits.append((m.start(), term))

# Build chunks: from each split start to the next split start
chunks = []
intro = text[:splits[0][0]].strip() if splits else text
for idx, (pos, term) in enumerate(splits):
    end = splits[idx + 1][0] if idx + 1 < len(splits) else len(text)
    chunk_text = text[pos:end].strip()
    chunks.append({"term": term, "text": chunk_text})

print(f"Intro (before first term): {intro[:70]}...")
print(f"Definition chunks: {len(chunks)}")
print("=" * 60)
for i, c in enumerate(chunks, 1):
    print(f"{i:2}. [{c['term']}] ({len(c['text'])} حرف)")
    print(f"    {c['text'][:75]}...")