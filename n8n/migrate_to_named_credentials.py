#!/usr/bin/env python3
"""
Replace hardcoded secrets in n8n workflow JSONs with n8n env-var expressions.

Usage:
  python n8n/migrate_to_named_credentials.py --check
  python n8n/migrate_to_named_credentials.py --apply

Set variables in n8n Settings → Environment (see .env.example).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent.parent
WORKFLOWS_DIR = ROOT / "n8n" / "workflows"

# Regex-based replacements (no literal secrets in this file)
PATTERN_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"Bearer sk-or-v1-[A-Za-z0-9]+"), "=Bearer {{ $env.OPENROUTER_API_KEY }}"),
    (re.compile(r"sk-or-v1-[A-Za-z0-9]+"), "={{ $env.OPENROUTER_API_KEY }}"),
    (
        re.compile(
            r"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"
        ),
        "={{ $env.SUPABASE_ANON_KEY }}",
    ),
    (re.compile(r"sb_secret_[A-Za-z0-9_-]+"), "={{ $env.SUPABASE_SERVICE_KEY }}"),
    (re.compile(r"=sb_secret_[A-Za-z0-9_-]+"), "={{ $env.SUPABASE_SERVICE_KEY }}"),
    (re.compile(r"Bearer sb_secret_[A-Za-z0-9_-]+"), "=Bearer {{ $env.SUPABASE_SERVICE_KEY }}"),
    (re.compile(r"=Bearer sb_secret_[A-Za-z0-9_-]+"), "=Bearer {{ $env.SUPABASE_SERVICE_KEY }}"),
    (re.compile(r"AIzaSy[A-Za-z0-9_-]{20,}"), "={{ $env.GOOGLE_AI_STUDIO_KEY }}"),
    (re.compile(r"__REDACTED_ADMIN_TOKEN__"), "' + ($env.ADMIN_TOKEN || '') + '"),
    (re.compile(r"__REDACTED_ADMIN_TOKEN__"), "' + ($env.ADMIN_TOKEN || '') + '"),
]

REMAINING_SECRETS = ["AIzaSy", "sk-or-v1", "sb_secret_"]


def patch_text(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    for pattern, repl in PATTERN_REPLACEMENTS:
        if pattern.search(text):
            text, n = pattern.subn(repl, text)
            if n:
                changes.append(f"  replaced {n}x via {pattern.pattern[:40]}…")
    return text, changes


def patch_file(path: pathlib.Path, apply: bool) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    patched, changes = patch_text(raw)
    if not changes:
        return []
    if apply:
        path.write_text(patched, encoding="utf-8")
    return [f"{path.relative_to(ROOT)}:"] + changes


def main() -> None:
    apply = "--apply" in sys.argv
    total: list[str] = []
    for path in sorted(WORKFLOWS_DIR.rglob("*.json")):
        if path.name == "work.json":
            continue
        total.extend(patch_file(path, apply))
    if not total:
        print("No hardcoded secrets matched in workflow JSON files.")
        return
    print(("APPLIED" if apply else "DRY-RUN") + ":\n" + "\n".join(total))
    if not apply:
        print("\nRe-run with --apply to write changes.")


if __name__ == "__main__":
    main()
