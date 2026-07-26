from pathlib import Path
from collections import defaultdict
from arabic_ordinals import is_heading_candidate, parse_heading

lines = Path("data/raw/labor_law_raw.txt").read_text(encoding="utf-8").splitlines()

occurrences = defaultdict(list)
renumbered = []

for i, line in enumerate(lines):
    if not is_heading_candidate(line):
        continue
    h = parse_heading(line)
    if h and h["number"] is not None:
        occurrences[h["number"]].append(i)
        if h["former_number"] is not None:
            renumbered.append((i, h["number"], h["former_number"]))

print(f"Renumbered articles found: {len(renumbered)}")
for i, num, former in renumbered:
    print(f"  [{i:4}] {num} (was {former})")
print("=" * 70)

dupes = {n: idxs for n, idxs in occurrences.items() if len(idxs) > 1}
print(f"Duplicate numbers: {sorted(dupes)}")
print("=" * 70)

for num in sorted(dupes):
    print(f"### ARTICLE {num} appears {len(dupes[num])} times")
    for idx in dupes[num]:
        print(f"  --- line {idx} ---")
        for j in range(idx, min(idx + 4, len(lines))):
            content = lines[j].strip()
            if content:
                print(f"    {content[:110]}")
    print("=" * 70)