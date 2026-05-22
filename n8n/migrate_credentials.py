"""
Migrate hardcoded secrets in n8n workflows to credentials + process.env.
Run once against the VPS n8n instance.
"""
import json, urllib.request, urllib.error, copy

import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


def _load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    env_path = PROJECT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


_ENV = _load_env()
API_BASE = os.environ.get("N8N_API_BASE", _ENV.get("N8N_API_BASE", "https://n8n.srv1649259.hstgr.cloud/api/v1"))
API_KEY = os.environ.get("N8N_API_KEY", _ENV.get("N8N_API_KEY", ""))
if not API_KEY:
    raise SystemExit("Set N8N_API_KEY in .env before running migrate_credentials.py")

SUPABASE_URL = os.environ.get("SUPABASE_URL", _ENV.get("SUPABASE_URL", ""))
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", _ENV.get("SUPABASE_SERVICE_KEY", ""))
SUPABASE_KEY_OLD = os.environ.get("SUPABASE_SERVICE_KEY_OLD", _ENV.get("SUPABASE_SERVICE_KEY_OLD", SUPABASE_KEY))
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", _ENV.get("OPENROUTER_API_KEY", ""))
GEMINI_KEY = os.environ.get("GOOGLE_AI_STUDIO_KEY", _ENV.get("GEMINI_API_KEY", _ENV.get("GOOGLE_AI_STUDIO_KEY", "")))
JWT_DEV = os.environ.get("JWT_SECRET", _ENV.get("JWT_SECRET", ""))
JWT_SECRET = JWT_DEV
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", _ENV.get("ADMIN_TOKEN", ""))

WF_IDS = [
    ("85QkGoCbJy5HFOCi", "health"),
    ("qGFtMyFOqd4IDzsu", "admin_metrics"),
    ("URWOKul2iCfEww83", "auth_magic_link"),
    ("Zd7ljIVPwGgfmiBv", "auth_me"),
    ("neBg3130bCVFDqNZ", "uploads_room_photo"),
    ("bzNhfK13U1nufiLD", "retrieve_references"),
    ("I1YHQVRe9yljhZJu", "generate_draft"),
    ("sfVJP0fobCZLRIN2", "generate_commit"),
    ("r1eiHJf1twXOECJd", "generate_edit"),
    ("0FJFDIiYcWpMD0fT", "generate_orchestrated"),
    ("KJlz5cR0HG0zhcGx", "generations_session"),
    ("la36BW7IfLmI6hW9", "generations_export"),
    ("uzivvsijQnPa8wBz", "wf_enhance_caption"),
    ("pWtkzdP2XLIl2JaW", "wf_jwt_sign"),
    ("PN5YANsmuOGA6qGe", "wf_jwt_verify"),
    ("Hycihwac8DqZzBje", "wf_event_log"),
    ("CdB8jeEoxr2p3Nht", "wf_save_generation"),
]

WRITABLE = {"name", "nodes", "connections", "settings", "staticData", "pinData"}

# ── helpers ─────────────────────────────────────────────────────────────────

def api(method, path, body=None):
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json", "X-N8N-API-KEY": API_KEY},
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, f"{e.code}: {e.read().decode()[:300]}"


def create_cred(name, ctype, data):
    result, err = api("POST", "/credentials", {"name": name, "type": ctype, "data": data})
    if err:
        print(f"  FAIL creating {name}: {err}")
        return None
    print(f"  OK  {name}  id={result['id']}")
    return result


# ── Step 1: credentials ──────────────────────────────────────────────────────

print("=== Creating credentials ===")

cred_supa = create_cred("Supabase Production", "supabaseApi", {
    "host": SUPABASE_URL,
    "serviceRole": SUPABASE_KEY,
})

cred_or = create_cred("OpenRouter API", "httpBearerAuth", {
    "token": OPENROUTER_KEY,
})

cred_gem = create_cred("Google Gemini API", "httpHeaderAuth", {
    "name": "x-goog-api-key",
    "value": GEMINI_KEY,
})

SUPABASE_C  = {"id": cred_supa["id"], "name": "Supabase Production"} if cred_supa else None
OPENROUTER_C = {"id": cred_or["id"],  "name": "OpenRouter API"}      if cred_or   else None
GEMINI_C    = {"id": cred_gem["id"],  "name": "Google Gemini API"}   if cred_gem  else None

# ── Step 2: patch functions ──────────────────────────────────────────────────

