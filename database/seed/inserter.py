"""
Database inserter.
Takes tagged, embedded, uploaded image data and inserts into Postgres.
"""

import os
import sys
import uuid
import json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.db import get_connection


def insert_demo_user(conn):
    """Insert a demo user if not exists. Returns user_id."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO users (email, is_demo)
            VALUES ('demo@interiordesign.ai', true)
            ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
            RETURNING id;
        """)
        user_id = cur.fetchone()[0]
        print(f"  Demo user: {user_id}")
        return user_id


def insert_reference_image(conn, image_data):
    """Insert a single reference image row.
    
    Args:
        conn: psycopg2 connection
        image_data: dict with keys:
            source, source_id, source_url, license, storage_path,
            caption, room_type, style_tags, dominant_colors,
            detected_objects, quality_score
    
    Returns:
        UUID of inserted/existing row
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO reference_images 
                (source, source_id, source_url, license, storage_path,
                 caption, room_type, style_tags, dominant_colors,
                 detected_objects, quality_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, source_id) DO UPDATE SET
                source_url = EXCLUDED.source_url,
                storage_path = EXCLUDED.storage_path,
                caption = EXCLUDED.caption,
                room_type = EXCLUDED.room_type,
                style_tags = EXCLUDED.style_tags,
                dominant_colors = EXCLUDED.dominant_colors,
                detected_objects = EXCLUDED.detected_objects,
                quality_score = EXCLUDED.quality_score
            RETURNING id;
        """, (
            image_data["source"],
            image_data["source_id"],
            image_data["source_url"],
            image_data["license"],
            image_data["storage_path"],
            image_data.get("caption", ""),
            image_data["room_type"],
            image_data["style_tags"],
            image_data.get("dominant_colors", []),
            image_data.get("detected_objects", []),
            image_data.get("quality_score", 0.5),
        ))
        return cur.fetchone()[0]


def insert_reference_embedding(conn, image_id, embedding, embedding_type="clip-vit-b32"):
    """Insert a CLIP embedding for a reference image.
    
    Args:
        conn: psycopg2 connection
        image_id: UUID of the reference_images row
        embedding: numpy array of shape (512,)
        embedding_type: string identifier for the model
    """
    # Convert numpy to list for psycopg2
    embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
    embedding_str = "[" + ",".join(str(x) for x in embedding_list) + "]"
    
    with conn.cursor() as cur:
        # Delete existing embedding for this image (upsert)
        cur.execute("""
            DELETE FROM reference_embeddings 
            WHERE reference_image_id = %s AND embedding_type = %s;
        """, (image_id, embedding_type))
        
        cur.execute("""
            INSERT INTO reference_embeddings (reference_image_id, embedding_type, embedding)
            VALUES (%s, %s, %s::vector);
        """, (image_id, embedding_type, embedding_str))


def insert_all(image_entries, tags, upload_results, embeddings=None):
    """Insert all data into the database.
    
    Args:
        image_entries: List of dicts with id, image_path, caption, style_folder
        tags: dict mapping image_id -> tagger result
        upload_results: dict mapping image_id -> {storage_path, public_url}
        embeddings: dict mapping image_id -> numpy array (optional, inserted if available)
        
    Returns:
        dict with insertion statistics
    """
    conn = get_connection(autocommit=True)
    
    # Insert demo user
    demo_user_id = insert_demo_user(conn)
    
    stats = {
        "images_inserted": 0,
        "images_skipped": 0,
        "embeddings_inserted": 0,
    }
    
    total = len(image_entries)
    
    for i, entry in enumerate(image_entries):
        img_id = entry["id"]
        tag = tags.get(img_id, {})
        upload = upload_results.get(img_id, {})
        
        if not upload:
            print(f"  [{i+1}/{total}] Image {img_id}: SKIPPED (no upload URL)")
            stats["images_skipped"] += 1
            continue
        
        image_data = {
            "source": "local",
            "source_id": str(img_id),
            "source_url": upload.get("public_url", ""),
            "license": "owned",
            "storage_path": upload.get("storage_path", ""),
            "caption": entry.get("caption", ""),
            "room_type": tag.get("room_type", "unknown"),
            "style_tags": tag.get("style_tags", [entry.get("style_folder", "unknown")]),
            "dominant_colors": tag.get("dominant_colors", []),
            "detected_objects": tag.get("detected_objects", []),
            "quality_score": tag.get("quality_score", 0.5),
        }
        
        print(f"  [{i+1}/{total}] Inserting image {img_id} ({image_data['room_type']})...", end="", flush=True)
        
        try:
            row_id = insert_reference_image(conn, image_data)
            stats["images_inserted"] += 1
            print(f" -> {row_id}", end="")
            
            # Insert embedding if available
            if embeddings and img_id in embeddings:
                insert_reference_embedding(conn, row_id, embeddings[img_id])
                stats["embeddings_inserted"] += 1
                print(" + embedding", end="")
            
            print()
        except Exception as e:
            print(f" FAILED: {e}")
            stats["images_skipped"] += 1
    
    conn.close()
    return stats
