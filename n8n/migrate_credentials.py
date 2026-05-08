"""
Migrate hardcoded secrets in n8n workflows to credentials + process.env.
Run once against the VPS n8n instance.
"""
import json, urllib.request, urllib.error, copy

API_BASE = "https://n8n.srv1649259.hstgr.cloud/api/v1"
API_KEY  = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiJiNjM5NGU0MC02YzQ2LTQ1M2ItYWNhOS01Y2NhMTdlZWJmOGEiLCJpc3MiOiJuOG4i"
    "LCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNTkxNTQxZDAtNjFkNi00MTI0LWFhZGMtZTZkNGY3"
    "ZDI3YTU3IiwiaWF0IjoxNzc4MDgwOTEzLCJleHAiOjE3ODA2MTA0MDB9"
    ".dtY7tmo61eiTqkJevyA5sThzKnMWbrPj4k8LAehnOzk"
)

SUPABASE_URL     = "https://uzghfpxboktnbcbbthns.supabase.co"
SUPABASE_KEY     = "__REDACTED_SUPABASE_SERVICE_KEY__"
SUPABASE_KEY_OLD = "__REDACTED_SUPABASE_SERVICE_KEY__"
OPENROUTER_KEY   = "__REDACTED_OPENROUTER_API_KEY__"
GEMINI_KEY       = "__REDACTED_GEMINI_API_KEY__"
JWT_DEV          = "__REDACTED_JWT_SECRET__"
JWT_SECRET       = "__REDACTED_JWT_SECRET__"
ADMIN_TOKEN      = "__REDACTED_ADMIN_TOKEN__"

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

# All literal secrets → process.env.*  (applies inside jsCode strings)
SECRET_MAP = [
    (SUPABASE_KEY_OLD, "process.env.SUPABASE_SERVICE_KEY"),
    (SUPABASE_KEY,     "process.env.SUPABASE_SERVICE_KEY"),
    (SUPABASE_URL,     "process.env.SUPABASE_URL"),
    (GEMINI_KEY,       "process.env.GOOGLE_AI_STUDIO_KEY"),
    (OPENROUTER_KEY,   "process.env.OPENROUTER_API_KEY"),
    (JWT_DEV,          "process.env.JWT_SECRET"),
    (JWT_SECRET,       "process.env.JWT_SECRET"),
    (ADMIN_TOKEN,      "process.env.ADMIN_TOKEN"),
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
