"""
Standalone CLIP embedding script for VPS.
No database dependencies — just reads images and outputs numpy files.

Usage:
    python3 embed_images.py --images-dir /path/to/images --output-dir /path/to/output
    python3 embed_images.py --images-dir /path/to/images --output-dir /path/to/output --batch-size 32 --gpu
"""

import os
import sys
import json
import argparse
import time
import numpy as np
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Generate CLIP ViT-B/32 embeddings for images")
    parser.add_argument("--images-dir", required=True, help="Root directory with style subdirectories containing images")
    parser.add_argument("--output-dir", required=True, help="Directory to save embeddings output")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for encoding")
    parser.add_argument("--gpu", action="store_true", help="Use GPU if available")
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Find all images
    image_dir = Path(args.images_dir)
    entries = []
    
    # Scan subdirectories (style folders)
    for style_dir in sorted(image_dir.iterdir()):
        if not style_dir.is_dir():
            continue
        for img_file in sorted(style_dir.iterdir()):
            if img_file.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                entries.append({
                    "id": img_file.stem,
                    "path": str(img_file),
                    "style": style_dir.name,
                })
    
    # Also check root level
    for img_file in sorted(image_dir.iterdir()):
        if img_file.is_file() and img_file.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            entries.append({
                "id": img_file.stem,
                "path": str(img_file),
                "style": "root",
            })
    
    print(f"Found {len(entries)} images")
    
    if not entries:
        print("ERROR: No images found!")
        sys.exit(1)
    
    # Load model
    print("Loading CLIP ViT-B/32 model...")
    from sentence_transformers import SentenceTransformer
    from PIL import Image
    
    device = "cpu"
    if args.gpu:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
    
    model = SentenceTransformer("sentence-transformers/clip-ViT-B-32", device=device)
    print("Model loaded.\n")
    
    # Process in batches
    start = time.time()
    results = {}
    total = len(entries)
    
    for batch_start in range(0, total, args.batch_size):
        batch = entries[batch_start:batch_start + args.batch_size]
        batch_end = min(batch_start + args.batch_size, total)
        print(f"  Batch [{batch_start+1}-{batch_end}] of {total}...", end="", flush=True)
        
        images = []
        ids = []
        for entry in batch:
            try:
                img = Image.open(entry["path"]).convert("RGB")
                images.append(img)
                ids.append(entry["id"])
            except Exception as e:
                print(f"\n    WARNING: Could not load {entry['path']}: {e}")
        
        if images:
            embeddings = model.encode(images, show_progress_bar=False, batch_size=len(images))
            for img_id, emb in zip(ids, embeddings):
                results[img_id] = emb.astype(np.float32)
            print(f" OK ({len(images)} images)")
        else:
            print(" SKIP (no valid images)")
    
    elapsed = time.time() - start
    
    # Save output
    print(f"\nSaving {len(results)} embeddings...")
    
    index = {}
    arrays = {}
    for i, (img_id, emb) in enumerate(sorted(results.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0])):
        index[img_id] = i
        arrays[f"emb_{i}"] = emb
    
    np.savez_compressed(os.path.join(args.output_dir, "embeddings.npz"), **arrays)
    with open(os.path.join(args.output_dir, "embeddings_index.json"), "w") as f:
        json.dump(index, f, indent=2)
    
    print(f"\nDone!")
    print(f"  Embeddings: {len(results)}")
    print(f"  Dimension: 512")
    print(f"  Time: {elapsed:.1f}s ({elapsed/len(results):.2f}s per image)")
    print(f"  Output: {args.output_dir}/embeddings.npz + embeddings_index.json")
    print(f"\nCopy these files to: database/seed/cache/embeddings/ on your local machine.")


if __name__ == "__main__":
    main()
