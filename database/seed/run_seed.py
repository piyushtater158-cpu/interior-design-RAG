"""
Main seed pipeline orchestrator.
Reads local images + captions, tags via Gemini, uploads to Supabase Storage,
optionally embeds via CLIP, and inserts everything into the database.

Usage:
    python database/seed/run_seed.py                    # Full pipeline (no embeddings)
    python database/seed/run_seed.py --with-embeddings  # Include CLIP embeddings
    python database/seed/run_seed.py --skip-tag         # Skip Gemini tagging (use cache)
    python database/seed/run_seed.py --skip-upload      # Skip Supabase Storage upload
    python database/seed/run_seed.py --tag-only          # Only run tagging step
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from database.seed.config import (
    IMAGES_DIR, CAPTIONS_DIR, CACHE_DIR, STYLE_FOLDERS, STORAGE_BUCKET
)
from database.seed.processors.tagger import tag_all_images
from database.seed.uploader import upload_all_images
from database.seed.inserter import insert_all


def discover_images():
    """Scan the local dataset and build a list of image entries.
    
    Returns:
        List of dicts: {id, image_path, caption, style_folder}
    """
    entries = []
    
    for folder_name, canonical_style in STYLE_FOLDERS.items():
        folder_path = os.path.join(IMAGES_DIR, folder_name)
        if not os.path.isdir(folder_path):
            print(f"  WARNING: Style folder not found: {folder_path}")
            continue
        
        # Find all image files in this style folder
        for img_file in sorted(Path(folder_path).iterdir()):
            if img_file.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
                continue
            
            img_id = img_file.stem  # e.g. '1', '42'
            
            # Find matching caption
            caption_file = os.path.join(CAPTIONS_DIR, f"{img_id}.txt")
            caption = ""
            if os.path.exists(caption_file):
                with open(caption_file, "r", encoding="utf-8") as f:
                    caption = f.read().strip()
            
            entries.append({
                "id": img_id,
                "image_path": str(img_file),
                "caption": caption,
                "style_folder": canonical_style,
            })
    
    return entries


def generate_seed_report(entries, tags, upload_results, embeddings, stats, elapsed):
    """Generate the seed report markdown file.
    
    Args:
        entries: image entries list
        tags: dict of tag results
        upload_results: dict of upload results
        embeddings: dict of embeddings (or None)
        stats: insertion stats dict
        elapsed: total elapsed seconds
    """
    contracts_dir = os.path.join(PROJECT_ROOT, "contracts")
    os.makedirs(contracts_dir, exist_ok=True)
    
    # Compute statistics
    room_style_matrix = defaultdict(lambda: defaultdict(int))
    room_counts = defaultdict(int)
    style_counts = defaultdict(int)
    quality_scores = []
    
    for entry in entries:
        img_id = entry["id"]
        tag = tags.get(img_id, {})
        room = tag.get("room_type", "unknown")
        styles = tag.get("style_tags", [entry["style_folder"]])
        quality = tag.get("quality_score", 0)
        
        room_counts[room] += 1
        for s in styles:
            style_counts[s] += 1
            room_style_matrix[room][s] += 1
        quality_scores.append(quality)
    
    quality_scores.sort()
    n = len(quality_scores)
    mean_q = sum(quality_scores) / n if n > 0 else 0
    median_q = quality_scores[n // 2] if n > 0 else 0
    p25_q = quality_scores[n // 4] if n > 0 else 0
    p75_q = quality_scores[3 * n // 4] if n > 0 else 0
    
    # Build report
    report = f"""# Seed Report

**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Elapsed:** {elapsed:.1f} seconds  
**Total images processed:** {len(entries)}

## Image Counts by Room Type

| Room Type | Count |
|---|---|
"""
    for room, count in sorted(room_counts.items()):
        report += f"| {room} | {count} |\n"
    
    report += f"""
## Image Counts by Style

