#!/usr/bin/env python3
"""
reset_database.py — Nuke the public schema and rebuild from migration 100.

Usage:
  python scripts/reset_database.py --confirm

Requires env vars:
  SUPABASE_URL            e.g. https://uzghfpxboktnbcbbthns.supabase.co
  SUPABASE_SERVICE_KEY    service-role JWT
  SUPABASE_ADMIN_KEY      (same as service key for Supabase projects)

DESTRUCTIVE: drops every table in public.*, clears auth.users, then applies
100_reset_and_rebuild.sql. Run only in development; there is no undo.
"""

import os
import sys
import pathlib
import urllib.request
import urllib.error
import json

ROOT = pathlib.Path(__file__).parent.parent

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://uzghfpxboktnbcbbthns.supabase.co")
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def http(method: str, path: str, body: dict | None = None) -> dict:
    url = SUPABASE_URL.rstrip("/") + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("apikey", SERVICE_KEY)
    req.add_header("Authorization", f"Bearer {SERVICE_KEY}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body_raw = e.read().decode(errors="replace")
        die(f"HTTP {e.code} on {method} {path}: {body_raw}")


def run_sql(sql: str) -> None:
    """Execute SQL via Supabase's postgres REST endpoint (service role)."""
    result = http("POST", "/rest/v1/rpc/exec_sql", {"query": sql})
    # exec_sql RPC may not exist — use pg_meta or psql instead for actual use
    return result


def main() -> None:
    if "--confirm" not in sys.argv:
        print(__doc__)
        die("Pass --confirm to actually run. This is irreversible.")

    if not SERVICE_KEY:
        die("SUPABASE_SERVICE_KEY not set.")

    migration = ROOT / "supabase" / "migrations" / "100_reset_and_rebuild.sql"
    if not migration.exists():
        die(f"Migration not found: {migration}")

    print("=" * 60)
    print("RESET DATABASE — all data will be lost")
    print(f"Target: {SUPABASE_URL}")
    print("=" * 60)

    # Step 1: Clear auth.users via Supabase admin API
    # NOTE: the admin API endpoint for listing users is paginated.
    # For a dev reset the simplest approach is psql or the Supabase dashboard.
    # This script prints the SQL you should run via Supabase MCP or psql.
    print("""
Steps to complete (run via Supabase SQL editor / psql / MCP apply_migration):

  1. In Supabase dashboard → Authentication → Users: delete all users.
     OR via SQL:
       delete from auth.users;  -- cascades to public.users

  2. Drop and recreate public schema:
       drop schema public cascade;
       create schema public;
       grant usage on schema public to postgres, anon, authenticated, service_role;
       grant all on all tables in schema public to postgres, service_role;
       grant all on all sequences in schema public to postgres, service_role;
       alter default privileges in schema public
         grant all on tables to postgres, service_role;
       alter default privileges in schema public
         grant all on sequences to postgres, service_role;

  3. Apply migration 100:
       -- paste contents of supabase/migrations/100_reset_and_rebuild.sql
       -- or use: supabase db push (if using Supabase CLI)
       -- or use: MCP apply_migration tool

  4. Verify:
       select count(*) from public.reference_images;  -- 0
       \\df retrieve_candidates_text                   -- 0 rows (RPC dropped)
       \\d public.reference_images                     -- no caption_fts column
""")

    migration_sql = migration.read_text(encoding="utf-8")
    print(f"Migration file ready ({len(migration_sql)} chars): {migration}")
    print("\nRun the steps above, then import n8n workflows and configure named credentials.")


if __name__ == "__main__":
    main()
