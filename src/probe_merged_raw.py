"""
Nizam — Phase 5 diagnostic: inspect RAW Gemini response for a general (non-tool)
question under the merged config. ONE Gemini call. Reveals why json.loads fails.
Run from project root, .venv active. Wait ~30s after previous run (rate limit).
"""
import os, json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from retriever import retrieve
from generator import MERGED_SYSTEM_INSTRUCTION, EOS_TOOL, build_context

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

query = "كم مدة إجازة الوضع للمرأة العاملة؟"
articles = retrieve(query, k=3)
context = build_context(articles)
prompt = f"السؤال: {query}\n\nالمواد المسترجَعة:\n{context}"

resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        system_instruction=MERGED_SYSTEM_INSTRUCTION,
        tools=[EOS_TOOL],
        temperature=0.0,
    ),
)

parts = resp.candidates[0].content.parts
print("=" * 60)
print("عدد الأجزاء (parts):", len(parts))
for i, p in enumerate(parts):
    print(f"\n--- part[{i}] ---")
    print("  has function_call:", bool(getattr(p, "function_call", None)))
    txt = getattr(p, "text", None)
    print("  has text:", txt is not None)
    if txt is not None:
        print("  text repr (أول 300):")
        print("  ", repr(txt[:300]))