# All literal secrets → $env.*  (n8n task-runner sandbox has no process.env)
SECRET_MAP = [
    (SUPABASE_KEY_OLD, "$env.SUPABASE_SERVICE_KEY"),
    (SUPABASE_KEY,     "$env.SUPABASE_SERVICE_KEY"),
    (SUPABASE_URL,     "$env.SUPABASE_URL"),
    (GEMINI_KEY,       "$env.GOOGLE_AI_STUDIO_KEY"),
    (OPENROUTER_KEY,   "$env.OPENROUTER_API_KEY"),
    (JWT_DEV,          "$env.JWT_SECRET"),
    (JWT_SECRET,       "$env.JWT_SECRET"),
    (ADMIN_TOKEN,      "$env.ADMIN_TOKEN"),
]


def patch_code(node):
    js = node["parameters"].get("jsCode", "")
    if not js:
        return False
    orig = js
    for secret, env_expr in SECRET_MAP:
        js = js.replace(f"'{secret}'", env_expr)
        js = js.replace(f'"{secret}"', env_expr)
    node["parameters"]["jsCode"] = js
    return js != orig


def header_contains(h, *values):
    v = h.get("value", "")
    return any(val in v for val in values)


def patch_http(node):
    params = node.get("parameters", {})
    hp = params.get("headerParameters", {})
    headers = hp.get("parameters", [])
    changed = False

    # Supabase — apikey or Authorization: Bearer <supabase-key>
    supa_keys = {SUPABASE_KEY, SUPABASE_KEY_OLD}
    supa_headers = [
        h for h in headers
        if h.get("name", "").lower() in ("apikey", "authorization")
        and any(k in h.get("value", "") for k in supa_keys)
    ]
    if supa_headers and SUPABASE_C:
        params["authentication"] = "predefinedCredentialType"
        params["nodeCredentialType"] = "supabaseApi"
        hp["parameters"] = [h for h in headers if h not in supa_headers]
        headers = hp["parameters"]
        node.setdefault("credentials", {})["supabaseApi"] = SUPABASE_C
        changed = True

    # OpenRouter — Authorization: Bearer <openrouter-key>
    or_headers = [
        h for h in headers
        if h.get("name", "").lower() == "authorization" and OPENROUTER_KEY in h.get("value", "")
    ]
    if or_headers and OPENROUTER_C:
        params["authentication"] = "genericCredentialType"
        params["genericAuthType"] = "httpBearerAuth"
        hp["parameters"] = [h for h in headers if h not in or_headers]
        headers = hp["parameters"]
        node.setdefault("credentials", {})["httpBearerAuth"] = OPENROUTER_C
        changed = True

    # Google Gemini — x-goog-api-key
    gem_headers = [
        h for h in headers
        if h.get("name", "").lower() == "x-goog-api-key" and GEMINI_KEY in h.get("value", "")
    ]
    if gem_headers and GEMINI_C:
        params["authentication"] = "genericCredentialType"
        params["genericAuthType"] = "httpHeaderAuth"
        hp["parameters"] = [h for h in headers if h not in gem_headers]
        node.setdefault("credentials", {})["httpHeaderAuth"] = GEMINI_C
        changed = True

    return changed


# ── Step 3: iterate workflows ────────────────────────────────────────────────

print()
print("=== Patching workflows ===")

for wf_id, label in WF_IDS:
    wf, err = api("GET", f"/workflows/{wf_id}")
    if err:
        print(f"  GET {wf_id} ({label}): {err}")
        continue

    code_n = http_n = 0
    for node in wf.get("nodes", []):
        ntype = node.get("type", "")
        if "code" in ntype:
            if patch_code(node):
                code_n += 1
        elif "httpRequest" in ntype:
            if patch_http(node):
                http_n += 1

    if code_n == 0 and http_n == 0:
        print(f"  {wf_id}  {label:35} — unchanged")
        continue

    payload = {k: v for k, v in wf.items() if k in WRITABLE}
    _, err = api("PUT", f"/workflows/{wf_id}", payload)
    if err:
        print(f"  {wf_id}  {label:35} — PUT FAIL: {err[:120]}")
    else:
        print(f"  {wf_id}  {label:35} — code:{code_n} http:{http_n}")

print()
print("=== Done ===")
print("Set these environment variables on the n8n VPS:")
for k in ["JWT_SECRET", "ADMIN_TOKEN", "SUPABASE_URL", "SUPABASE_SERVICE_KEY",
          "OPENROUTER_API_KEY", "GOOGLE_AI_STUDIO_KEY"]:
    print(f"  {k}")
