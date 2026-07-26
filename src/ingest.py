"""
Nizam — Phase 1 Ingestion
Parses the raw Saudi Labor Law text into numbered articles with metadata.
"""
from pathlib import Path
import re

RAW_PATH = Path("data/raw/labor_law_raw.txt")
BODY_START_MARKER = "الباب الأول"

# ---------- Arabic ordinal → integer ----------
_ONES = {
    "الاولى": 1, "الثانية": 2, "الثالثة": 3, "الرابعة": 4, "الخامسة": 5,
    "السادسة": 6, "السابعة": 7, "الثامنة": 8, "التاسعة": 9, "العاشرة": 10,
    "الحادية": 1,
    "الاول": 1, "الثاني": 2, "الثالث": 3, "الرابع": 4, "الخامس": 5,
    "السادس": 6, "السابع": 7, "الثامن": 8, "التاسع": 9, "العاشر": 10,
    "الحادي": 1,
}
_TEENS = {
    "الحادية عشرة": 11, "الثانية عشرة": 12, "الثالثة عشرة": 13,
    "الرابعة عشرة": 14, "الخامسة عشرة": 15, "السادسة عشرة": 16,
    "السابعة عشرة": 17, "الثامنة عشرة": 18, "التاسعة عشرة": 19,
    "الحادية عشر": 11, "الثانية عشر": 12, "الثالثة عشر": 13,
    "الرابعة عشر": 14, "الخامسة عشر": 15, "السادسة عشر": 16,
    "السابعة عشر": 17, "الثامنة عشر": 18, "التاسعة عشر": 19,
}
_TENS = {
    "العشرون": 20, "العشرين": 20, "الثلاثون": 30, "الثلاثين": 30,
    "الاربعون": 40, "الاربعين": 40, "الخمسون": 50, "الخمسين": 50,
    "الستون": 60, "الستين": 60, "السبعون": 70, "السبعين": 70,
    "الثمانون": 80, "الثمانين": 80, "التسعون": 90, "التسعين": 90,
}
_TEENS = {
    "الحادية عشرة": 11, "الثانية عشرة": 12, "الثالثة عشرة": 13,
    "الرابعة عشرة": 14, "الخامسة عشرة": 15, "السادسة عشرة": 16,
    "السابعة عشرة": 17, "الثامنة عشرة": 18, "التاسعة عشرة": 19,
    "الحادية عشر": 11, "الثانية عشر": 12, "الثالثة عشر": 13,
    "الرابعة عشر": 14, "الخامسة عشر": 15, "السادسة عشر": 16,
    "السابعة عشر": 17, "الثامنة عشر": 18, "التاسعة عشر": 19,
    # المذكّر — لعناوين الأبواب (الحادي عشر، الثاني عشر ...)
    "الحادي عشر": 11, "الثاني عشر": 12, "الثالث عشر": 13,
    "الرابع عشر": 14, "الخامس عشر": 15, "السادس عشر": 16,
    "السابع عشر": 17, "الثامن عشر": 18, "التاسع عشر": 19,
}
_HUNDREDS = {
    "المائة": 100, "المئة": 100,
    "المائتين": 200, "المائتان": 200, "المئتين": 200, "المئتان": 200,
}


