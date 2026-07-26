import re

ONES = {
    "الأولى": 1, "الثانية": 2, "الثالثة": 3, "الرابعة": 4, "الخامسة": 5,
    "السادسة": 6, "السابعة": 7, "الثامنة": 8, "التاسعة": 9, "العاشرة": 10,
}

TEENS = {
    "الحادية عشرة": 11, "الثانية عشرة": 12, "الثالثة عشرة": 13,
    "الرابعة عشرة": 14, "الخامسة عشرة": 15, "السادسة عشرة": 16,
    "السابعة عشرة": 17, "الثامنة عشرة": 18, "التاسعة عشرة": 19,
}

TENS = {
    "العشرون": 20, "العشرين": 20, "الثلاثون": 30, "الثلاثين": 30,
    "الأربعون": 40, "الأربعين": 40, "الخمسون": 50, "الخمسين": 50,
    "الستون": 60, "الستين": 60, "السبعون": 70, "السبعين": 70,
    "الثمانون": 80, "الثمانين": 80, "التسعون": 90, "التسعين": 90,
}

# Units as used in compounds: "الحادية والعشرون"
COMPOUND_ONES = {
    "الحادية": 1, "الثانية": 2, "الثالثة": 3, "الرابعة": 4, "الخامسة": 5,
    "السادسة": 6, "السابعة": 7, "الثامنة": 8, "التاسعة": 9,
}


def normalize(text: str) -> str:
    """Remove diacritics-free noise: alef variants, colons, extra spaces."""
    text = text.replace("ـ", "")
    text = re.sub(r"[:：]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def ordinal_to_int(heading: str):
    """Convert an Arabic ordinal article heading to an integer. None if unknown."""
    text = normalize(heading)
    text = re.sub(r"^المادة\s*", "", text)

    hundreds = 0
    if re.search(r"بعد\s+الما?ئتين", text):
        hundreds = 200
        text = re.sub(r"بعد\s+الما?ئتين", "", text)
    elif re.search(r"بعد\s+الما?ئة", text):
        hundreds = 100
        text = re.sub(r"بعد\s+الما?ئة", "", text)

    text = normalize(text)

    if not text:  # "المادة المائة" style handled below
        return hundreds or None
    if text in ("المائة", "المئة"):
        return 100
    if text in ("المائتان", "المائتين", "المئتان", "المئتين"):
        return 200
    if text in TEENS:
        return hundreds + TEENS[text]
    if text in ONES:
        return hundreds + ONES[text]
    if text in TENS:
        return hundreds + TENS[text]

    # Compound: "الحادية والعشرون"
    parts = text.split()
    if len(parts) == 2 and parts[1].startswith("و"):
        unit = COMPOUND_ONES.get(parts[0])
        ten = TENS.get(parts[1][1:])
        if unit is not None and ten is not None:
            return hundreds + unit + ten

    return None
# Renumbered heading: "(المادة X حالياً) (المادة Y سابقاً)"
RENUMBERED_RE = re.compile(r"^\(\s*المادة\s+(?P<current>.+?)\s+حالي\S*\s*\)")
FORMER_RE = re.compile(r"\(\s*المادة\s+(?P<former>.+?)\s+سابق\S*\s*\)")


def is_heading_candidate(line: str) -> bool:
    return bool(re.match(r"^\(?\s*المادة", line.strip()))


def parse_heading(line: str):
    """Return {'number', 'former_number', 'raw'} or None if not a heading."""
    line = line.strip()

    m = RENUMBERED_RE.match(line)
    if m:
        rest = line[m.end():]
        former_m = FORMER_RE.search(rest)
        return {
            "number": ordinal_to_int(m.group("current")),
            "former_number": ordinal_to_int(former_m.group("former")) if former_m else None,
            "raw": line,
        }

    if line.startswith("المادة"):
        return {"number": ordinal_to_int(line), "former_number": None, "raw": line}

    return None