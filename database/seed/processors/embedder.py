"""
CLIP ViT-B/32 image embedder.
Designed to run on SSH VPS with GPU or locally on CPU.
Generates 512-dim embeddings for each image.

Usage (standalone on VPS):
    python -m database.seed.processors.embedder --images-dir /path/to/images --output /path/to/output

Usage (as module):
    from database.seed.processors.embedder import embed_all_images
"""

import os
import sys
import json
import argparse
import numpy as np
from pathlib import Path

CACHE_DIR = None  # Set by init or CLI


def init_cache_dir(project_root):
    """Initialize cache directory."""
    global CACHE_DIR
    CACHE_DIR = os.path.join(project_root, "database", "seed", "cache", "embeddings")
    os.makedirs(CACHE_DIR, exist_ok=True)


def load_clip_model():
    """Load CLIP ViT-B/32 model. Requires sentence-transformers to be installed."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers not installed.")
        print("Install with: pip install 'sentence-transformers[image]'")
        sys.exit(1)
    
    print("  Loading CLIP ViT-B/32 model...")
    model = SentenceTransformer("sentence-transformers/clip-ViT-B-32")
    print("  Model loaded.")
    return model


def embed_single_image(model, image_path):
    """Generate CLIP embedding for a single image.
    
    Returns:
        numpy array of shape (512,)
    """
    from PIL import Image
    img = Image.open(image_path).convert("RGB")
    embedding = model.encode(img, show_progress_bar=False)
    return embedding.astype(np.float32)


def embed_all_images(image_entries, use_cache=True, batch_size=16):
    """Embed all images using CLIP.
    
    Args:
        image_entries: List of dicts with keys: id, image_path
        use_cache: If True, load cached embeddings
        batch_size: Number of images to process at once
        
    Returns:
        dict mapping image_id -> numpy array (512,)
    """
    embeddings_file = os.path.join(CACHE_DIR, "embeddings.npz") if CACHE_DIR else None
    index_file = os.path.join(CACHE_DIR, "embeddings_index.json") if CACHE_DIR else None
    
    # Try loading cache
    if use_cache and embeddings_file and os.path.exists(embeddings_file) and os.path.exists(index_file):
        print("  Loading cached embeddings...")
        data = np.load(embeddings_file)
        with open(index_file, "r") as f:
            index = json.load(f)
        
        results = {}
        for img_id, idx in index.items():
            results[img_id] = data[f"emb_{idx}"]
        
        # Check if all entries are cached
        missing = [e for e in image_entries if e["id"] not in results]
        if not missing:
            print(f"  All {len(results)} embeddings loaded from cache.")
            return results
        print(f"  Found {len(results)} cached, {len(missing)} missing. Re-embedding all...")
    
    # Load model and embed
    model = load_clip_model()
    
    from PIL import Image
    
    results = {}
    total = len(image_entries)
    
    # Process in batches
    for batch_start in range(0, total, batch_size):
        batch = image_entries[batch_start:batch_start + batch_size]
        batch_end = min(batch_start + batch_size, total)
        print(f"  Embedding batch [{batch_start+1}-{batch_end}] of {total}...", flush=True)
        
        images = []
        ids = []
        for entry in batch:
            try:
                img = Image.open(entry["image_path"]).convert("RGB")
                images.append(img)
                ids.append(entry["id"])
            except Exception as e:
                print(f"    WARNING: Could not load {entry['image_path']}: {e}")
        
        if images:
            embeddings = model.encode(images, show_progress_bar=False, batch_size=len(images))
            for img_id, emb in zip(ids, embeddings):
                results[img_id] = emb.astype(np.float32)
    
    # Save to cache
    if CACHE_DIR:
        print(f"  Saving {len(results)} embeddings to cache...")
        index = {}
        arrays = {}
        for i, (img_id, emb) in enumerate(results.items()):
            index[img_id] = i
            arrays[f"emb_{i}"] = emb
        
        np.savez_compressed(os.path.join(CACHE_DIR, "embeddings.npz"), **arrays)
        with open(os.path.join(CACHE_DIR, "embeddings_index.json"), "w") as f:
            json.dump(index, f, indent=2)
        print("  Embeddings cached.")
    
    return results


def main():
    """CLI entrypoint for running on VPS."""
    parser = argparse.ArgumentParser(description="Generate CLIP embeddings for images")
    parser.add_argument("--images-dir", required=True, help="Directory containing image files")
    parser.add_argument("--output-dir", required=True, help="Directory to save embeddings")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    args = parser.parse_args()
    
    global CACHE_DIR
    CACHE_DIR = args.output_dir
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # Find all images
    image_dir = Path(args.images_dir)
    entries = []
    for img_file in sorted(image_dir.rglob("*")):
        if img_file.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            entries.append({
                "id": img_file.stem,
                "image_path": str(img_file),
            })
    
    print(f"Found {len(entries)} images in {args.images_dir}")
    
    results = embed_all_images(entries, use_cache=False, batch_size=args.batch_size)
    
    print(f"\nDone. {len(results)} embeddings saved to {CACHE_DIR}")


if __name__ == "__main__":
    main()