def _normalize_ar(s: str) -> str:
    """Strip diacritics, unify alef/hamza forms, collapse spaces."""
    s = s.replace("\u0640", "")                    # tatweel
    s = re.sub(r"[\u064B-\u0652\u0670]", "", s)    # harakat
    s = re.sub(r"[أإآ]", "ا", s)                    # unify alef
    s = re.sub(r"[:：.،]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def ordinal_to_int(phrase: str):
    """Convert an Arabic ordinal phrase to an integer, or None if unknown."""
    t = _normalize_ar(phrase)
    t = re.sub(r"^المادة\s*", "", t)
    t = re.sub(r"\s*مكرر\s*$", "", t).strip()

    hundreds = 0
    m = re.search(r"بعد\s+(الما[ئي]ت(?:ين|ان)|الما[ئي]ة)", t)
    if m:
        hundreds = _HUNDREDS.get(_normalize_ar(m.group(1)), 0)
        t = t[:m.start()].strip()

    t = _normalize_ar(t)
    if not t:
        return hundreds or None
    if t in _HUNDREDS:
        return _HUNDREDS[t]
    if t in _TEENS:
        return hundreds + _TEENS[t]
    if t in _TENS:
        return hundreds + _TENS[t]
    if t in _ONES:
        return hundreds + _ONES[t]

    parts = t.split()
    if len(parts) == 2 and parts[1].startswith("و"):
        unit = _ONES.get(parts[0])
        ten = _TENS.get(parts[1][1:])
        if unit is not None and ten is not None:
            return hundreds + unit + ten
    return None


# ---------- heading & structure detection ----------
_RE_RENUM = re.compile(
    r"^\(\s*المادة\s+(?P<cur>.+?)\s+حالي\S*\s*\)\s*"
    r"\(\s*المادة\s+(?P<old>.+?)\s+سابق\S*\s*\)\s*:?\s*$"
)
_RE_MUKARRAR = re.compile(r"^\(\s*(?P<ord>.+?مكرر)\s*\)\s*:?\s*$")
_RE_PLAIN = re.compile(r"^المادة\s+(?P<ord>.+?)\s*:?\s*$")
_RE_BAB = re.compile(r"^الباب\s+(?P<ord>[^:]+):\s*(?P<title>.+)$")

_MARKERS = {"تعديلات المادة", "مرفق المادة"}


def detect_heading(line: str):
    """Return a dict describing an article/bab heading, or None."""
    s = line.strip()
    if not s:
        return None

    m = _RE_RENUM.match(s)
    if m:
        return {"type": "article", "number": ordinal_to_int(m.group("cur")),
                "former": ordinal_to_int(m.group("old")), "mukarrar": False}

    m = _RE_MUKARRAR.match(s)
    if m:
        return {"type": "article", "number": ordinal_to_int(m.group("ord")),
                "former": None, "mukarrar": True}

    m = _RE_BAB.match(s)
    if m:
        return {"type": "bab", "number": ordinal_to_int(m.group("ord")),
                "title": m.group("title").strip()}

    m = _RE_PLAIN.match(s)
    if m:
        n = ordinal_to_int(m.group("ord"))
        if n is not None:
            return {"type": "article", "number": n,
                    "former": None, "mukarrar": "مكرر" in s}
    return None

def load_text() -> str:
    """Read raw file and normalize line endings (Windows CRLF -> LF)."""
    text = RAW_PATH.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def strip_preamble(text: str) -> str:
    """Drop the royal decree preamble; keep from the first Bab onward."""
    idx = text.find(BODY_START_MARKER)
    if idx == -1:
        raise ValueError(f"Body start marker '{BODY_START_MARKER}' not found.")
    return text[idx:]


if __name__ == "__main__":
    body = strip_preamble(load_text())
    lines = body.split("\n")

    current_bab = None
    articles, babs = [], []

    for i, line in enumerate(lines):
        h = detect_heading(line)
        if h is None:
            continue
        if h["type"] == "bab":
            current_bab = h
            babs.append(h)
        else:
            articles.append({**h, "bab": current_bab["number"] if current_bab else None,
                             "line": i})

    print(f"Babs detected     : {len(babs)}")
    print(f"Articles detected : {len(articles)}")
    print(f"Mukarrar articles : {[a['number'] for a in articles if a['mukarrar']]}")
    print(f"Renumbered        : {[(a['number'], a['former']) for a in articles if a['former']]}")
    print(f"Articles w/o bab  : {[a['number'] for a in articles if a['bab'] is None]}")
    print("-" * 50)
    print("FIRST 5:", [(a['number'], a['bab']) for a in articles[:5]])
    print("LAST 5 :", [(a['number'], a['bab']) for a in articles[-5:]])