from pathlib import Path
from arabic_ordinals import is_heading_candidate, parse_heading

lines = Path("data/raw/labor_law_raw.txt").read_text(encoding="utf-8").splitlines()

parsed, failed = [], []
for i, line in enumerate(lines):
    if not is_heading_candidate(line):
        continue
    h = parse_heading(line)
    if h is None or h["number"] is None:
        failed.append((i, line.strip()))
    else:
        parsed.append((i, h))

print(f"Candidates: {len(parsed) + len(failed)} | Parsed: {len(parsed)} | Failed: {len(failed)}")
print("=" * 60)

if failed:
    print("FAILED:")
    for i, line in failed:
        print(f"[{i:4}] {line[:90]}")
    print("=" * 60)

renumbered = [(i, h) for i, h in parsed if h["former_number"] is not None]
print(f"Renumbered articles: {len(renumbered)}")
for i, h in renumbered:
    print(f"[{i:4}] {h['number']} (was {h['former_number']})")
print("=" * 60)

nums = [h["number"] for _, h in parsed]
seen, dupes = set(), []
for n in nums:
    if n in seen:
        dupes.append(n)
    seen.add(n)

print(f"Total unique : {len(seen)}")
print(f"Duplicates   : {sorted(set(dupes))}")
print(f"Missing 1-245: {sorted(set(range(1, 246)) - seen)}")
print(f"Out of range : {sorted(n for n in seen if n > 245)}")