"""Quick test of Gemini tagging with thinking disabled."""
import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(".env")
client = genai.Client(api_key=os.getenv("GOOGLE_AI_STUDIO_KEY"))

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_sample = os.path.join(_root, "reference_dataset", "industrial", "1.png")
with open(_sample, "rb") as f:
    img_data = f.read()

prompt = 'Classify this interior design image. Return JSON: {"room_type":"...","style_tags":["..."],"dominant_colors":["#hex"],"detected_objects":["..."],"quality_score":0.0}'

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
                types.Part.from_bytes(data=img_data, mime_type="image/png"),
            ],
        ),
    ],
    config=types.GenerateContentConfig(
        temperature=0.1,
        max_output_tokens=2000,
        response_mime_type="application/json",
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    ),
)

print("=== RAW RESPONSE ===")
print(repr(response.text))
print()
try:
    parsed = json.loads(response.text)
    print(json.dumps(parsed, indent=2))
except Exception as e:
    print(f"JSON parse error: {e}")
print("=== END ===")
