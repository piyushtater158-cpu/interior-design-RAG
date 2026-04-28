#!/usr/bin/env python3
"""
Seed multimodal embeddings (image + caption fused) for all reference_images.
Uses nvidia/llama-nemotron-embed-vl-1b-v2:free via OpenRouter.

Input format: ["<caption>\n<data_uri>"]  — Format B, confirmed by probe_multimodal.py.
Each call returns a single 2048-dim vector combining both visual and text signal.

Overwrites any existing row with embedding_type='nemotron-vl-1b-v2', so re-running
is safe and idempotent.

Usage (from project root):
    python n8n/seed_embeddings.py
"""

import base64
import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

CAPTIONS_DIR = Path(__file__).parent.parent / "Interior design samples"

# ── Load .env ─────────────────────────────────────────────────────────────────

def _load_env() -> dict:
    env_path = Path(__file__).parent.parent / ".env"
    file_env: dict = {}
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                file_env[k.strip()] = v.strip()

    def get(key: str, default: str = "") -> str:
        return os.environ.get(key) or file_env.get(key) or default

    return {
        "SUPABASE_URL":           get("SUPABASE_URL"),
        "SUPABASE_SERVICE_KEY":   get("SUPABASE_SERVICE_KEY"),
        "OPENROUTER_API_KEY":     get("OPENROUTER_API_KEY"),
        "OPENROUTER_BASE_URL":    get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        "OPENROUTER_EMBED_MODEL": get("OPENROUTER_EMBED_MODEL",
                                      "nvidia/llama-nemotron-embed-vl-1b-v2:free"),
    }

ENV = _load_env()

SUPA_URL = ENV["SUPABASE_URL"].rstrip("/")
SUPA_KEY = ENV["SUPABASE_SERVICE_KEY"]
OR_KEY   = ENV["OPENROUTER_API_KEY"]
OR_BASE  = ENV["OPENROUTER_BASE_URL"].rstrip("/")
MODEL    = ENV["OPENROUTER_EMBED_MODEL"]

EMBED_TYPE = "nemotron-vl-1b-v2"

# ── HTTP helpers ───────────────────────────────────────────────────────────────

def supa_headers() -> dict:
    return {
        "apikey": SUPA_KEY,
        "Authorization": f"Bearer {SUPA_KEY}",
        "Content-Type": "application/json",
    }

def http_get(url: str, headers: dict = None, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def http_post(url: str, body: dict, headers: dict, timeout: int = 60) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_err = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body_err[:400]}") from e

def http_delete(url: str, headers: dict, timeout: int = 15) -> None:
    req = urllib.request.Request(url, headers=headers, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        body_err = e.read().decode(errors="replace")
        raise RuntimeError(f"DELETE HTTP {e.code}: {body_err[:400]}") from e

# ── Data helpers ───────────────────────────────────────────────────────────────

def fetch_reference_images() -> list:
    url = (f"{SUPA_URL}/rest/v1/reference_images"
           f"?select=id,source_url,source_id,caption&order=created_at.asc&limit=1000")
    raw = http_get(url, headers=supa_headers())
    rows = json.loads(raw)
    if not isinstance(rows, list):
        raise RuntimeError(f"Unexpected response: {str(raw)[:200]}")
    return rows

def load_caption(source_id: str, db_caption: str) -> str:
    """Read caption from local .txt file; fall back to the DB caption column."""
    txt_file = CAPTIONS_DIR / f"{source_id}.txt"
    if txt_file.exists():
        return txt_file.read_text(encoding="utf-8").strip()
    if db_caption:
        return db_caption.strip()
    raise ValueError(f"No caption for source_id={source_id!r}")

def image_to_data_uri(source_url: str) -> str:
    raw = http_get(source_url, timeout=30)
    if raw[:3] == b"\xff\xd8\xff":
        mime = "image/jpeg"
    elif raw[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "image/png"
    elif raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        mime = "image/jpeg"
    b64 = base64.b64encode(raw).decode()
    return f"data:{mime};base64,{b64}"

# ── Embedding ──────────────────────────────────────────────────────────────────

def embed_multimodal(data_uri: str, caption: str) -> list:
    """Single OpenRouter call → 2048-dim fused image+text vector (Format B)."""
    url = f"{OR_BASE}/embeddings"
    body = {
        "model": MODEL,
        "input": [f"{caption}\n{data_uri}"],
        "encoding_format": "float",
    }
    headers = {
        "Authorization": f"Bearer {OR_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://interior-design-rag.local",
        "X-Title": "Interior Design RAG seed",
    }
    resp = http_post(url, body, headers, timeout=90)
    data = resp.get("data", [])
    if not data or "embedding" not in data[0]:
        raise RuntimeError(f"No embedding in response: {str(resp)[:400]}")
    return data[0]["embedding"]

# ── Database ───────────────────────────────────────────────────────────────────

def delete_existing_embedding(ref_id: str) -> None:
    url = (f"{SUPA_URL}/rest/v1/reference_embeddings"
           f"?reference_image_id=eq.{ref_id}&embedding_type=eq.{EMBED_TYPE}")
    http_delete(url, headers=supa_headers())

def insert_embedding(ref_id: str, vec: list) -> None:
    vec_literal = "[" + ",".join(str(float(x)) for x in vec) + "]"
    url = f"{SUPA_URL}/rest/v1/reference_embeddings"
    headers = {**supa_headers(), "Prefer": "return=minimal"}
    body = {
        "reference_image_id": ref_id,
        "embedding_type": EMBED_TYPE,
        "embedding": vec_literal,
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        body_err = e.read().decode(errors="replace")
        raise RuntimeError(f"Insert HTTP {e.code}: {body_err[:400]}") from e

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("Fetching reference_images …")
    images = fetch_reference_images()
    print(f"  Found {len(images)} reference images\n")

    ok = 0
    skipped = 0

    for i, row in enumerate(images, 1):
        ref_id     = row["id"]
        source_url = row["source_url"]
        source_id  = row.get("source_id") or str(i)
        db_caption = row.get("caption") or ""

        try:
            caption = load_caption(source_id, db_caption)
        except ValueError as e:
            print(f"[{i:3d}/{len(images)}] SKIP (no caption): {e}")
            skipped += 1
            continue

        caption_preview = caption[:70] + ("..." if len(caption) > 70 else "")
        print(f"[{i:3d}/{len(images)}] {source_url.split('/')[-1]}  caption: {caption_preview}")

        try:
            data_uri = image_to_data_uri(source_url)
            vec      = embed_multimodal(data_uri, caption)
            delete_existing_embedding(ref_id)
            insert_embedding(ref_id, vec)
            print(f"             OK  {len(vec)}-dim fused vector stored")
            ok += 1
        except Exception as e:
            print(f"             FAIL  {e}")
            skipped += 1

        if i < len(images):
            time.sleep(0.5)

    print(f"\nDone: {ok} inserted, {skipped} skipped, {ok + skipped} total")

if __name__ == "__main__":
    main()
