"""
Seed pipeline configuration.
Central constants for paths, styles, room types, and thresholds.
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# === Paths ===
# Styled reference folders live here (see STYLE_FOLDERS). Rename or symlink if migrating from an older dataset folder.
IMAGES_DIR = os.path.join(PROJECT_ROOT, "reference_dataset")
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

