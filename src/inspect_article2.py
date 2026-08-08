import json
from pathlib import Path

articles = json.loads(Path("data/processed/articles.json").read_text(encoding="utf-8"))
art2 = next(a for a in articles if a["number"] == 2 and not a["is_mukarrar"])

text = art2["text"]
print(f"Total chars: {len(text)}")
print("=" * 60)
# Print with visible structure — show first 1500 chars raw
print(text[:1500])
print("=" * 60)
print("...")
print(text[-600:])