#!/usr/bin/env python3
"""
Push a workflow JSON to production n8n (merge + PUT + activate).

Uses N8N_API_KEY from project .env. Default: generations_export → fixes
POST /webhook/generations/:id/export on split-workflow deployments.

Modes:
  python n8n/push_consolidated_activate.py
      → writes n8n/workflows/work.json from generations_export.json,
        PUTs to workflow la36BW7IfLmI6hW9, activates.

  python n8n/push_consolidated_activate.py consolidated JbnB5CPdoqgCl75F
      → work.json from interior_design_rag_consolidated.json,
        PUTs to given workflow id (must already exist on server).

  python n8n/push_consolidated_activate.py consolidated --create "INTERIOR DESIGN RAG"
      → POSTs new workflow from consolidated (only if you know duplicate
        webhooks are deactivated elsewhere). Prints new id.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT = Path(__file__).resolve().parents[1]
WORK_JSON = PROJECT / "n8n" / "workflows" / "work.json"
N8N_API = os.environ.get("N8N_API_BASE", "https://n8n.srv1649259.hstgr.cloud/api/v1")

DEFAULT_EXPORT_WF_ID = "la36BW7IfLmI6hW9"
EXPORT_SOURCE = PROJECT / "n8n" / "workflows" / "generations_export.json"
CONSOLIDATED_SOURCE = PROJECT / "n8n" / "workflows" / "interior_design_rag_consolidated.json"
SUPABASE_CRED = {"supabaseApi": {"id": "7rZNgbzFZJtpVqub", "name": "Supabase account"}}


def _patch_export_supabase_nodes(wf: dict) -> None:
    """Replace blocked $env header auth with n8n supabaseApi credential."""
    for node in wf.get("nodes", []):
        if node.get("type") != "n8n-nodes-base.httpRequest":
            continue
        params = node.setdefault("parameters", {})
        blob = json.dumps(params)
        if "$env." not in blob and "SUPABASE_SERVICE_KEY" not in blob:
            continue
        params.pop("sendHeaders", None)
        hp = params.get("headerParameters", {})
        hp["parameters"] = [
            h for h in hp.get("parameters", [])
            if h.get("name") not in ("apikey", "Authorization")
        ]
        if hp.get("parameters"):
            params["headerParameters"] = hp
        else:
            params.pop("headerParameters", None)
        params["authentication"] = "predefinedCredentialType"
        params["nodeCredentialType"] = "supabaseApi"
        node["credentials"] = SUPABASE_CRED


def _load_n8n_key() -> str:
    env_path = PROJECT / ".env"
    if not env_path.exists():
        print("Missing .env with N8N_API_KEY", file=sys.stderr)
        sys.exit(1)
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("N8N_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    print("N8N_API_KEY not set in .env", file=sys.stderr)
    sys.exit(1)


def _api(method: str, path: str, key: str, body: dict | None = None) -> tuple[int, dict | list | str]:
    url = N8N_API.rstrip("/") + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "X-N8N-API-KEY": key},
    )
    with urlopen(req, timeout=180) as resp:
        raw = resp.read().decode("utf-8")
        code = resp.status
    if not raw:
        return code, {}
    try:
        return code, json.loads(raw)
    except json.JSONDecodeError:
        return code, raw


def _write_work_json(local: dict) -> None:
    strip_keys = ("name", "nodes", "connections", "settings", "staticData", "pinData")
    stripped = {k: local[k] for k in strip_keys if k in local}
    WORK_JSON.parent.mkdir(parents=True, exist_ok=True)
    WORK_JSON.write_text(json.dumps(stripped, indent=2), encoding="utf-8")
    print(f"Wrote {WORK_JSON.relative_to(PROJECT)} ({len(stripped.get('nodes', []))} nodes)")


def _put_merge_activate(key: str, wf_id: str, local: dict) -> None:
    _write_work_json(local)
    try:
        _code, cur = _api("GET", f"/workflows/{wf_id}", key)
    except HTTPError as e:
        print(f"GET workflow {wf_id} failed: HTTP {e.code} {e.reason}", file=sys.stderr)
        if e.code == 404:
            print(
                "Hint: list workflows with GET /api/v1/workflows and use an existing id, "
                "or run: python n8n/push_consolidated_activate.py consolidated --create \"NAME\"",
                file=sys.stderr,
            )
        sys.exit(1)
    except URLError as e:
        print(f"GET workflow failed: {e.reason}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(cur, dict):
        print("Unexpected GET response", file=sys.stderr)
        sys.exit(1)

    # n8n rejects unknown keys on PUT (e.g. active, versionId, shared, …)
    merged: dict = {
        "name": local.get("name") or cur.get("name"),
        "nodes": local["nodes"],
        "connections": local["connections"],
        "settings": local.get("settings") or cur.get("settings") or {},
    }
    if "description" in cur or "description" in local:
        merged["description"] = local.get("description", cur.get("description") or "")
    for k in ("staticData", "pinData"):
        if k in local and local[k]:
            merged[k] = local[k]
        elif k in cur and cur[k]:
            merged[k] = cur[k]

    try:
        _code, updated = _api("PUT", f"/workflows/{wf_id}", key, merged)
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:2000]
        print(f"PUT failed: HTTP {e.code}\n{body}", file=sys.stderr)
        sys.exit(1)

    if isinstance(updated, dict):
        print(
            f"PUT ok: id={updated.get('id')} active={updated.get('active')} "
            f"nodes={len(updated.get('nodes', []))}"
        )
    else:
        print("PUT ok")

    try:
        _code, act = _api("POST", f"/workflows/{wf_id}/activate", key, {})
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:2000]
        print(f"ACTIVATE failed: HTTP {e.code}\n{body}", file=sys.stderr)
        sys.exit(1)

    if isinstance(act, dict):
        print(f"ACTIVATE ok: active={act.get('active', act)}")
    else:
        print("ACTIVATE ok")


def _post_create(key: str, local: dict, name: str) -> str:
    strip_keys = ("nodes", "connections", "settings", "staticData", "pinData")
    body = {k: local[k] for k in strip_keys if k in local}
    body["name"] = name
    try:
        _code, created = _api("POST", "/workflows", key, body)
    except HTTPError as e:
        print(e.read().decode("utf-8", errors="replace")[:2000], file=sys.stderr)
        sys.exit(1)
    if not isinstance(created, dict) or not created.get("id"):
        print("Unexpected POST /workflows response", file=sys.stderr)
        sys.exit(1)
    wid = created["id"]
    print(f"CREATED workflow id={wid}")
    _api("POST", f"/workflows/{wid}/activate", key, {})
    print(f"ACTIVATE ok for {wid}")
    return wid


def main() -> None:
    key = _load_n8n_key()
    argv = [a.lower() for a in sys.argv[1:]]
    if "consolidated" in argv and "--create" in argv:
        idx = argv.index("--create")
        name = sys.argv[sys.argv.index("--create") + 1] if len(sys.argv) > sys.argv.index("--create") + 1 else "INTERIOR DESIGN RAG"
        local = json.loads(CONSOLIDATED_SOURCE.read_text(encoding="utf-8"))
        _write_work_json(local)
        _post_create(key, local, name)
        return
    if len(sys.argv) >= 3 and sys.argv[1].lower() == "consolidated":
        wf_id = sys.argv[2]
        local = json.loads(CONSOLIDATED_SOURCE.read_text(encoding="utf-8"))
        _put_merge_activate(key, wf_id, local)
        return

    # default: generations_export
    local = json.loads(EXPORT_SOURCE.read_text(encoding="utf-8"))
    _patch_export_supabase_nodes(local)
    _put_merge_activate(key, DEFAULT_EXPORT_WF_ID, local)


if __name__ == "__main__":
    main()
