"""
Supabase Storage uploader.
Uploads reference images to a Supabase Storage bucket and returns public URLs.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from database.seed import supabase_rest


def ensure_bucket(bucket_name):
    """Create the storage bucket if it doesn't exist."""
    try:
        supabase_rest.ensure_bucket_public(bucket_name)
        print(f"  Bucket '{bucket_name}' ready (public).")
    except Exception as e:
        print(f"  Bucket note: {e}")


def upload_image(bucket_name, local_path, storage_path):
    """Upload a single image to Supabase Storage."""
    with open(local_path, "rb") as f:
        file_data = f.read()

    ext = Path(local_path).suffix.lower()
    content_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    content_type = content_types.get(ext, "image/png")

    try:
        supabase_rest.upload_object(bucket_name, storage_path, file_data, content_type)
    except Exception as e:
        print(f"    WARNING: Could not upload {storage_path}: {e}")
        return None

    return supabase_rest.public_url(bucket_name, storage_path)


def upload_all_images(image_entries, bucket_name="reference-images"):
    """Upload all images to Supabase Storage.
    
    Args:
        image_entries: List of dicts with keys: id, image_path, style_folder
        bucket_name: Supabase Storage bucket name
        
    Returns:
        dict mapping image_id -> {storage_path, public_url}
    """
    ensure_bucket(bucket_name)
    
    results = {}
    total = len(image_entries)
    
    for i, entry in enumerate(image_entries):
        img_id = entry["id"]
        filename = os.path.basename(entry["image_path"])
        style_folder = entry.get("style_folder", "unknown")
        storage_path = f"{style_folder}/{filename}"
        
        print(f"  [{i+1}/{total}] Uploading {storage_path}...", end="", flush=True)
        
        url = upload_image(bucket_name, entry["image_path"], storage_path)
        
        if url:
            results[img_id] = {
                "storage_path": storage_path,
                "public_url": url,
            }
            print(" OK")
        else:
            print(" FAILED")
    
    return results
