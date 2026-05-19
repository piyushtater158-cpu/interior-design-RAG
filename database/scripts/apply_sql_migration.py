"""
Apply a single SQL migration file to Supabase Postgres.

Tries DATABASE_URL first, then direct db.<project-ref>.supabase.co:5432.

Usage:
  python database/scripts/apply_sql_migration.py n8n/migrations/016_reference_images_catalog_rls.sql
"""

import os
import sys
import socket
from urllib.parse import urlparse, quote_plus

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(ROOT, ".env"))


def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return socket.getaddrinfo(host, port, socket.AF_INET, type, proto, flags)


def _parse_database_url(url: str):
    p = urlparse(url)
    return {
        "host": p.hostname,
        "port": p.port or 5432,
        "user": p.username,
        "password": p.password,
        "dbname": (p.path or "/postgres").lstrip("/") or "postgres",
    }


def _connect(params: dict):
    import psycopg2

    return psycopg2.connect(
        host=params["host"],
        port=params["port"],
        user=params["user"],
        password=params["password"],
        dbname=params["dbname"],
        connect_timeout=30,
    )


def _apply_via_management_api(sql: str, project_ref: str, access_token: str) -> bool:
    import requests

    url = f"https://api.supabase.com/v1/projects/{project_ref}/database/query"
    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"query": sql},
        timeout=120,
    )
    if r.status_code not in (200, 201):
        print(f"[apply] Management API failed ({r.status_code}): {r.text[:500]}")
        return False
    print("[apply] Applied via Supabase Management API.")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: apply_sql_migration.py <path-to.sql>")
        sys.exit(1)

    sql_path = sys.argv[1]
    if not os.path.isabs(sql_path):
        sql_path = os.path.join(ROOT, sql_path)
    if not os.path.isfile(sql_path):
        print(f"ERROR: file not found: {sql_path}")
        sys.exit(1)

    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    supabase_url = os.getenv("SUPABASE_URL", "")
    project_ref = supabase_url.split("//", 1)[-1].split(".")[0] if supabase_url else ""
    access_token = os.getenv("SUPABASE_ACCESS_TOKEN", "").strip()
    if access_token and project_ref:
        if _apply_via_management_api(sql, project_ref, access_token):
            return

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    from database.migrate import fix_database_url

    base = _parse_database_url(fix_database_url(database_url))
    supabase_url = os.getenv("SUPABASE_URL", "")
    ref = ""
    if "supabase.co" in supabase_url:
        ref = supabase_url.split("//", 1)[-1].split(".")[0]

    pooler_host = base.get("host") or ""
    if pooler_host and "pooler.supabase.com" in pooler_host:
        # Session pooler: postgres.<ref> @ :5432; transaction pooler: postgres @ :6543
        candidates = [
            {**base, "user": f"postgres.{ref}", "port": 5432},
            {**base, "user": "postgres", "port": 6543},
            base,
            {**base, "host": f"db.{ref}.supabase.co", "port": 5432, "user": "postgres"},
        ]
    else:
        candidates = [
            base,
            {**base, "host": f"db.{ref}.supabase.co", "port": 5432, "user": "postgres"},
            {**base, "host": f"db.{ref}.supabase.co", "port": 5432, "user": f"postgres.{ref}"},
            {**base, "user": f"postgres.{ref}", "port": 5432},
        ]

    socket.getaddrinfo = _ipv4_getaddrinfo
    last_err = None
    conn = None
    for i, params in enumerate(candidates):
        try:
            print(f"[apply] Connecting ({i + 1}/{len(candidates)}) {params['user']}@{params['host']}:{params['port']} ...")
            conn = _connect(params)
            print("[apply] Connected.")
            break
        except Exception as e:
            last_err = e
            print(f"[apply] Failed: {e}")

    if conn is None:
        print(f"ERROR: Could not connect: {last_err}")
        sys.exit(1)

    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            print(f"[apply] Executing {sql_path} ...")
            cur.execute(sql)
        print("[apply] Done.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
