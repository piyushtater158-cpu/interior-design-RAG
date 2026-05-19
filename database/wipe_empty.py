"""
Wipe Postgres public schema and app storage rows (DESTRUCTIVE).

Requires DATABASE_URL in .env (project root). Prefer direct DB port 5432 if
DROP SCHEMA fails through the pooler (6543).

Usage:
  python database/wipe_empty.py --yes
"""

import os
import sys
import argparse
import socket

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import importlib.util

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def _load_migrate():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrate.py")
    spec = importlib.util.spec_from_file_location("db_migrate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm wipe without interactive prompt",
    )
    args = parser.parse_args()

    if not args.yes:
        print("Refusing to run without --yes (destructive).")
        sys.exit(1)

    sql_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "scripts",
        "wipe_public_schema.sql",
    )
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    migrate = _load_migrate()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    database_url = migrate.fix_database_url(database_url)

    _orig_getaddrinfo = socket.getaddrinfo

    def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

    socket.getaddrinfo = _ipv4_getaddrinfo

    import psycopg2

    print("[wipe] Connecting...")
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            print("[wipe] Executing wipe_public_schema.sql ...")
            cur.execute(sql)
        print("[wipe] Done. public schema is empty; app buckets/policies removed from storage catalog.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
