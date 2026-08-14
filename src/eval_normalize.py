"""
Nizam — Phase 5: canonical normalization for display_name comparison.
Applied to BOTH sides of every hit@k comparison so a correct answer never
fails on a whitespace/diacritic mismatch. Zero dependencies, offline.
"""
import re
import unicodedata

# Arabic diacritics (tashkeel) range
_TASHKEEL = re.compile(r"[\u064B-\u0652\u0670\u0640]")  # includes tatweel ـ


def normalize_name(s: str) -> str:
    """Canonicalize an Arabic display_name for exact-set comparison."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = _TASHKEEL.sub("", s)          # drop diacritics + tatweel
    s = s.replace("\u00A0", " ")      # non-breaking space -> normal space
    s = re.sub(r"\s+", " ", s)        # collapse all whitespace runs
    return s.strip()


if __name__ == "__main__":
    # sanity: these must all compare equal after normalization
    tests = [
        ("المادة 79 مكرر", "المادة 79 مكرر "),      # trailing space
        ("المادة 79 مكرر", "المادة 79  مكرر"),       # double space
        ("المادة 79 مكرّر", "المادة 79 مكرر"),       # diacritic on ر
        ("المادة 79", "المادة 79"),                  # identical
    ]
    for a, b in tests:
        na, nb = normalize_name(a), normalize_name(b)
        print(f"{na!r} == {nb!r} ? {na == nb}")
    # and this pair must NOT be equal (guards against over-normalizing)
    print("guard:", normalize_name("المادة 79") != normalize_name("المادة 79 مكرر"))