from pathlib import Path

RAW_PATH = Path("data/raw/labor_law_raw.txt")
lines = RAW_PATH.read_text(encoding="utf-8").splitlines()

# Candidate headings: lines that START with "المادة"
candidates = [
    (i, line.strip())
    for i, line in enumerate(lines)
    if line.strip().startswith("المادة")
]

print(f"Total lines                  : {len(lines)}")
print(f"Lines STARTING with 'المادة' : {len(candidates)}")
print("=" * 60)

print("FIRST 20 CANDIDATES:")
for i, line in candidates[:20]:
    print(f"[{i:4}] {line}")

print("=" * 60)
print("LAST 8 CANDIDATES:")
for i, line in candidates[-8:]:
    print(f"[{i:4}] {line}")

print("=" * 60)
for marker in ("الباب", "الفصل"):
    hits = [l.strip() for l in lines if l.strip().startswith(marker)]
    print(f"Lines STARTING with '{marker}' : {len(hits)}")
    for h in hits[:6]:
        print(f"    {h}")
    print("-" * 40)