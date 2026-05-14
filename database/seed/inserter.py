"""
Database inserter.
Takes tagged, uploaded image data and inserts into Postgres.

Requires env var:
  SEED_OWNER_USER_ID  UUID of the auth.users row that will own the seeded rows.
                      Must exist in auth.users before running the seed.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.db import get_connection
from database.seed.canonical_room_type import pick_canonical_room_type
from database.seed.canonical_style_tags import pick_canonical_style_tags_singleton


def get_seed_owner_id() -> str:
    owner_id = os.environ.get("SEED_OWNER_USER_ID", "").strip()
    if not owner_id:
        raise RuntimeError(
            "SEED_OWNER_USER_ID env var is required.\n"
            "Set it to the UUID of the auth.users row that should own the seeded reference images.\n"
            "Example: export SEED_OWNER_USER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        )
    return owner_id


def insert_reference_image(conn, image_data: dict) -> str:
    """Insert a single reference image row owned by SEED_OWNER_USER_ID.

    image_data keys required:
        owner_id, source, source_id, source_url, license, storage_path,
        room_type, style_tags
    optional:
        caption, spatial_signature, dominant_colors, detected_objects, quality_score

    Returns: UUID of the inserted/updated row.
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO reference_images
                (owner_id, source, source_id, source_url, license, storage_path,
                 caption, spatial_signature, room_type, style_tags,
                 dominant_colors, detected_objects, quality_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (owner_id, source, source_id) DO UPDATE SET
                source_url        = EXCLUDED.source_url,
                storage_path      = EXCLUDED.storage_path,
                caption           = EXCLUDED.caption,
                spatial_signature = EXCLUDED.spatial_signature,
                room_type         = EXCLUDED.room_type,
                style_tags        = EXCLUDED.style_tags,
                dominant_colors   = EXCLUDED.dominant_colors,
                detected_objects  = EXCLUDED.detected_objects,
                quality_score     = EXCLUDED.quality_score
            RETURNING id;
        """, (
            image_data["owner_id"],
            image_data["source"],
            image_data["source_id"],
            image_data["source_url"],
            image_data["license"],
            image_data["storage_path"],
            image_data.get("caption"),
            image_data.get("spatial_signature"),
            image_data["room_type"],
            image_data["style_tags"],
            image_data.get("dominant_colors", []),
            image_data.get("detected_objects", []),
            image_data.get("quality_score"),
        ))
        return cur.fetchone()[0]


def insert_all(image_entries, tags, upload_results):
    """Insert all data into the database.

    Args:
        image_entries: List of dicts with id, image_path, caption, style_folder
        tags: dict mapping image_id -> tagger result
        upload_results: dict mapping image_id -> {storage_path, public_url}

    Returns:
        dict with insertion statistics
    """
    owner_id = get_seed_owner_id()
    print(f"  Seed owner: {owner_id}")

    conn = get_connection(autocommit=True)

    stats = {"images_inserted": 0, "images_skipped": 0}
    total = len(image_entries)

    for i, entry in enumerate(image_entries):
        img_id = entry["id"]
        tag    = tags.get(img_id, {})
        upload = upload_results.get(img_id, {})

        if not upload:
            print(f"  [{i+1}/{total}] {img_id}: SKIPPED (no upload result)")
            stats["images_skipped"] += 1
            continue

        raw_tags = tag.get("style_tags", [entry.get("style_folder", "unknown")])
        if not isinstance(raw_tags, list):
            raw_tags = [str(raw_tags)]

        image_data = {
            "owner_id":    owner_id,
            "source":      "local",
            "source_id":   str(img_id),
            "source_url":  upload.get("public_url", ""),
            "license":     "owned",
            "storage_path": upload.get("storage_path", ""),
            "caption":     entry.get("caption"),
            "spatial_signature": tag.get("spatial_signature"),
            "room_type":   pick_canonical_room_type(
                entry.get("caption", ""),
                tag.get("room_type", "unknown"),
                tag.get("detected_objects") or [],
            ),
            "style_tags":  pick_canonical_style_tags_singleton(
                entry.get("caption", ""), raw_tags
            ),
            "dominant_colors":  tag.get("dominant_colors", []),
            "detected_objects": tag.get("detected_objects", []),
            "quality_score":    tag.get("quality_score"),
        }

        print(f"  [{i+1}/{total}] {img_id} ({image_data['room_type']})...", end="", flush=True)
        try:
            row_id = insert_reference_image(conn, image_data)
            stats["images_inserted"] += 1
            print(f" -> {row_id}")
        except Exception as e:
            print(f" FAILED: {e}")
            stats["images_skipped"] += 1

    conn.close()
    return stats
