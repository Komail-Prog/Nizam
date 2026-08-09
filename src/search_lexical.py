"""
Nizam — Phase 2: Lexical (BM25) search with Arabic normalization.
"""
import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

CHUNKS_PATH = Path("data/processed/chunks.json")

_ALEF = re.compile(r"[إأآا]")
_HARAKAT = re.compile(r"[\u064B-\u0652\u0670]")
_TATWEEL = "\u0640"


def normalize_ar(text: str) -> str:
    """Medium normalization: unify alef/ta/ya, strip harakat, drop leading 'ال'."""
    text = text.replace(_TATWEEL, "")
    text = _HARAKAT.sub("", text)
    text = _ALEF.sub("ا", text)
    text = text.replace("ة", "ه").replace("ى", "ي")
    text = text.replace("ؤ", "و").replace("ئ", "ي").replace("ء", "")
    return text


def tokenize(text: str) -> list:
    """Normalize, split on non-Arabic-letter boundaries, strip leading 'ال'."""
    text = normalize_ar(text)
    # keep Arabic letters and digits, split on everything else
    tokens = re.findall(r"[\u0621-\u064A0-9]+", text)
    # drop the definite article prefix 'ال' from each token (length > 3)
    cleaned = []
    for t in tokens:
        if t.startswith("ال") and len(t) > 3:
            cleaned.append(t[2:])
        else:
            cleaned.append(t)
    return cleaned


class LexicalIndex:
    def __init__(self):
        self.chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
        corpus = [tokenize(c["text"]) for c in self.chunks]
        self.bm25 = BM25Okapi(corpus)

    def search(self, query: str, k: int = 5):
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        hits = []
        for i in ranked:
            c = self.chunks[i]
            hits.append({
                "display_name": c["display_name"],
                "term": c["term"] or "",
                "score": scores[i],
                "text": c["text"],
            })
        return hits


if __name__ == "__main__":
    idx = LexicalIndex()
    tests = [
        "كم مدة الإجازة السنوية للعامل؟",
        "متى يحق لصاحب العمل فصل العامل دون مكافأة؟",
        "ما هي أحكام المادة 109؟",
    ]
    for q in tests:
        print("=" * 65)
        print(f"❓ {q}")
        print(f"   tokens: {tokenize(q)}")
        print("-" * 65)
        for i, h in enumerate(idx.search(q, k=3), 1):
            term = f" [{h['term']}]" if h["term"] else ""
            print(f"  {i}. {h['display_name']}{term}  (score={h['score']:.2f})")
            print(f"     {h['text'][:60]}...")