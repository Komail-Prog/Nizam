import json
from pathlib import Path

d = json.loads(Path("data/processed/chunks.json").read_text(encoding="utf-8"))

for num in (98, 100, 101):
    art = next((x for x in d if x["article_number"] == num), None)
    print(f"=== المادة {num} ===")
    print(art["text"][:220] if art else "غير موجودة")
    print()