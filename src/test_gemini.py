import os
from dotenv import load_dotenv
from google import genai

# Load variables from .env into the environment
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="أجب بجملة واحدة فقط بالعربية الفصحى: ما هو تعريف عقد العمل؟",
)

print(response.text)