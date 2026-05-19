"""
Minimal Supabase REST + Storage client (requests only).
Used when the supabase Python package is unavailable.
"""

import os
from typing import Any

import requests
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def _base_url() -> str:
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    if not url:
        raise RuntimeError("SUPABASE_URL not set in .env")
    return url


def _service_key() -> str:
    key = os.getenv("SUPABASE_SERVICE_KEY") or ""
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_KEY not set in .env")
    return key


def _headers(extra: dict | None = None) -> dict[str, str]:
    h = {
        "apikey": _service_key(),
        "Authorization": f"Bearer {_service_key()}",
    }
    if extra:
        h.update(extra)
    return h


def ensure_bucket_public(bucket_name: str) -> None:
    """Create bucket if missing (public read)."""
    url = f"{_base_url()}/storage/v1/bucket"
    r = requests.post(
        url,
        headers={**_headers(), "Content-Type": "application/json"},
        json={"id": bucket_name, "name": bucket_name, "public": True},
        timeout=60,
    )
    if r.status_code in (200, 201):
        return
    if r.status_code == 409 or "already exists" in (r.text or "").lower():
        return
    # Bucket may exist but POST failed for another reason — try GET
    gr = requests.get(f"{url}/{bucket_name}", headers=_headers(), timeout=30)
    if gr.status_code == 200:
        return
    r.raise_for_status()


def upload_object(bucket: str, storage_path: str, data: bytes, content_type: str) -> None:
    path = storage_path.lstrip("/")
    url = f"{_base_url()}/storage/v1/object/{bucket}/{path}"
    r = requests.post(
        url,
        headers={
            **_headers(),
            "Content-Type": content_type,
            "x-upsert": "true",
        },
        data=data,
        timeout=120,
    )
    if r.status_code not in (200, 201):
        r.raise_for_status()


def public_url(bucket: str, storage_path: str) -> str:
    path = storage_path.lstrip("/")
    return f"{_base_url()}/storage/v1/object/public/{bucket}/{path}"


def upsert_reference_image(row: dict[str, Any]) -> str:
    """Upsert reference_images on (owner_id, source, source_id). Returns row id."""
    url = f"{_base_url()}/rest/v1/reference_images"
    r = requests.post(
        url,
        headers={
            **_headers(),
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation",
        },
        params={"on_conflict": "owner_id,source,source_id"},
        json=row,
        timeout=60,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"reference_images upsert failed ({r.status_code}): {r.text}")
    data = r.json()
    if isinstance(data, list) and data:
        return data[0]["id"]
    if isinstance(data, dict):
        return data["id"]
    raise RuntimeError(f"Unexpected upsert response: {data!r}")


def count_reference_images() -> int:
    url = f"{_base_url()}/rest/v1/reference_images"
    r = requests.get(
        url,
        headers={**_headers(), "Prefer": "count=exact"},
        params={"select": "id"},
        timeout=30,
    )
    r.raise_for_status()
    cr = r.headers.get("Content-Range") or r.headers.get("content-range") or ""
    # e.g. 0-9/104
    if "/" in cr:
        return int(cr.split("/")[-1])
    return len(r.json() or [])


def first_auth_user_id() -> str | None:
    """Return first auth user id (service role)."""
    url = f"{_base_url()}/auth/v1/admin/users"
    r = requests.get(url, headers=_headers(), params={"per_page": 1}, timeout=30)
    if r.status_code != 200:
        return None
    payload = r.json()
    users = payload.get("users") if isinstance(payload, dict) else payload
    if not users:
        return None
    return users[0].get("id")
