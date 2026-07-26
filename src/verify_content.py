from pathlib import Path
import hashlib

raw = Path("data/raw/labor_law_raw.txt").read_text(encoding="utf-8")

# Normalize line endings, then hash — this ignores CRLF vs LF differences
normalized = raw.replace("\r\n", "\n").replace("\r", "\n")

h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

print(f"Chars (raw)        : {len(raw)}")
print(f"Chars (normalized) : {len(normalized)}")
print(f"CRLF pairs         : {raw.count(chr(13) + chr(10))}")
print(f"Lone LF            : {normalized.count(chr(10))}")
print(f"Normalized SHA256  : {h}")