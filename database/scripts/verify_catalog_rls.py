"""Check reference_images visibility: anon (expect 0) vs service role (full catalog)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, ".env"))

ANON = os.getenv("SUPABASE_ANON_KEY", "")


def count(key: str) -> str:
    base = os.getenv("SUPABASE_URL", "").rstrip("/")
    r = requests.get(
        f"{base}/rest/v1/reference_images",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Prefer": "count=exact",
        },
        params={"select": "id", "limit": 1},
        timeout=30,
    )
    r.raise_for_status()
    return r.headers.get("content-range", "?")


def main():
    if not ANON:
        print("ERROR: SUPABASE_ANON_KEY missing")
        sys.exit(1)
    svc = os.getenv("SUPABASE_SERVICE_KEY", "")
    if not svc:
        print("ERROR: SUPABASE_SERVICE_KEY missing")
        sys.exit(1)
    anon_cr = count(ANON)
    svc_cr = count(svc)
    print("reference_images Content-Range:")
    print(f"  anon:    {anon_cr}")
    print(f"  service: {svc_cr}")
    print()
    if anon_cr.endswith("/0"):
        print("Anon blocked (expected).")
    if "/283" in svc_cr or ("/" in svc_cr and not svc_cr.endswith("/0")):
        n = svc_cr.split("/")[-1]
        print(f"Service sees {n} rows.")
    print()
    print("After migration 016, sign in on mobile-app and Profile → Database should list styles.")
    print("Apply SQL: n8n/migrations/016_reference_images_catalog_rls.sql (Supabase SQL Editor).")


if __name__ == "__main__":
    main()
