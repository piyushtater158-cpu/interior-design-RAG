#!/usr/bin/env python3
"""
migrate_to_named_credentials.py
Replace hardcoded secrets in n8n workflow JSONs with n8n env-var expressions.

Usage:
  python n8n/migrate_to_named_credentials.py --check   # dry-run, print what would change
  python n8n/migrate_to_named_credentials.py --apply   # patch files in-place

After patching, set these environment variables in n8n Settings → Environment:
  OPENROUTER_API_KEY  = sk-or-v1-...
  SUPABASE_ANON_KEY   = eyJhbGc... (anon/public key)
  SUPABASE_SERVICE_KEY= sb_secret_... (service-role key)
  ADMIN_TOKEN         = __REDACTED_ADMIN_TOKEN__
"""

import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
WORKFLOWS_DIR = ROOT / "n8n" / "workflows"

# (literal_string, replacement_expression)
SIMPLE_REPLACEMENTS = [
    # OpenRouter API key
    (
        "Bearer __REDACTED_OPENROUTER_API_KEY__",
        "=Bearer {{ $env.OPENROUTER_API_KEY }}",
    ),
    (
        "__REDACTED_OPENROUTER_API_KEY__",
        "={{ $env.OPENROUTER_API_KEY }}",
    ),
    # Supabase anon key
    (
        "__REDACTED_JWT_OR_ANON__",
        "={{ $env.SUPABASE_ANON_KEY }}",
    ),
    # Supabase service key (used in REST calls; note: Phase 5 will refine which calls
    # should use user bearer vs service key)
    (
        "__REDACTED_SUPABASE_SERVICE_KEY__",
        "={{ $env.SUPABASE_SERVICE_KEY }}",
    ),
    (
        "=__REDACTED_SUPABASE_SERVICE_KEY__",
        "={{ $env.SUPABASE_SERVICE_KEY }}",
    ),
    (
        "Bearer __REDACTED_SUPABASE_SERVICE_KEY__",
        "=Bearer {{ $env.SUPABASE_SERVICE_KEY }}",
    ),
    (
        "=Bearer __REDACTED_SUPABASE_SERVICE_KEY__",
        "=Bearer {{ $env.SUPABASE_SERVICE_KEY }}",
    ),
    # Admin token (in JS code string)
    (
        "__REDACTED_ADMIN_TOKEN__",
        "' + (process.env.ADMIN_TOKEN || $env.ADMIN_TOKEN || '') + '",
    ),
]

# Gemini direct-call keys to flag as still needing manual migration
REMAINING_SECRETS = [
    "AIzaSy",  # Gemini API key prefix
]


def patch_text(text: str) -> tuple[str, list[str]]:
    """Apply all simple replacements. Returns (new_text, list_of_changes)."""
    changes = []
    for old, new in SIMPLE_REPLACEMENTS:
        if old in text:
            count = text.count(old)
            text = text.replace(old, new)
            changes.append(f"  replaced {count}x: {old[:60]}…")
    return text, changes


def check_remaining(text: str, path: pathlib.Path) -> list[str]:
    warnings = []
    for secret in REMAINING_SECRETS:
        if secret in text:
            warnings.append(f"  WARNING: still contains '{secret}' — needs manual migration")
    return warnings


def main() -> None:
    dry_run = "--check" in sys.argv
    apply   = "--apply" in sys.argv

    if not dry_run and not apply:
        print(__doc__)
        sys.exit(1)

    json_files = sorted(WORKFLOWS_DIR.rglob("*.json"))
    total_changes = 0

    for path in json_files:
        original = path.read_text(encoding="utf-8")
        patched, changes = patch_text(original)
        warnings = check_remaining(patched, path)

        if changes or warnings:
            print(f"\n{path.relative_to(ROOT)}")
            for c in changes:
                print(c)
            for w in warnings:
                print(w)
            total_changes += len(changes)

        if apply and changes and patched != original:
            path.write_text(patched, encoding="utf-8")
            print("  -> written")

    if total_changes == 0 and not any(
        check_remaining(p.read_text("utf-8"), p) for p in json_files
    ):
        print("No secrets found — already clean.")
    elif dry_run:
        print(f"\nDry run: {total_changes} replacement(s) would be applied. Run --apply to patch.")
    else:
        print(f"\nApplied {total_changes} replacement(s).")


if __name__ == "__main__":
    main()
