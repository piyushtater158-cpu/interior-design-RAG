#!/usr/bin/env python3
"""PUT allowlist-patched workflow JSONs to live n8n (split deployment)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Reuse push helper from parent package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from push_consolidated_activate import _api, _load_n8n_key, _put_merge_activate

PROJECT = Path(__file__).resolve().parents[2]
WF_DIR = PROJECT / "n8n" / "workflows"

DEPLOY = {
    "generate_orchestrated.json": "0FJFDIiYcWpMD0fT",
    "generate_edit.json": "r1eiHJf1twXOECJd",
    "generate_commit.json": "sfVJP0fobCZLRIN2",
    "caption_generate.json": "XfzyMx6c4spt0AxC",
    "uploads_room_photo.json": "neBg3130bCVFDqNZ",
    "uploads_reference_bulk.json": "f7z0T8JNKRTpUZiS",
}


def main() -> None:
    key = _load_n8n_key()
    for filename, wf_id in DEPLOY.items():
        path = WF_DIR / filename
        local = json.loads(path.read_text(encoding="utf-8"))
        print(f"\n=== {filename} -> {wf_id} ===")
        _put_merge_activate(key, wf_id, local)
    print("\nAll allowlist workflows deployed.")


if __name__ == "__main__":
    main()
