"""
Shared database connection utility.
Handles IPv4 forcing and URL-encoded passwords for Supabase.
"""

import os
import sys
import re
import socket
from urllib.parse import quote_plus
import psycopg2
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Force IPv4 globally — Supabase IPv6 times out on some networks
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _ipv4_getaddrinfo


def get_connection(autocommit=True):
    """Create a database connection from DATABASE_URL env var."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = autocommit
        return conn
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)
