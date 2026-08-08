import json
import re
from pathlib import Path

articles = json.loads(Path("data/processed/articles.json").read_text(encoding="utf-8"))
art2 = next(a for a in articles if a["number"] == 2 and not a["is_mukarrar"])
text = art2["text"]

# A definition term: starts after ". " (or at very start), short (1-4 words),
# followed by a colon. We capture the term before each colon that follows a period.
# Pattern: sentence boundary -> short phrase -> colon
pattern = re.compile(r'(?:^|\.\s+)([^.:]{2,40}?):\s')

matches = list(pattern.finditer(text))
print(f"Candidate terms found: {len(matches)}")
print("=" * 60)
for i, m in enumerate(matches, 1):
    term = m.group(1).strip()
    # show a bit of the following definition for context
    start = m.end()
    preview = text[start:start + 45].replace("\n", " ")
    print(f"{i:2}. [{term}]  →  {preview}...")