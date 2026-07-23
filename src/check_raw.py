from pathlib import Path

RAW_PATH = Path("data/raw/labor_law_raw.txt")

text = RAW_PATH.read_text(encoding="utf-8")

print(f"Characters : {len(text)}")
print(f"Lines      : {len(text.splitlines())}")
print("-" * 50)
print("FIRST 200 CHARS:")
print(text[:200])
print("-" * 50)
print("LAST 200 CHARS:")
print(text[-200:])
print("-" * 50)
print(f"'المادة' count : {text.count('المادة')}")
print(f"'الباب'  count : {text.count('الباب')}")