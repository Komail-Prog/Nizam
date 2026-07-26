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


def collect_blocks(lines):
    """Walk lines, attach each article to its bab, and gather its body text."""
    heads = []
    current_bab = None
    for i, line in enumerate(lines):
        h = detect_heading(line)
        if h is None:
            continue
        if h["type"] == "bab":
            current_bab = h
        else:
            heads.append({**h, "bab": current_bab["number"], "start": i})

    blocks = []
    # Build a set of ALL heading line indices (articles AND babs) to bound bodies
    heading_lines = set()
    for i, line in enumerate(lines):
        if detect_heading(line) is not None:
            heading_lines.add(i)

    blocks = []
    for k, head in enumerate(heads):
        start = head["start"]
        # body ends at the next heading line of ANY kind (article or bab)
        end = start + 1
        while end < len(lines) and end not in heading_lines:
            end += 1
        body_lines = lines[start + 1:end]

        marker = None
        text_parts = []
        for bl in body_lines:
            s = bl.strip()
            if not s:
                continue
            if s in _MARKERS:
                if marker is None:
                    marker = s
                continue
            text_parts.append(s)

        blocks.append({
            "number": head["number"],
            "former": head["former"],
            "mukarrar": head["mukarrar"],
            "bab": head["bab"],
            "marker": marker,
            "text": " ".join(text_parts),
            "start": start,
        })
    return blocks
    


def resolve_conflicts(blocks):
    """Keep the current version of each article number; record exclusions."""
    from collections import defaultdict
    by_key = defaultdict(list)
    for b in blocks:
        # mukarrar articles get their own identity, never conflict with base
        key = (b["number"], b["mukarrar"])
        by_key[key].append(b)

    kept, excluded = [], []
    for key, group in by_key.items():
        if len(group) == 1:
            kept.append(group[0])
            continue
        # conflict: prefer مرفق marker, else prefer the renumbered (former set)
        winner = None
        for b in group:
            if b["marker"] == "مرفق المادة":
                winner = b
                break
        if winner is None:
            for b in group:
                if b["former"] is not None:
                    winner = b
                    break
        if winner is None:
            winner = group[0]  # fallback, should not happen here
        kept.append(winner)
        for b in group:
            if b is not winner:
                excluded.append(b)
    return kept, excluded

def clean_marfaq_text(block):
    """Extract quoted statutory text from decree-added articles.

    Applies whenever the body embeds the actual text inside quotes following
    a decree preamble ("... بالنص الآتي: \"...\""), regardless of marker,
    since مكرر articles may lack a separate مرفق المادة marker line.
    """
    text = block["text"]
    # Only act if it looks like a decree-wrapper: has an addition phrase + quotes
    is_wrapper = ("اُضيفت" in text or "أُضيفت" in text or "إضافة مادة" in text)
    first = text.find('"')
    last = text.rfind('"')
    if is_wrapper and first != -1 and last != -1 and last > first:
        quoted = text[first + 1:last].strip()
        note = (text[:first] + " " + text[last + 1:]).strip()
        if quoted:                       # never blank out the article
            block["text"] = quoted
            block["amendment_note"] = note
    return block


import json


def build_records(kept):
    """Convert kept blocks into final article records with clean metadata."""
    ORD_WORDS = {
        1: "الأولى", 2: "الثانية", 3: "الثالثة", 4: "الرابعة", 5: "الخامسة",
    }
    records = []
    for b in kept:
        suffix = "_mukarrar" if b["mukarrar"] else ""
        display = f"المادة {b['number']}" + (" مكرر" if b["mukarrar"] else "")
        rec = {
            "article_id": f"art_{b['number']:03d}{suffix}",
            "number": b["number"],
            "is_mukarrar": b["mukarrar"],
            "former_number": b["former"],
            "display_name": display,
            "bab_number": b["bab"],
            "text": b["text"].strip(),
            "char_count": len(b["text"].strip()),
        }
        if b.get("amendment_note"):
            rec["amendment_note"] = b["amendment_note"].strip()
        records.append(rec)
    return records


BAB_TITLES = {}


def collect_bab_titles(lines):
    titles = {}
    current = None
    for line in lines:
        h = detect_heading(line)
        if h and h["type"] == "bab":
            titles[h["number"]] = h["title"]
    return titles


if __name__ == "__main__":
    body = strip_preamble(load_text())
    lines = body.split("\n")

    blocks = collect_blocks(lines)
    kept, excluded = resolve_conflicts(blocks)
    kept = [clean_marfaq_text(b) for b in kept]
    kept.sort(key=lambda b: b["start"])

    bab_titles = collect_bab_titles(lines)
    records = build_records(kept)
    for r in records:
        r["bab_title"] = bab_titles.get(r["bab_number"], "")

    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "articles.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    excluded_records = [{
        "number": b["number"], "reason": "old-numbering duplicate (superseded)",
        "marker": b["marker"], "text_preview": b["text"][:80],
    } for b in excluded]
    (out_dir / "excluded.json").write_text(
        json.dumps(excluded_records, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ---- Phase 1 transition gate: sample of 10 articles with correct numbers ----
    print(f"✅ Wrote {len(records)} articles → data/processed/articles.json")
    print(f"✅ Wrote {len(excluded_records)} excluded → data/processed/excluded.json")
    print("=" * 60)
    print("SAMPLE OF 10 ARTICLES:")
    sample_nums = [1, 2, 84, 85, 98, 109, 165, "79_mukarrar", 234, 245]
    for r in records:
        tag = f"{r['number']}_mukarrar" if r["is_mukarrar"] else r["number"]
        if tag in sample_nums or r["number"] in sample_nums and not r["is_mukarrar"]:
            print(f"[{r['display_name']}] (باب {r['bab_number']}: {r['bab_title']}) "
                  f"[{r['char_count']} حرف]")
            print(f"   {r['text'][:70]}...")