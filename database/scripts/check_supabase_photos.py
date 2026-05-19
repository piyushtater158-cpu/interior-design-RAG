"""Check reference_images rows and whether storage URLs are reachable."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, ".env"))

base = os.getenv("SUPABASE_URL", "").rstrip("/")
key = os.getenv("SUPABASE_SERVICE_KEY", "")
if not base or not key:
    print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY missing in .env")
    sys.exit(1)

h = {"apikey": key, "Authorization": f"Bearer {key}"}


def count_rows(**filters):
    params = {"select": "id", "limit": 1, **filters}
    r = requests.get(
        f"{base}/rest/v1/reference_images",
        headers={**h, "Prefer": "count=exact"},
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    return r.headers.get("content-range", "?")


def main():
    print(f"Project: {base}\n")
    print("reference_images total:", count_rows())
    for src in ("local", "studio"):
        print(f"  source={src}:", count_rows(source=f"eq.{src}"))

    r = requests.get(
        f"{base}/rest/v1/reference_images",
        headers=h,
        params={
            "select": "id,source,source_url,storage_path,room_type,style_tags,created_at",
            "order": "created_at.desc",
            "limit": 8,
        },
        timeout=30,
    )
    r.raise_for_status()
    rows = r.json()
    print(f"\nLatest {len(rows)} rows:")
    for row in rows:
        sp = (row.get("storage_path") or "")[:55]
        print(
            f"  [{row.get('source')}] {row.get('room_type')} "
            f"{row.get('style_tags')} | {sp}"
        )

    if rows:
        url = rows[0].get("source_url") or ""
        pub = url.replace(
            "/object/reference-images/", "/object/public/reference-images/"
        )
        for label, u in [("source_url (DB)", url), ("public variant", pub)]:
            if not u:
                continue
            resp = requests.head(u, timeout=20)
            ct = resp.headers.get("content-type", "")
            print(f"\n{label}: HTTP {resp.status_code} {ct}")
            print(f"  {u}")

    lst = requests.post(
        f"{base}/storage/v1/object/list/reference-images",
        headers={**h, "Content-Type": "application/json"},
        json={"prefix": "", "limit": 10, "offset": 0},
        timeout=30,
    )
    print(f"\nStorage bucket list (status {lst.status_code}):")
    if lst.ok:
        items = lst.json() or []
        for obj in items[:10]:
            if isinstance(obj, dict):
                print(f"  {obj.get('name', obj)}")
            else:
                print(f"  {obj}")
    else:
        print(" ", lst.text[:400])


if __name__ == "__main__":
    main()
