"""
Seed pipeline configuration.
Central constants for paths, styles, room types, and thresholds.
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === Paths ===
IMAGES_DIR = os.path.join(PROJECT_ROOT, "interior design lora training data set")
CAPTIONS_DIR = os.path.join(PROJECT_ROOT, "Interior design samples")
CACHE_DIR = os.path.join(PROJECT_ROOT, "database", "seed", "cache")

# === Style folder mapping (folder name -> canonical style name) ===
STYLE_FOLDERS = {
    "industrial": "industrial",
    "Japandi": "japandi",
    "mid century modern": "mid-century-modern",
    "Minimilist": "minimalist",
    "Modern ethnic fusion": "modern-ethnic-fusion",
    "Neo comtemporary": "neo-contemporary",
    "scandenavian style": "scandinavian",
}

# === Room types recognized by the tagger ===
ROOM_TYPES = [
    "bedroom",
    "kitchen",
    "living room",
    "study room",
    "kids room",
    "mandir",
    "hallway",
    "dining room",
]

# === Quality thresholds ===
MIN_QUALITY_SCORE = 0.7

# === Supabase Storage ===
STORAGE_BUCKET = "reference-images"

# === Embedding ===
CLIP_MODEL_NAME = "sentence-transformers/clip-ViT-B-32"
CLIP_EMBEDDING_DIM = 512
EMBEDDING_TYPE = "clip-vit-b32"