| Style | Count |
|---|---|
"""
    for style, count in sorted(style_counts.items()):
        report += f"| {style} | {count} |\n"
    
    report += f"""
## Room x Style Matrix

| Room \\ Style | {' | '.join(sorted(style_counts.keys()))} |
|---|{'---|' * len(style_counts)}
"""
    for room in sorted(room_counts.keys()):
        row = f"| {room} |"
        for style in sorted(style_counts.keys()):
            row += f" {room_style_matrix[room][style]} |"
        report += row + "\n"
    
    report += f"""
## Quality Score Statistics

| Metric | Value |
|---|---|
| Count | {n} |
| Mean | {mean_q:.3f} |
| Median | {median_q:.3f} |
| P25 | {p25_q:.3f} |
| P75 | {p75_q:.3f} |
| Min | {min(quality_scores) if quality_scores else 0:.3f} |
| Max | {max(quality_scores) if quality_scores else 0:.3f} |

## Embedding Statistics

| Metric | Value |
|---|---|
| Embeddings generated | {len(embeddings) if embeddings else 0} |
| Embedding dimension | 512 (CLIP ViT-B/32) |
| 1:1 with images | {'Yes' if embeddings and len(embeddings) == len(entries) else 'No'} |

## Upload Statistics

| Metric | Value |
|---|---|
| Images uploaded to Supabase | {len(upload_results)} |
| Upload failures | {len(entries) - len(upload_results)} |

## Insertion Statistics

| Metric | Value |
|---|---|
| Images inserted | {stats.get('images_inserted', 0)} |
| Images skipped | {stats.get('images_skipped', 0)} |
| Embeddings inserted | {stats.get('embeddings_inserted', 0)} |

## Cost Summary

