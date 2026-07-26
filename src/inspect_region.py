from pathlib import Path

lines = Path("data/raw/labor_law_raw.txt").read_text(encoding="utf-8").splitlines()

START, END = 870, 945

for i in range(START, min(END, len(lines))):
    content = lines[i].strip()
    if content:
        print(f"[{i:4}] {content[:130]}")