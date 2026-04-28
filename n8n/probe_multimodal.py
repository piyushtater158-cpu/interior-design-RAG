#!/usr/bin/env python3
"""
Smoke-test: find which OpenRouter multimodal input format produces a single
fused image+text embedding from nvidia/llama-nemotron-embed-vl-1b-v2:free.

Usage:
    python n8n/probe_multimodal.py

Reads .env for SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENROUTER_API_KEY.
Does NOT write to the DB.
"""

import base64
import json
import math
import os
import urllib.request
import urllib.error
from pathlib import Path

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

CAPTIONS_DIR = Path(__file__).parent.parent / "Interior design samples"

# ── HTTP helpers ───────────────────────────────────────────────────────────────

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
        raise RuntimeError(f"HTTP {e.code}: {body_err[:600]}") from e

def embed_request(input_payload, timeout: int = 90) -> dict:
    url = f"{ENV['OPENROUTER_BASE_URL'].rstrip('/')}/embeddings"
    body = {"model": ENV["OPENROUTER_EMBED_MODEL"], "encoding_format": "float",
            "input": input_payload}
    headers = {
        "Authorization": f"Bearer {ENV['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://interior-design-rag.local",
        "X-Title": "Interior Design RAG probe",
    }
    return http_post(url, body, headers, timeout=timeout)

# ── Vector math ────────────────────────────────────────────────────────────────

def norm(v: list) -> float:
    return math.sqrt(sum(x * x for x in v))

def cosine(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (norm(a) * norm(b) + 1e-10)

def l2_normalize(v: list) -> list:
    n = norm(v)
    return [x / n for x in v] if n > 0 else v

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    supa_url = ENV["SUPABASE_URL"].rstrip("/")
    supa_key = ENV["SUPABASE_SERVICE_KEY"]
    if not supa_url or not supa_key:
        print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY not set in .env")
        return

    # --- Fetch source_id='1' from DB ---
    print("Fetching reference image 1 from Supabase …")
    raw = http_get(
        f"{supa_url}/rest/v1/reference_images?source_id=eq.1&select=id,source_url,caption&limit=1",
        headers={"apikey": supa_key, "Authorization": f"Bearer {supa_key}"},
    )
    rows = json.loads(raw)
    if not rows:
        print("ERROR: No row with source_id='1' found in reference_images.")
        return
    row = rows[0]
    source_url: str = row["source_url"]
    db_caption: str = row.get("caption") or ""
    print(f"  source_url : {source_url}")
    print(f"  db caption : {db_caption[:80]}")

    # --- Load caption from .txt file (prefer file, fallback DB) ---
    txt_file = CAPTIONS_DIR / "1.txt"
    if txt_file.exists():
        caption = txt_file.read_text(encoding="utf-8").strip()
        print(f"  txt caption: {caption}")
    elif db_caption:
        caption = db_caption
        print(f"  (using DB caption — txt file not found at {txt_file})")
    else:
        print("ERROR: No caption found — neither txt file nor DB row has one.")
        return

    # --- Download image → data URI ---
    print("\nDownloading image bytes …")
    img_bytes = http_get(source_url, timeout=30)
    if img_bytes[:3] == b"\xff\xd8\xff":
        mime = "image/jpeg"
    elif img_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "image/png"
    elif img_bytes[:4] == b"RIFF" and img_bytes[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        mime = "image/jpeg"
    b64 = base64.b64encode(img_bytes).decode()
    data_uri = f"data:{mime};base64,{b64}"
    print(f"  {len(img_bytes):,} bytes  ({mime})")

    # ---- Baseline: image-only and text-only ----
    print("\n── Baseline embeddings ──────────────────────────────────────────")
    print("  [baseline-img] image only …")
    try:
        r = embed_request([data_uri])
        vec_img = r["data"][0]["embedding"]
        print(f"    ✓  dim={len(vec_img)}  n_outputs={len(r['data'])}")
    except Exception as e:
        print(f"    ✗  {e}")
        vec_img = None

    print("  [baseline-txt] text only …")
    try:
        r = embed_request([caption])
        vec_txt = r["data"][0]["embedding"]
        print(f"    ✓  dim={len(vec_txt)}  n_outputs={len(r['data'])}")
    except Exception as e:
        print(f"    ✗  {e}")
        vec_txt = None

    # ---- Probe fusion formats ----
    formats = [
        ("A-object",       [{"image": data_uri, "text": caption}]),
        ("B-string",       [f"{caption}\n{data_uri}"]),
        ("C-text_first",   [caption, data_uri]),
        ("D-image_first",  [data_uri, caption]),
    ]

    results = {}
    print("\n── Fusion format probes ─────────────────────────────────────────")
    for name, payload in formats:
        print(f"  [{name}] …")
        try:
            r = embed_request(payload)
            n_out = len(r.get("data", []))
            if n_out == 0:
                print(f"    ✗  empty data array: {str(r)[:200]}")
                continue
            vec = r["data"][0]["embedding"]
            dim = len(vec)
            is_fused = (n_out == 1)
            print(f"    n_outputs={n_out}  dim={dim}  {'FUSED (single vector)' if is_fused else 'BATCH (multiple vectors)'}")

            # Compare against baselines
            if vec_img and vec_txt:
                cs_img = cosine(vec, vec_img)
                cs_txt = cosine(vec, vec_txt)
                print(f"    cosine_to_img={cs_img:.4f}  cosine_to_txt={cs_txt:.4f}")
                # A truly fused vector should differ from both unimodals
                looks_fused = is_fused and cs_img < 0.9999 and cs_txt < 0.9999
                print(f"    looks_truly_fused={'YES' if looks_fused else 'NO (identical to a baseline)'}")

            if is_fused:
                results[name] = {"vec": vec, "dim": dim}
        except Exception as e:
            print(f"    ✗  {e}")

    # ---- Report ----
    print("\n── Summary ──────────────────────────────────────────────────────")
    if results:
        winner = next(iter(results))
        print(f"  WINNER: Format '{winner}' produces a single fused vector.")
        print(f"  → Use this format in seed_embeddings.py / _seed_nemotron_references.json")
    else:
        print("  No format produced a single fused vector.")
        print("  → Fallback: average image-only + text-only vectors client-side.")
        if vec_img and vec_txt:
            v_img_n = l2_normalize(vec_img)
            v_txt_n = l2_normalize(vec_txt)
            fused = l2_normalize([a + b for a, b in zip(v_img_n, v_txt_n)])
            cs_img = cosine(fused, vec_img)
            cs_txt = cosine(fused, vec_txt)
            print(f"  Fallback fused dim={len(fused)}  cosine_to_img={cs_img:.4f}  cosine_to_txt={cs_txt:.4f}")
            print("  (This is the vector that would be stored per reference image.)")

if __name__ == "__main__":
    main()
