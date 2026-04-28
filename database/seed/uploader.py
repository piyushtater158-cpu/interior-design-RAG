"""
Supabase Storage uploader.
Uploads reference images to a Supabase Storage bucket and returns public URLs.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def get_supabase_client():
    """Create Supabase client."""
    from supabase import create_client
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY not set in .env")
        sys.exit(1)
    
    return create_client(url, key)


def ensure_bucket(supabase, bucket_name):
    """Create the storage bucket if it doesn't exist."""
    try:
        supabase.storage.get_bucket(bucket_name)
        print(f"  Bucket '{bucket_name}' already exists.")
    except Exception:
        try:
            supabase.storage.create_bucket(
                bucket_name,
                options={"public": True}
            )
            print(f"  Created bucket '{bucket_name}' (public).")
        except Exception as e:
            # Bucket might already exist with different case
            print(f"  Bucket creation note: {e}")


def upload_image(supabase, bucket_name, local_path, storage_path):
    """Upload a single image to Supabase Storage.
    
    Args:
        supabase: Supabase client
        bucket_name: Storage bucket name
        local_path: Local file path
        storage_path: Path within the bucket (e.g. 'industrial/1.png')
        
    Returns:
        Public URL of the uploaded image
    """
    # Read file
    with open(local_path, "rb") as f:
        file_data = f.read()
    
    # Determine content type
    ext = Path(local_path).suffix.lower()
    content_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    content_type = content_types.get(ext, "image/png")
    
    try:
        # Try to upload (will fail if file exists)
        supabase.storage.from_(bucket_name).upload(
            storage_path,
            file_data,
            file_options={"content-type": content_type}
        )
    except Exception as e:
        if "Duplicate" in str(e) or "already exists" in str(e):
            # File already uploaded, skip
            pass
        else:
            # Try upsert
            try:
                supabase.storage.from_(bucket_name).update(
                    storage_path,
                    file_data,
                    file_options={"content-type": content_type}
                )
            except Exception as e2:
                print(f"    WARNING: Could not upload {storage_path}: {e2}")
                return None
    
    # Get public URL
    url = supabase.storage.from_(bucket_name).get_public_url(storage_path)
    return url


def upload_all_images(image_entries, bucket_name="reference-images"):
    """Upload all images to Supabase Storage.
    
    Args:
        image_entries: List of dicts with keys: id, image_path, style_folder
        bucket_name: Supabase Storage bucket name
        
    Returns:
        dict mapping image_id -> {storage_path, public_url}
    """
    supabase = get_supabase_client()
    ensure_bucket(supabase, bucket_name)
    
    results = {}
    total = len(image_entries)
    
    for i, entry in enumerate(image_entries):
        img_id = entry["id"]
        filename = os.path.basename(entry["image_path"])
        style_folder = entry.get("style_folder", "unknown")
        storage_path = f"{style_folder}/{filename}"
        
        print(f"  [{i+1}/{total}] Uploading {storage_path}...", end="", flush=True)
        
        url = upload_image(supabase, bucket_name, entry["image_path"], storage_path)
        
        if url:
            results[img_id] = {
                "storage_path": storage_path,
                "public_url": url,
            }
            print(" OK")
        else:
            print(" FAILED")
    
    return results
