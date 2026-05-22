#!/usr/bin/env python3
"""Ensure allowlisted emails exist in Supabase Auth (admin API)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT / ".env")

INVITE_EMAILS = [
    "siddhant@100xengineers.com",
    "shipra@100xengineers.com",
]


def _base() -> str:
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    if not url:
        raise SystemExit("SUPABASE_URL not set in .env")
    return url


def _key() -> str:
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not key:
        raise SystemExit("SUPABASE_SERVICE_KEY (or SUPABASE_SERVICE_ROLE_KEY) not set in .env")
    return key


def _headers() -> dict[str, str]:
    k = _key()
    return {
        "apikey": k,
        "Authorization": f"Bearer {k}",
        "Content-Type": "application/json",
    }


def find_user_id(email: str) -> str | None:
    url = f"{_base()}/auth/v1/admin/users"
    page = 1
    while True:
        r = requests.get(
            url,
            headers=_headers(),
            params={"page": page, "per_page": 200},
            timeout=30,
        )
        r.raise_for_status()
        payload = r.json()
        users = payload.get("users") if isinstance(payload, dict) else payload
        if not users:
            return None
        for u in users:
            if (u.get("email") or "").lower() == email.lower():
                return u.get("id")
        if len(users) < 200:
            return None
        page += 1


def ensure_user(email: str) -> tuple[str, str]:
    existing = find_user_id(email)
    if existing:
        return existing, "already_exists"

    url = f"{_base()}/auth/v1/admin/users"
    body = {
        "email": email,
        "email_confirm": True,
        "user_metadata": {"invited": True, "source": "invite_auth_users.py"},
    }
    r = requests.post(url, headers=_headers(), json=body, timeout=30)
    if r.status_code in (200, 201):
        data = r.json()
        return data.get("id") or "?", "created"

    if r.status_code == 422:
        # duplicate or policy — recheck
        again = find_user_id(email)
        if again:
            return again, "already_exists"
    r.raise_for_status()
    return "?", "unknown"


def main() -> None:
    for email in INVITE_EMAILS:
        try:
            uid, status = ensure_user(email)
            print(f"{email}: {status} ({uid})")
        except requests.HTTPError as e:
            detail = e.response.text[:500] if e.response is not None else str(e)
            print(f"{email}: ERROR {e} — {detail}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
