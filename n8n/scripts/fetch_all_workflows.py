#!/usr/bin/env python3
"""
Download all active n8n workflows and save sanitized JSON under n8n/workflows/.

Maps workflow name -> filename (snake_case). Updates manifest.json with id/active/exported_at.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
WF_DIR = PROJECT / "n8n" / "workflows"
SHARED_DIR = WF_DIR / "_shared"
MANIFEST = WF_DIR / "manifest.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sanitize_workflow_secrets import audit_strings, sanitize_workflow  # noqa: E402

sys.path.insert(0, str(PROJECT / "n8n"))
from push_consolidated_activate import _api, _load_n8n_key  # noqa: E402

# Prefer updating these filenames when names match
NAME_TO_FILE = {
    "health": "health.json",
    "auth_me": "auth_me.json",
    "auth_magic_link": "auth_magic_link.json",
    "uploads_room_photo": "uploads_room_photo.json",
    "uploads_reference": "uploads_reference.json",
    "uploads_reference_bulk": "uploads_reference_bulk.json",
    "caption_generate": "caption_generate.json",
    "generate_orchestrated": "generate_orchestrated.json",
    "generate_edit": "generate_edit.json",
    "generate_commit": "generate_commit.json",
    "generations_export": "generations_export.json",
    "generations_session": "generations_session.json",
    "admin_metrics": "admin_metrics.json",
    "wf_supabase_verify": "_shared/wf_supabase_verify.json",
    "wf_event_log": "_shared/wf_event_log.json",
    "wf_save_generation": "_shared/wf_save_generation.json",
    "wf_enhance_caption": "wf_enhance_caption.json",
    "interior_design_rag_consolidated": "interior_design_rag_consolidated.json",
    "generate_edit": "generate_edit.json",
}


def slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_")
    return s or "workflow"


def export_body(wf: dict) -> dict:
    keep = ("name", "nodes", "connections", "settings", "staticData", "pinData", "meta")
    out = {k: wf[k] for k in keep if k in wf and wf[k] is not None}
    out["_export"] = {
        "workflow_id": wf.get("id"),
        "active": wf.get("active"),
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    return out


def target_path(name: str) -> Path:
    if name in NAME_TO_FILE:
        rel = NAME_TO_FILE[name]
        return WF_DIR / rel if not rel.startswith("_shared") else SHARED_DIR / rel.split("/", 1)[1]
    return WF_DIR / f"{slug(name)}.json"


def main() -> None:
    key = _load_n8n_key()
    _code, data = _api("GET", "/workflows?limit=250", key)
    items = data.get("data", data) if isinstance(data, dict) else data
    manifest: dict = {"exported_at": datetime.now(timezone.utc).isoformat(), "workflows": []}
    leaked: list[str] = []

    for row in sorted(items, key=lambda x: (x.get("name") or "").lower()):
        wid = row.get("id")
        name = row.get("name") or wid
        _code, wf = _api("GET", f"/workflows/{wid}", key)
        if not isinstance(wf, dict):
            print(f"SKIP {name}: bad response", file=sys.stderr)
            continue
        body = export_body(wf)
        clean = sanitize_workflow(body)
        raw_check = json.dumps(clean)
        hits = audit_strings(raw_check)
        if hits:
            leaked.append(f"{name}: still has {hits}")

        dest = target_path(name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(clean, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {dest.relative_to(PROJECT)} ({len(clean.get('nodes', []))} nodes, active={row.get('active')})")
        manifest["workflows"].append(
            {
                "id": wid,
                "name": name,
                "active": row.get("active"),
                "file": str(dest.relative_to(PROJECT)).replace("\\", "/"),
            }
        )

    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"\nManifest: {MANIFEST.relative_to(PROJECT)} ({len(manifest['workflows'])} workflows)")
    if leaked:
        print("WARNING post-sanitize hits:", file=sys.stderr)
        for line in leaked:
            print(f"  {line}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
