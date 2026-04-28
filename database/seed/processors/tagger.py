"""
Gemini 2.5 Flash auto-tagger.
Sends each image + its caption to Gemini for structured classification.
Returns room_type, style_tags, dominant_colors, detected_objects, quality_score.

Uses the google.genai SDK with JSON response mode for reliable parsing.
"""

import os
import sys
import json
import time
import re
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load env
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Configure client
client = genai.Client(api_key=os.getenv("GOOGLE_AI_STUDIO_KEY"))

CACHE_DIR = os.path.join(PROJECT_ROOT, "database", "seed", "cache", "tags")
os.makedirs(CACHE_DIR, exist_ok=True)

TAGGING_PROMPT = """You are an interior design image classifier. Analyze this image and its caption.

Caption: "{caption}"

Return a JSON object with these exact fields:
- "room_type": one of: "bedroom", "kitchen", "living room", "study room", "kids room", "mandir", "hallway", "dining room"
- "style_tags": array of style names like "industrial", "japandi", "minimalist", "scandinavian", "mid-century-modern", "modern-ethnic-fusion", "neo-contemporary"
- "dominant_colors": array of 3 hex color codes visible in the image
- "detected_objects": array of key furniture/decor items visible
- "quality_score": float 0-1, rate the image quality and relevance to interior design (1.0 = perfect)
"""


def extract_json(text):
    """Extract JSON from a text response, handling markdown code fences."""
    text = text.strip()
    # Remove markdown code fences
    if "```" in text:
        # Find content between code fences
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()
    return json.loads(text)


def tag_single_image(image_path, caption, image_id, use_cache=True):
    """Tag a single image using Gemini 2.5 Flash.

    Args:
        image_path: Path to the image file
        caption: Pre-written caption text
        image_id: Unique identifier (e.g. '1', '42')
        use_cache: If True, return cached result if available

    Returns:
        dict with room_type, style_tags, dominant_colors, detected_objects, quality_score
    """
    cache_file = os.path.join(CACHE_DIR, f"{image_id}.json")

    # Check cache
    if use_cache and os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)

    # Read image bytes
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Determine mime type
    ext = Path(image_path).suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")

    # Build prompt
    prompt = TAGGING_PROMPT.format(caption=caption)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt),
                            types.Part.from_bytes(data=image_data, mime_type=mime_type),
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

            # Parse response
            result = extract_json(response.text)

            # Validate required fields
            assert "room_type" in result, "Missing room_type"
            assert "style_tags" in result, "Missing style_tags"
            assert "quality_score" in result, "Missing quality_score"

            # Normalize room_type to canonical values
            room_type_raw = result["room_type"].lower().strip()
            room_type_map = {
                "meditation room": "mandir",
                "prayer room": "mandir",
                "pooja room": "mandir",
                "puja room": "mandir",
                "temple room": "mandir",
                "worship room": "mandir",
                "living room": "living room",
                "drawing room": "living room",
                "lounge": "living room",
                "study room": "study room",
                "study": "study room",
                "home office": "study room",
                "office": "study room",
                "kids room": "kids room",
                "children's room": "kids room",
                "kid's room": "kids room",
                "nursery": "kids room",
                "hallway": "hallway",
                "corridor": "hallway",
                "entryway": "hallway",
                "foyer": "hallway",
                "dining room": "dining room",
                "dining": "dining room",
            }
            result["room_type"] = room_type_map.get(room_type_raw, room_type_raw)
            result["style_tags"] = [t.lower().strip() for t in result["style_tags"]]
            result.setdefault("dominant_colors", [])
            result.setdefault("detected_objects", [])

            # Cache result
            with open(cache_file, "w") as f:
                json.dump(result, f, indent=2)

            return result

        except Exception as e:
            print(f"    Attempt {attempt + 1}/{max_retries} failed for image {image_id}: {e}")
            if attempt < max_retries - 1:
                time.sleep(10)  # Wait before retry
            else:
                # Return fallback
                print(f"    WARNING: All retries failed for image {image_id}, using fallback tags")
                fallback = {
                    "room_type": "unknown",
                    "style_tags": [],
                    "dominant_colors": [],
                    "detected_objects": [],
                    "quality_score": 0.5,
                    "error": str(e),
                }
                with open(cache_file, "w") as f:
                    json.dump(fallback, f, indent=2)
                return fallback


def tag_all_images(image_entries, use_cache=True):
    """Tag all images in the dataset.

    Args:
        image_entries: List of dicts with keys: id, image_path, caption
        use_cache: If True, skip already-cached images

    Returns:
        dict mapping image_id -> tag result
    """
    results = {}
    total = len(image_entries)

    for i, entry in enumerate(image_entries):
        img_id = entry["id"]
        cached = os.path.exists(os.path.join(CACHE_DIR, f"{img_id}.json"))
        status = "cached" if (cached and use_cache) else "tagging"
        print(f"  [{i+1}/{total}] Image {img_id}: {status}...", end="", flush=True)

        result = tag_single_image(
            entry["image_path"],
            entry["caption"],
            img_id,
            use_cache=use_cache,
        )
        results[img_id] = result
        print(f" -> {result['room_type']} ({', '.join(result['style_tags'])})")

        # Rate limiting: Gemini free tier = 10 RPM
        if not (cached and use_cache):
            time.sleep(7)  # ~8.5 req/min to stay safe

    return results
