"""
Database migration runner.
Executes SQL migration files in order against the Supabase Postgres database.
Tracks applied migrations in a _migrations table for idempotency.

Usage:
    python database/migrate.py          # Apply all pending migrations
    python database/migrate.py --reset  # Drop all tables and re-apply (DESTRUCTIVE)
"""

import os
import sys
import re
import glob
import argparse
from urllib.parse import quote_plus
import psycopg2
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations")
# Supabase-hosted DDL + catalog fixes (style_tags, room_type, RLS, RPC) live here.
SUPABASE_MIGRATIONS_DIR = os.path.join(PROJECT_ROOT, "supabase", "migrations")


def fix_database_url(url):
    """URL-encode the password in a database URL to handle special characters."""
    # Split: postgresql://user:password@host:port/db
    # Password may contain @, [, ] etc. so we split on the LAST @
    proto_end = url.find('://') + 3
    first_colon = url.index(':', proto_end)
    last_at = url.rindex('@')
    user_prefix = url[:first_colon]       # postgresql://postgres
    password = url[first_colon + 1:last_at]  # raw password
    host_suffix = url[last_at + 1:]       # host:port/db
    return f"{user_prefix}:{quote_plus(password)}@{host_suffix}"


def get_connection():
    """Create a database connection from DATABASE_URL env var."""
    import socket
    # Force IPv4 — Supabase IPv6 times out on some networks
    _orig_getaddrinfo = socket.getaddrinfo
    def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    socket.getaddrinfo = _ipv4_getaddrinfo

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)


def ensure_migrations_table(conn):
    """Create the _migrations tracking table if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id SERIAL PRIMARY KEY,
                filename TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMPTZ DEFAULT now()
            );
        """)


def get_applied_migrations(conn):
    """Return set of already-applied migration filenames."""
    with conn.cursor() as cur:
        cur.execute("SELECT filename FROM _migrations ORDER BY filename;")
        return {row[0] for row in cur.fetchall()}


def get_migration_files():
    """Return sorted list of migration SQL files (database/migrations then supabase/migrations)."""
    files = []
    for d in (MIGRATIONS_DIR, SUPABASE_MIGRATIONS_DIR):
        if os.path.isdir(d):
            files.extend(glob.glob(os.path.join(d, "*.sql")))
    # Sort by basename so 001…004 run before 009…015
    return sorted(files, key=lambda p: os.path.basename(p))


def apply_migration(conn, filepath):
    """Execute a single migration file."""
    filename = os.path.basename(filepath)
    print(f"  Applying: {filename} ... ", end="")

    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "INSERT INTO _migrations (filename) VALUES (%s) ON CONFLICT DO NOTHING;",
                (filename,),
            )
        print("OK")
    except Exception as e:
        print(f"FAILED\n  Error: {e}")
        raise


def reset_database(conn):
    """Drop all project tables (DESTRUCTIVE). Used for development only."""
    print("\n[!] RESETTING DATABASE -- dropping all project tables...")
    tables = [
        "events",
        "generations",
        "reference_images",
        "users",
        "_migrations",
    ]
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            print(f"  Dropped: {table}")
    print("  Reset complete.\n")


def main():
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables and re-apply migrations (DESTRUCTIVE)",
    )
    args = parser.parse_args()

    print("\n[DB] Database Migration Runner")
    print("=" * 40)

    conn = get_connection()
    print(f"  Connected to database.\n")

    if args.reset:
        confirm = input("  Type 'yes' to confirm database reset: ")
        if confirm.strip().lower() != "yes":
            print("  Aborted.")
            sys.exit(0)
        reset_database(conn)

    ensure_migrations_table(conn)
    applied = get_applied_migrations(conn)
    migration_files = get_migration_files()

    if not migration_files:
        print("  No migration files found.")
        conn.close()
        return

    pending = [f for f in migration_files if os.path.basename(f) not in applied]

    if not pending:
        print("  All migrations already applied. Nothing to do.")
    else:
        print(f"  Found {len(pending)} pending migration(s):\n")
        for filepath in pending:
            apply_migration(conn, filepath)
        print(f"\n  [OK] {len(pending)} migration(s) applied successfully.")

    # Summary
    applied_now = get_applied_migrations(conn)
    print(f"\n  Total applied migrations: {len(applied_now)}")
    for name in sorted(applied_now):
        print(f"    - {name}")

    conn.close()
    print("\nDone.\n")


if __name__ == "__main__":
    main()
