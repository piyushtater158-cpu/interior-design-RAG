#!/usr/bin/env python3
"""
Patch and deploy generate_orchestrated without secrets in workflow JSON.

- Config node: non-secret routing only (URLs, model names).
- OpenRouter HTTP nodes: n8n openRouterApi credential (same as caption_generate).
- Supabase service-role reads: n8n supabaseApi credential.
- Supabase RLS reads: n8n httpHeaderAuth credential for apikey + user bearer_token from item JSON.

Validation (JWT) stays in wf_supabase_verify sub-workflow; bearer_token flows on $json.

Usage:
  python n8n/generate_orchestrated_workflow.py --check
  python n8n/generate_orchestrated_workflow.py --apply
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from copy import deepcopy
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).parent.parent
WF_PATH = Path(__file__).parent / "workflows" / "generate_orchestrated.json"
CRED_REFS_PATH = Path(__file__).parent / "credential_refs.json"
DEBUG_LOG = PROJECT / "debug-1b1362.log"
SESSION_DEBUG_LOG = PROJECT / "debug-79addd.log"
N8N_BASE = "https://n8n.srv1649259.hstgr.cloud/api/v1"
WORKFLOW_ID = "0FJFDIiYcWpMD0fT"

WRITABLE = {"name", "description", "nodes", "connections", "settings", "staticData", "pinData"}

OPENROUTER_NODE_NAMES = {
    "Agent 1 (Orchestrator)",
    "Agent 2 (Retriever)",
    "Generate image (Gemini)",
}

OPENROUTER_URL_EXPR = "={{ $('Config').first().json._cfg.openrouter_base + '/chat/completions' }}"

RLS_NODE_NAMES = {
    "Fetch candidate pool",
    "Fetch candidate pool (all)",
    "Fetch picked URLs",
}

SERVICE_SUPABASE_NODES = {"Fetch image_model"}

SECRET_PATTERNS = [
    (re.compile(r"sk-or-v1-[a-zA-Z0-9]+"), "openrouter_key"),
    (re.compile(r"sb_secret_[a-zA-Z0-9_-]+"), "supabase_service_key"),
    (
        re.compile(
            r"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"
        ),
        "jwt_like",
    ),
]

CONFIG_FIELDS = ("supabase_url", "openrouter_base", "orch_model", "retriever_model")

# Multimodal orchestrator: fast, reliable on long VL prompts (exec 1564 nemotron idle-timed out).
ORCH_MODEL_DEFAULT = "google/gemini-2.5-flash"

DEFAULT_CFG = {
    "supabase_url": "https://uzghfpxboktnbcbbthns.supabase.co",
    "openrouter_base": "https://openrouter.ai/api/v1",
    "orch_model": ORCH_MODEL_DEFAULT,
    "retriever_model": ORCH_MODEL_DEFAULT,
    "supabase_anon_key": "",
}


def debug_log(message: str, data: dict | None = None, hypothesis_id: str = "H-cred") -> None:
    # #region agent log
    payload = {
        "sessionId": "1b1362",
        "timestamp": int(time.time() * 1000),
        "location": "generate_orchestrated_workflow.py",
        "message": message,
        "data": data or {},
        "hypothesisId": hypothesis_id,
        "runId": "gen-orch-creds",
    }
    with DEBUG_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
    # #endregion


def _read_env() -> dict[str, str]:
    out: dict[str, str] = {}
    env_path = PROJECT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


def _anon_from_env() -> str:
    return _read_env().get("SUPABASE_ANON_KEY", "") or DEFAULT_CFG["supabase_anon_key"]


def load_cred_refs() -> dict[str, Any]:
    return json.loads(CRED_REFS_PATH.read_text(encoding="utf-8"))


def api(method: str, path: str, body: dict | None = None) -> dict:
    api_key = _read_env().get("N8N_API_KEY", "")
    if not api_key:
        raise RuntimeError("N8N_API_KEY missing from .env")
    req = urllib.request.Request(
        N8N_BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"Content-Type": "application/json", "X-N8N-API-KEY": api_key},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def list_credentials() -> list[dict]:
    return api("GET", "/credentials").get("data", [])


def ensure_supabase_anon_credential(
    anon_key: str, apply: bool, supabase_url: str
) -> dict[str, str]:
    refs = load_cred_refs()
    existing = refs.get("supabaseAnonApiKey")
    if existing and existing.get("id"):
        return existing

    creds = list_credentials()
    for c in creds:
        if c.get("name") == "Supabase Anon Key" and c.get("type") == "httpHeaderAuth":
            ref = {"id": c["id"], "name": c["name"]}
            refs["supabaseAnonApiKey"] = ref
            if apply:
                CRED_REFS_PATH.write_text(
                    json.dumps(refs, indent=2) + "\n", encoding="utf-8"
                )
            return ref

    if not apply:
        return {"id": "(would-create)", "name": "Supabase Anon Key"}

    supabase_host = supabase_url.rstrip("/")
    created = api(
        "POST",
        "/credentials",
        {
            "name": "Supabase Anon Key",
            "type": "httpHeaderAuth",
            "data": {
                "name": "apikey",
                "value": anon_key,
                "allowedDomains": supabase_host,
            },
        },
    )
    ref = {"id": created["id"], "name": created.get("name", "Supabase Anon Key")}
    refs["supabaseAnonApiKey"] = ref
    CRED_REFS_PATH.write_text(json.dumps(refs, indent=2) + "\n", encoding="utf-8")
    debug_log("created_anon_cred", {"id": ref["id"]}, "H-anon")
    return ref


def audit_secrets(wf: dict) -> list[str]:
    hits: list[str] = []
    blob = json.dumps(wf)
    for pattern, label in SECRET_PATTERNS:
        if pattern.search(blob):
            hits.append(label)
    if "$env." in blob:
        hits.append("$env")
    cfg = next((n for n in wf.get("nodes", []) if n.get("name") == "Config"), None)
    if cfg:
        js = cfg.get("parameters", {}).get("jsCode", "")
        for key in ("openrouter_key", "supabase_key", "supabase_anon_key"):
            if key in js:
                hits.append(f"config_field:{key}")
    for node in wf.get("nodes", []):
        params = node.get("parameters", {})
        for h in params.get("headerParameters", {}).get("parameters", []):
            val = str(h.get("value", ""))
            if "openrouter_key" in val or "supabase_key" in val or "supabase_anon_key" in val:
                hits.append(f"header_ref:{node.get('name')}:{h.get('name')}")
    return hits


def config_js(cfg: dict[str, str]) -> str:
    lines = [
        "return [{",
        "  json: {",
        "    ...$json,",
        "    _cfg: {",
        f"      supabase_url:    '{cfg['supabase_url']}',",
        f"      openrouter_base: '{cfg['openrouter_base']}',",
        f"      orch_model:      '{cfg['orch_model']}',",
        f"      retriever_model: '{cfg.get('retriever_model', cfg['orch_model'])}'",
        "    }",
        "  },",
        "  binary: $input.first().binary || {}",
        "}];",
    ]
    return "\n".join(lines)


def ensure_config_node(wf: dict, cfg: dict[str, str]) -> bool:
    """Insert Config after webhook when missing (Build Agent 1/2 use $('Config'))."""
    nodes = wf.setdefault("nodes", [])
    if any(n.get("name") == "Config" for n in nodes):
        return False

    webhook = next(
        (n for n in nodes if n.get("type") == "n8n-nodes-base.webhook"),
        None,
    )
    wh_pos = webhook.get("position", [240, 300]) if webhook else [240, 300]
    verify_name = "Extract user from token"
    verify = next((n for n in nodes if n.get("name") == verify_name), None)
    if not verify:
        raise RuntimeError("Cannot add Config: Extract user from token node missing")

    nodes.append(
        {
            "parameters": {"jsCode": config_js(cfg)},
            "id": "orch-config",
            "name": "Config",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [wh_pos[0] + 120, wh_pos[1]],
        }
    )

    conns = wf.setdefault("connections", {})
    wh_name = webhook["name"] if webhook else "POST /generate/orchestrated"
    old_targets = conns.get(wh_name, {}).get("main", [[]])[0]
    next_node = (
        old_targets[0]["node"]
        if old_targets and old_targets[0].get("node")
        else verify_name
    )
    conns[wh_name] = {
        "main": [[{"node": "Config", "type": "main", "index": 0}]]
    }
    conns["Config"] = {
        "main": [[{"node": next_node, "type": "main", "index": 0}]]
    }
    return True


def _strip_header(params: dict, name: str) -> None:
    headers = params.get("headerParameters", {}).get("parameters", [])
    params.setdefault("headerParameters", {})["parameters"] = [
        h for h in headers if h.get("name") != name
    ]


def patch_openrouter_node(node: dict, cred_refs: dict) -> bool:
    params = node.setdefault("parameters", {})
    _strip_header(params, "Authorization")
    params["authentication"] = "predefinedCredentialType"
    params["nodeCredentialType"] = "openRouterApi"
    params["url"] = OPENROUTER_URL_EXPR
    node["credentials"] = {"openRouterApi": cred_refs["openRouterApi"]}
    headers = params.setdefault("headerParameters", {}).setdefault("parameters", [])
    if not any(h.get("name") == "Content-Type" for h in headers):
        headers.append({"name": "Content-Type", "value": "application/json"})
    return True


def patch_supabase_service_node(node: dict, cred_refs: dict) -> bool:
    params = node.setdefault("parameters", {})
    for h in ("apikey", "Authorization"):
        _strip_header(params, h)
    params["authentication"] = "predefinedCredentialType"
    params["nodeCredentialType"] = "supabaseApi"
    node["credentials"] = {"supabaseApi": cred_refs["supabaseApi"]}
    url = params.get("url", "")
    if "uzghfpxboktnbcbbthns.supabase.co" in url and not str(url).startswith("="):
        params["url"] = (
            "={{ $('Config').first().json._cfg.supabase_url + "
            "'/rest/v1/app_config?key=eq.image_model&select=value' }}"
        )
    return True


def patch_rls_node(node: dict, cred_refs: dict) -> bool:
    params = node.setdefault("parameters", {})
    _strip_header(params, "apikey")
    params["authentication"] = "genericCredentialType"
    params["genericAuthType"] = "httpHeaderAuth"
    node["credentials"] = {"httpHeaderAuth": cred_refs["supabaseAnonApiKey"]}
    headers = params.setdefault("headerParameters", {}).setdefault("parameters", [])
    if not any(h.get("name") == "Authorization" for h in headers):
        headers.append(
            {"name": "Authorization", "value": "=Bearer {{ $json.bearer_token }}"}
        )
    else:
        for h in headers:
            if h.get("name") == "Authorization":
                h["value"] = "=Bearer {{ $json.bearer_token }}"
    if not any(h.get("name") == "Accept" for h in headers):
        headers.append({"name": "Accept", "value": "application/json"})
    return True


def patch_workflow(wf: dict, cred_refs: dict, cfg: dict[str, str]) -> dict:
    out = deepcopy(wf)
    ensure_config_node(out, cfg)
    from migrate_gemini_to_openrouter import EXTRACT_CODE_ORCHESTRATED

    for node in out.get("nodes", []):
        name = node.get("name", "")
        if name == "Config":
            node.setdefault("parameters", {})["jsCode"] = config_js(cfg)
        elif name == "Extract output PNG":
            js = node.setdefault("parameters", {}).get("jsCode", "")
            if "collectImageParts" not in js:
                node["parameters"]["jsCode"] = EXTRACT_CODE_ORCHESTRATED
        elif name == "Respond 200":
            params = node.setdefault("parameters", {})
            body = params.get("responseBody", "")
            if "Parse Agent 2" in body or "Parse Agent 1" in body:
                params["responseBody"] = (
                    "={{ JSON.stringify({\n"
                    "  generation_id:       $json.generation_id,\n"
                    "  output_url:          $json.output_url,\n"
                    "  latency_ms:          $json.latency_ms,\n"
                    "  cost_usd:            $json.cost_usd,\n"
                    "  model_id:            $json.model_id,\n"
                    "  backend_id:          'gemini',\n"
                    "  reference_image_ids: $json.reference_image_ids,\n"
                    "  criteria:            $json.criteria\n"
                    "}) }}"
                )
        elif name in OPENROUTER_NODE_NAMES:
            patch_openrouter_node(node, cred_refs)
        elif name in SERVICE_SUPABASE_NODES:
            patch_supabase_service_node(node, cred_refs)
        elif name in RLS_NODE_NAMES:
            patch_rls_node(node, cred_refs)

    if "$env." in json.dumps(out):
        raise RuntimeError("workflow still references $env after patch")
    hits = audit_secrets(out)
    if hits:
        raise RuntimeError(f"workflow still contains secrets: {hits}")
    return out


def deploy(wf: dict) -> dict:
    live = api("GET", f"/workflows/{WORKFLOW_ID}")
    payload = {k: v for k, v in live.items() if k in WRITABLE}
    payload["nodes"] = wf["nodes"]
    payload["connections"] = wf["connections"]
    payload["description"] = payload.get("description") or wf.get("description") or ""
    merged_settings = {**(live.get("settings") or {}), **(wf.get("settings") or {})}
    payload["settings"] = {"executionOrder": merged_settings.get("executionOrder", "v1")}
    api("PUT", f"/workflows/{WORKFLOW_ID}", payload)
    check = api("GET", f"/workflows/{WORKFLOW_ID}")
    if not check.get("active"):
        api("POST", f"/workflows/{WORKFLOW_ID}/activate")
    return check


def fetch_execution(exec_id: str) -> dict:
    return api("GET", f"/executions/{exec_id}?includeData=true")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--exec-id", default="1336", help="Execution to inspect after apply")
    args = parser.parse_args()
    if not args.check and not args.apply:
        parser.error("use --check or --apply")

    env = _read_env()
    orch_model = env.get(
        "OPENROUTER_ORCHESTRATOR_MODEL", DEFAULT_CFG["orch_model"]
    )
    cfg = {
        "supabase_url": env.get("SUPABASE_URL", DEFAULT_CFG["supabase_url"]),
        "openrouter_base": env.get("OPENROUTER_BASE_URL", DEFAULT_CFG["openrouter_base"]),
        "orch_model": orch_model,
        "retriever_model": env.get(
            "OPENROUTER_RETRIEVER_MODEL",
            env.get("OPENROUTER_ORCH_MODEL", orch_model),
        ),
    }
    anon_key = env.get("SUPABASE_ANON_KEY") or _anon_from_env()

    debug_log("start", {"check": args.check, "apply": args.apply}, "H1")

    cred_refs = load_cred_refs()
    anon_ref = ensure_supabase_anon_credential(
        anon_key, apply=args.apply, supabase_url=cfg["supabase_url"]
    )
    cred_refs["supabaseAnonApiKey"] = anon_ref

    wf = json.loads(WF_PATH.read_text(encoding="utf-8-sig"))
    before_hits = audit_secrets(wf)
    debug_log("audit_before", {"hits": before_hits}, "H2")

    patched = patch_workflow(wf, cred_refs, cfg)
    after_hits = audit_secrets(patched)
    debug_log("audit_after", {"hits": after_hits}, "H2")

    if args.check:
        print("Config fields:", CONFIG_FIELDS)
        print("Before audit:", before_hits or "clean")
        print("After patch:", after_hits or "clean")
        print("Anon credential:", anon_ref)
        return

    WF_PATH.write_text(json.dumps(patched, indent=2) + "\n", encoding="utf-8")
    deployed = deploy(patched)
    debug_log(
        "deployed",
        {
            "workflow_id": WORKFLOW_ID,
            "name": deployed.get("name"),
            "active": deployed.get("active"),
            "openrouter_nodes": sorted(OPENROUTER_NODE_NAMES),
        },
        "H3",
    )
    print(f"OK  deployed {deployed.get('name')} ({WORKFLOW_ID})")

    if args.exec_id:
        try:
            ex = fetch_execution(args.exec_id)
            err_nodes = []
            run_data = ex.get("data", {}).get("resultData", {}).get("runData", {})
            for node_name, runs in run_data.items():
                if not isinstance(runs, list):
                    continue
                for run in runs:
                    if not isinstance(run, list):
                        continue
                    for item in run:
                        if not isinstance(item, dict):
                            continue
                        err = item.get("error")
                        if err and isinstance(err, dict):
                            err_nodes.append(
                                {
                                    "node": node_name,
                                    "message": str(err.get("message", ""))[:200],
                                }
                            )
            debug_log(
                "execution_snapshot",
                {"id": args.exec_id, "status": ex.get("status"), "errors": err_nodes[:5]},
                "H4",
            )
            print(f"Execution {args.exec_id} status={ex.get('status')} (historical)")
        except urllib.error.HTTPError as e:
            debug_log("execution_fetch_failed", {"code": e.code}, "H4")


if __name__ == "__main__":
    main()