| Item | Cost |
|---|---|
| Gemini 2.5 Flash tagging (free tier) | $0.00 |
| Supabase Storage (free tier) | $0.00 |
| CLIP embeddings (local/VPS) | $0.00 |
| **Total** | **$0.00** |
"""
    
    report_path = os.path.join(contracts_dir, "seed-report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n  Seed report written to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Run the seed pipeline")
    parser.add_argument("--skip-tag", action="store_true", help="Skip Gemini tagging (use cached)")
    parser.add_argument("--skip-upload", action="store_true", help="Skip Supabase Storage upload")
    parser.add_argument("--with-embeddings", action="store_true", help="Include CLIP embeddings (requires sentence-transformers)")
    parser.add_argument("--tag-only", action="store_true", help="Only run tagging step")
    parser.add_argument("--no-insert", action="store_true", help="Skip database insertion")
    args = parser.parse_args()
    
    start_time = time.time()
    
    print("\n" + "=" * 60)
    print("  SEED PIPELINE")
    print("=" * 60)
    
    # ──────────────────────────────────────────────
    # Step 1: Discover local images
    # ──────────────────────────────────────────────
    print("\n[1/5] Discovering local images...")
    entries = discover_images()
    print(f"  Found {len(entries)} images across {len(STYLE_FOLDERS)} style folders.")
    
    # Print summary
    style_summary = defaultdict(int)
    caption_count = sum(1 for e in entries if e["caption"])
    for e in entries:
        style_summary[e["style_folder"]] += 1
    for style, count in sorted(style_summary.items()):
        print(f"    {style}: {count} images")
    print(f"  Captions found: {caption_count}/{len(entries)}")
    
    if not entries:
        print("  ERROR: No images found. Check IMAGES_DIR in config.py")
        sys.exit(1)
    
    # ──────────────────────────────────────────────
    # Step 2: Tag images via Gemini (always uses cache if present)
    # ──────────────────────────────────────────────
    os.makedirs(CACHE_DIR, exist_ok=True)
    if args.skip_tag:
        print("\n[2/5] Loading tags from cache (--skip-tag)...")
        tags = {}
        tags_cache_dir = os.path.join(CACHE_DIR, "tags")
        for entry in entries:
            cache_file = os.path.join(tags_cache_dir, f"{entry['id']}.json")
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    tags[entry["id"]] = json.load(f)
    else:
        print("\n[2/5] Tagging images via Gemini 2.5 Flash...")
        tags = tag_all_images(entries, use_cache=True)

    tagged_count = sum(1 for t in tags.values() if t.get("room_type") != "unknown")
    print(f"  Successfully tagged: {tagged_count}/{len(entries)}")
    
    if args.tag_only:
        print("\n  --tag-only flag set. Stopping after tagging.")
        elapsed = time.time() - start_time
        print(f"\n  Done in {elapsed:.1f}s")
        return
    
    # ──────────────────────────────────────────────
    # Step 3: Upload to Supabase Storage
    # ──────────────────────────────────────────────
    upload_results = {}
    if not args.skip_upload:
        print("\n[3/5] Uploading images to Supabase Storage...")
        upload_results = upload_all_images(entries, bucket_name=STORAGE_BUCKET)
        print(f"  Uploaded: {len(upload_results)}/{len(entries)}")
    else:
        print("\n[3/5] Skipping upload (--skip-upload)")
        # Try loading from cache
        upload_cache = os.path.join(CACHE_DIR, "upload_results.json")
        if os.path.exists(upload_cache):
            with open(upload_cache, "r") as f:
                upload_results = json.load(f)
            print(f"  Loaded {len(upload_results)} cached upload results.")
    
    # Cache upload results
    if upload_results:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(os.path.join(CACHE_DIR, "upload_results.json"), "w") as f:
            json.dump(upload_results, f, indent=2)
    
    # ──────────────────────────────────────────────
    # Step 4: Generate CLIP embeddings (optional)
    # ──────────────────────────────────────────────
    embeddings = None
    if args.with_embeddings:
        print("\n[4/5] Generating CLIP embeddings...")
        from database.seed.processors.embedder import embed_all_images, init_cache_dir
        init_cache_dir(PROJECT_ROOT)
        embeddings = embed_all_images(entries, use_cache=True)
        print(f"  Embeddings: {len(embeddings)}/{len(entries)}")
    else:
        print("\n[4/5] Skipping embeddings (use --with-embeddings or run on VPS)")
        # Try loading cached embeddings
        emb_cache = os.path.join(PROJECT_ROOT, "database", "seed", "cache", "embeddings")
        index_file = os.path.join(emb_cache, "embeddings_index.json")
        npz_file = os.path.join(emb_cache, "embeddings.npz")
        if os.path.exists(index_file) and os.path.exists(npz_file):
            import numpy as np
            print("  Loading cached embeddings from VPS output...")
            data = np.load(npz_file)
            with open(index_file, "r") as f:
                index = json.load(f)
            embeddings = {}
            for img_id, idx in index.items():
                embeddings[img_id] = data[f"emb_{idx}"]
            print(f"  Loaded {len(embeddings)} cached embeddings.")
    
    # ──────────────────────────────────────────────
    # Step 5: Insert into database
    # ──────────────────────────────────────────────
    stats = {}
    if not args.no_insert:
        print("\n[5/5] Inserting into database...")
        stats = insert_all(entries, tags, upload_results, embeddings)
        print(f"\n  Insertion complete:")
        print(f"    Images inserted: {stats['images_inserted']}")
        print(f"    Images skipped: {stats['images_skipped']}")
        print(f"    Embeddings inserted: {stats['embeddings_inserted']}")
    else:
        print("\n[5/5] Skipping insertion (--no-insert)")
    
    # ──────────────────────────────────────────────
    # Generate seed report
    # ──────────────────────────────────────────────
    elapsed = time.time() - start_time
    print("\n" + "-" * 40)
    print("  Generating seed report...")
    generate_seed_report(entries, tags, upload_results, embeddings, stats, elapsed)
    
    print(f"\n{'=' * 60}")
    print(f"  SEED PIPELINE COMPLETE")
    print(f"  Total time: {elapsed:.1f}s")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
