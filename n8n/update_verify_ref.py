"""
Patches live n8n workflows to:
  1. Replace wf_jwt_verify -> wf_supabase_verify
  2. Fix stale wf_event_log / wf_save_generation IDs (404 on server)
  3. Ensure description is a string (not null)
Also syncs the local source JSON files.
"""
import json, os, sys
import urllib.request, urllib.error

N8N_BASE = "https://n8n.srv1649259.hstgr.cloud"
N8N_KEY  = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
             ".eyJzdWIiOiJiNjM5NGU0MC02YzQ2LTQ1M2ItYWNhOS01Y2NhMTdlZWJmOGEi"
             "LCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNTkxNTQx"
             "ZDAtNjFkNi00MTI0LWFhZGMtZTZkNGY3ZDI3YTU3IiwiaWF0IjoxNzc4MDgw"
             "OTEzLCJleHAiOjE3ODA2MTA0MDB9"
             ".dtY7tmo61eiTqkJevyA5sThzKnMWbrPj4k8LAehnOzk")

WRITABLE = {"name", "description", "nodes", "connections",
            "settings", "staticData", "pinData"}

# ID substitutions to apply to every executeWorkflow node
ID_MAP = {
    # wf_jwt_verify (any old deployment)
    "iPfGe1kcq5Uz1bLV": ("56BlN6jqFkXVszX2", "wf_supabase_verify"),
    "PN5YANsmuOGA6qGe": ("56BlN6jqFkXVszX2", "wf_supabase_verify"),
    # stale wf_event_log -> correct server ID
    "DED19gZAiWymYRdY": ("Hycihwac8DqZzBje", "wf_event_log"),
    # stale wf_save_generation -> correct server ID
    "xaDS6H9QuMdNovir": ("CdB8jeEoxr2p3Nht", "wf_save_generation"),
}
# Also fix by cachedResultName in case the value doesn't match
NAME_MAP = {
    "wf_jwt_verify": ("56BlN6jqFkXVszX2", "wf_supabase_verify"),
}

WORKFLOWS = {
    "auth_me.json":               "Zd7ljIVPwGgfmiBv",
    "uploads_room_photo.json":    "neBg3130bCVFDqNZ",
    "generations_session.json":   "KJlz5cR0HG0zhcGx",
    "generations_export.json":    "la36BW7IfLmI6hW9",
    "generate_orchestrated.json": "0FJFDIiYcWpMD0fT",
    "generate_edit.json":         "r1eiHJf1twXOECJd",
    "generate_commit.json":       "sfVJP0fobCZLRIN2",
}

BASE_DIR = (r"C:\Users\asus\OneDrive\Documents\Claude\Projects"
            r"\Interior design RAG\n8n\workflows")

def api(method, path, body=None):
    url = f"{N8N_BASE}/api/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json", "X-N8N-API-KEY": N8N_KEY}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def patch_nodes(nodes):
    changes = 0
    for node in nodes:
        if node.get("type") != "n8n-nodes-base.executeWorkflow":
            continue
        wid = node.get("parameters", {}).get("workflowId")
        if isinstance(wid, dict):
            val  = wid.get("value", "")
            name = wid.get("cachedResultName", "")
            if val in ID_MAP:
                new_id, new_name = ID_MAP[val]
                wid["value"] = new_id
                wid["cachedResultName"] = new_name
                changes += 1
            elif name in NAME_MAP:
                new_id, new_name = NAME_MAP[name]
                wid["value"] = new_id
                wid["cachedResultName"] = new_name
                changes += 1
        elif isinstance(wid, str) and wid in ID_MAP:
            new_id, _ = ID_MAP[wid]
            node["parameters"]["workflowId"] = new_id
            changes += 1
    return changes

ok = errors = 0

for fname, server_id in WORKFLOWS.items():
    print(f"\n[{fname} | server={server_id}]")
    try:
        live = api("GET", f"/workflows/{server_id}")
    except Exception as e:
        print(f"  GET failed: {e}")
        errors += 1
        continue

    changes = patch_nodes(live.get("nodes", []))
    print(f"  patched {changes} node reference(s) in live workflow")

    # also sync local source file
    local_path = os.path.join(BASE_DIR, fname)
    if os.path.exists(local_path):
        with open(local_path, encoding="utf-8-sig") as f:
            src = json.load(f)
        src_c = patch_nodes(src.get("nodes", []))
        if src_c:
            with open(local_path, "w", encoding="utf-8") as f:
                json.dump(src, f, indent=2)
            print(f"  local file: {src_c} ref(s) updated")

    payload = {k: v for k, v in live.items() if k in WRITABLE}
    # n8n requires description to be a string
    payload["description"] = payload.get("description") or ""

    try:
        api("PUT", f"/workflows/{server_id}", payload)
        print(f"  PUT OK")
        ok += 1
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"  PUT HTTP {e.code}: {err_body[:400]}")
        errors += 1
    except Exception as e:
        print(f"  PUT failed: {e}")
        errors += 1

print(f"\nResult: {ok} OK, {errors} failed.")
sys.exit(0 if errors == 0 else 1)
