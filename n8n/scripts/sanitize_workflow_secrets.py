#!/usr/bin/env python3
"""Redact secret literals from workflow JSON / strings before committing."""
from __future__ import annotations

import json
import re
from typing import Any

# Order matters: longer / specific patterns first
REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"sk-or-v1-[A-Za-z0-9]+"), "__REDACTED_OPENROUTER_API_KEY__"),
    (re.compile(r"sb_secret_[A-Za-z0-9_-]+"), "__REDACTED_SUPABASE_SERVICE_KEY__"),
    (re.compile(r"AIzaSy[A-Za-z0-9_-]{20,}"), "__REDACTED_GEMINI_API_KEY__"),
    (
        re.compile(
            r"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"
        ),
        "__REDACTED_SUPABASE_ANON_KEY__",
    ),
    (re.compile(r"__REDACTED_ADMIN_TOKEN__"), "__REDACTED_ADMIN_TOKEN__"),
    (re.compile(r"__REDACTED_ADMIN_TOKEN__"), "__REDACTED_ADMIN_TOKEN__"),
    (
        re.compile(
            r"6o2iWJgH\+dV2nlfIf3vRV/pJdYl\+lnkwSR40QmSv8/C\+zW4Z\+P2Ri6x0WSaNfVBo"
        ),
        "__REDACTED_JWT_SECRET__",
    ),
    (re.compile(r"__REDACTED_JWT_SECRET__"), "__REDACTED_JWT_SECRET__"),
    (
        re.compile(
            r"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            r"\.eyJzdWIiOiJiNjM5NGU0MC02YzQ2LTQ1M2ItYWNhOS01Y2NhMTdlZWJmOGEi[^\"']+"
        ),
        "__REDACTED_N8N_API_KEY__",
    ),
]


def redact_string(text: str) -> str:
    out = text
    for pattern, repl in REPLACEMENTS:
        out = pattern.sub(repl, out)
    return out


def sanitize_workflow(wf: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy with secrets redacted in all string fields."""
    raw = json.dumps(wf, ensure_ascii=False)
    cleaned = redact_string(raw)
    return json.loads(cleaned)


def audit_strings(text: str) -> list[str]:
    hits: list[str] = []
    for pattern, label in REPLACEMENTS:
        if pattern.search(text):
            hits.append(label)
    return hits
