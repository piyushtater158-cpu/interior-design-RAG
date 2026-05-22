#!/usr/bin/env python3
"""
Build and deploy 13 individual n8n workflows — one per endpoint.

Each workflow is:
  - standalone (sub-workflows inlined, $env baked in)
  - titled as  "Function  (input -> output)"
  - deployed to n8n and activated

The consolidated workflow is deactivated first to free the webhook paths.

Usage (from project root):
    python n8n/deploy_individual.py
"""
import json, os, re, uuid, urllib.request, urllib.error
from copy import deepcopy
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

PROJECT = Path(__file__).parent.parent
WF_DIR  = PROJECT / "n8n" / "workflows"

N8N_BASE           = os.environ.get("N8N_API_BASE", "http://localhost:5678/api/v1").replace("/api/v1", "")
CONSOLIDATED_WF_ID = "JbnB5CPdoqgCl75F"

# ── Credentials ───────────────────────────────────────────────────────────────

def _load_env() -> dict:
    file_env: dict = {}
    env_path = PROJECT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            file_env[k.strip()] = v.strip()

    def get(key: str, *alts, default: str = "") -> str:
        for k in (key,) + alts:
            if v := os.environ.get(k):
                return v
        for k in (key,) + alts:
            if v := file_env.get(k):
                return v
        return default

    orch = get(
        "OPENROUTER_ORCHESTRATOR_MODEL",
        default="nvidia/nemotron-nano-12b-v2-vl:free",
    )
    return {
        "SUPABASE_URL":                  get("SUPABASE_URL"),
        "SUPABASE_SERVICE_KEY":          get("SUPABASE_SERVICE_KEY"),
        "GEMINI_API_KEY":                get("GEMINI_API_KEY", "GOOGLE_AI_STUDIO_KEY"),
        "OPENROUTER_API_KEY":            get("OPENROUTER_API_KEY"),
        "OPENROUTER_BASE_URL":           get("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1"),
        "OPENROUTER_ORCHESTRATOR_MODEL": orch,
        "OPENROUTER_RETRIEVER_MODEL":    get("OPENROUTER_RETRIEVER_MODEL", default=orch),
        "OPENROUTER_EMBED_MODEL":        get("OPENROUTER_EMBED_MODEL", default="nvidia/llama-nemotron-embed-vl-1b-v2:free"),
        # .env uses "JWT Secret" (with space) — check both forms
        "JWT_SECRET":                    get("JWT_SECRET", "JWT Secret"),
        # .env uses "Admin Token" (with space) — check both forms
        "ADMIN_TOKEN":                   get("ADMIN_TOKEN", "Admin Token"),
        "JWT_TTL_HOURS":                 get("JWT_TTL_HOURS", default="24"),
        "N8N_API_KEY":                   get("N8N_API_KEY"),
    }

_ENV = _load_env()
N8N_API_KEY = _ENV.get("N8N_API_KEY", "")
if not N8N_API_KEY:
    raise SystemExit("N8N_API_KEY not set in .env")

ENV_TO_CFG = {
    "SUPABASE_URL":                  "supabase_url",
    "SUPABASE_SERVICE_KEY":          "supabase_key",
    "GEMINI_API_KEY":                "gemini_key",
    "OPENROUTER_API_KEY":            "openrouter_key",
    "OPENROUTER_BASE_URL":           "openrouter_base",
    "OPENROUTER_ORCHESTRATOR_MODEL": "orch_model",
    "OPENROUTER_RETRIEVER_MODEL":    "retriever_model",
    "OPENROUTER_EMBED_MODEL":        "embed_model",
    "ADMIN_TOKEN":                   "admin_token",
    "JWT_SECRET":                    "jwt_secret",
    "JWT_TTL_HOURS":                 "jwt_ttl",
}

def _js(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")

# ── Config code node ──────────────────────────────────────────────────────────

CONFIG_CODE = (
    "return [{\n"
    "  json: {\n"
    "    ...$json,\n"
    "    _cfg: {\n"
    f"      supabase_url:    '{_js(_ENV['SUPABASE_URL'])}',\n"
    f"      supabase_key:    '{_js(_ENV['SUPABASE_SERVICE_KEY'])}',\n"
    f"      gemini_key:      '{_js(_ENV['GEMINI_API_KEY'])}',\n"
    f"      openrouter_key:  '{_js(_ENV['OPENROUTER_API_KEY'])}',\n"
    f"      openrouter_base: '{_js(_ENV['OPENROUTER_BASE_URL'])}',\n"
    f"      orch_model:      '{_js(_ENV['OPENROUTER_ORCHESTRATOR_MODEL'])}',\n"
    f"      retriever_model: '{_js(_ENV['OPENROUTER_RETRIEVER_MODEL'])}',\n"
    f"      embed_model:     '{_js(_ENV['OPENROUTER_EMBED_MODEL'])}',\n"
    f"      admin_token:     '{_js(_ENV['ADMIN_TOKEN'])}',\n"
    f"      jwt_secret:      '{_js(_ENV['JWT_SECRET'])}',\n"
    f"      jwt_ttl:         {_ENV['JWT_TTL_HOURS']}\n"
    "    }\n"
    "  },\n"
    "  binary: $input.first().binary || {}\n"
    "}];"
)

# ── JWT + HMAC templates (pure JS, no require) ────────────────────────────────

_JWT_SECRET = _js(_ENV["JWT_SECRET"])
_JWT_TTL    = _ENV["JWT_TTL_HOURS"]

_HMAC_PREAMBLE = (
    "const _sha256=(m)=>{const H=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];\n"
    "const K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];\n"
    "if(typeof m==='string')m=Buffer.from(m,'utf8');\n"
    "const L=m.length,ex=((L%64)<56?56:120)-(L%64),M=Buffer.alloc(L+ex+8);\n"
    "m.copy(M);M[L]=0x80;M.writeUInt32BE(L*8>>>0,M.length-4);\n"
    "const add=(a,b)=>(a+b)>>>0,r=(v,n)=>(v>>>n)|(v<<(32-n));\n"
    "for(let i=0;i<M.length;i+=64){const W=[];\n"
    "for(let j=0;j<16;j++)W[j]=M.readUInt32BE(i+j*4);\n"
    "for(let j=16;j<64;j++){const s0=r(W[j-15],7)^r(W[j-15],18)^(W[j-15]>>>3),s1=r(W[j-2],17)^r(W[j-2],19)^(W[j-2]>>>10);W[j]=add(add(add(W[j-16],s0),W[j-7]),s1);}\n"
    "let[a,b,c,d,e,f,g,hh]=H.slice();\n"
    "for(let j=0;j<64;j++){const T1=add(add(add(add(hh,r(e,6)^r(e,11)^r(e,25)),(e&f)^(~e&g)),K[j]),W[j]),T2=add(r(a,2)^r(a,13)^r(a,22),(a&b)^(a&c)^(b&c));hh=g;g=f;f=e;e=add(d,T1);d=c;c=b;b=a;a=add(T1,T2);}\n"
    "H[0]=add(H[0],a);H[1]=add(H[1],b);H[2]=add(H[2],c);H[3]=add(H[3],d);H[4]=add(H[4],e);H[5]=add(H[5],f);H[6]=add(H[6],g);H[7]=add(H[7],hh);}\n"
    "const res=Buffer.alloc(32);H.forEach((v,i)=>res.writeUInt32BE(v,i*4));return res;};\n"
    "const _hmac=(key,data)=>{if(typeof key==='string')key=Buffer.from(key,'utf8');if(typeof data==='string')data=Buffer.from(data,'utf8');if(key.length>64)key=_sha256(key);const kp=Buffer.alloc(64);key.copy(kp);const ik=Buffer.alloc(64),ok=Buffer.alloc(64);for(let i=0;i<64;i++){ik[i]=kp[i]^0x36;ok[i]=kp[i]^0x5c;}return _sha256(Buffer.concat([ok,_sha256(Buffer.concat([ik,data]))]));};\n"
)

JWT_VERIFY_CODE = (
    _HMAC_PREAMBLE +
    "const token = ($json.headers?.authorization || '').replace(/^Bearer /i, '').trim();\n"
    "if (!token) return [{ json: { ok: false, status: 401, error: 'missing_token', code: 'unauthorized' } }];\n"
    "const parts = token.split('.');\n"
    "if (parts.length !== 3) return [{ json: { ok: false, status: 401, error: 'malformed_token', code: 'unauthorized' } }];\n"
    "const [hp, pp, sp] = parts;\n"
    f"const expected = _hmac('{_JWT_SECRET}', hp + '.' + pp).toString('base64url');\n"
    "if (sp !== expected) return [{ json: { ok: false, status: 401, error: 'invalid_token', code: 'unauthorized' } }];\n"
    "let decoded;\n"
    "try { decoded = JSON.parse(Buffer.from(pp, 'base64url').toString()); }\n"
    "catch(e) { return [{ json: { ok: false, status: 401, error: 'malformed_payload', code: 'unauthorized' } }]; }\n"
    "if (decoded.exp && decoded.exp < Date.now() / 1000)\n"
    "  return [{ json: { ok: false, status: 401, error: 'token_expired', code: 'unauthorized' } }];\n"
    "return [{ json: { ok: true, user_id: decoded.sub, email: decoded.email } }];"
)

JWT_SIGN_CODE = (
    _HMAC_PREAMBLE +
    "const { user_id, email } = $json;\n"
    f"const ttl = {_JWT_TTL} * 3600;\n"
    "const now = Math.floor(Date.now() / 1000);\n"
    "const hp = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');\n"
    "const pp = Buffer.from(JSON.stringify({ sub: user_id, email, iat: now, exp: now + ttl })).toString('base64url');\n"
    f"const sig = _hmac('{_JWT_SECRET}', hp + '.' + pp).toString('base64url');\n"
    "return [{ json: { token: hp + '.' + pp + '.' + sig, user_id, email } }];"
)

ASSEMBLE_ROW_CODE = (
    "const generation_id = $json.generation_id || 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => { const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16); });\n"
    "return [{\n"
    "  json: {\n"
    "    generation_id,\n"
    "    user_id:              $json.user_id,\n"
    "    session_id:           $json.session_id || null,\n"
    "    parent_generation_id: $json.parent_generation_id || null,\n"
    "    kind:                 $json.kind,\n"
    "    input_image_path:     $json.input_image_path || null,\n"
    "    output_image_path:    `user-outputs/${$json.user_id}/${generation_id}.png`,\n"
    "    room_type:            $json.room_type || null,\n"
    "    style_tag:            $json.style_tag || null,\n"
    "    reference_image_ids:  $json.reference_image_ids || null,\n"
    "    prompt:               $json.prompt || null,\n"
    "    criteria:             $json.criteria || null,\n"
    "    model_config:         $json.model_config || 'A',\n"
    "    model_id:             $json.model_id || null,\n"
    "    latency_ms:           $json.latency_ms || null,\n"
    "    cost_usd:             $json.cost_usd || 0\n"
    "  },\n"
    "  binary: $input.first().binary\n"
    "}];"
)

# ── Node factories ────────────────────────────────────────────────────────────

def _new_id() -> str:
    return str(uuid.uuid4())[:8]


def code_node(name: str, code: str, x: int, y: int) -> dict:
    return {
        "id": _new_id(), "name": name,
        "type": "n8n-nodes-base.code", "typeVersion": 2,
        "position": [x, y],
        "parameters": {"jsCode": code},
    }


def http_node(name: str, params: dict, x: int, y: int) -> dict:
    return {
        "id": _new_id(), "name": name,
        "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
        "position": [x, y],
        "parameters": params,
    }


def _strip_n8n_expr(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, (int, float, bool)):
        return json.dumps(v)
    s = str(v).strip()
    if s.startswith("={{") and s.endswith("}}"):
        return s[3:-2].strip()
    if s.startswith("="):
        return s[1:]
    return json.dumps(s)

# ── Sub-workflow inliners ─────────────────────────────────────────────────────

def inline_jwt_verify(orig_node: dict) -> list:
    x, y = orig_node["position"]
    return [code_node("Verify JWT", JWT_VERIFY_CODE, x, y)]


def inline_jwt_sign(orig_node: dict) -> list:
    x, y = orig_node["position"]
    return [code_node("Sign JWT", JWT_SIGN_CODE, x, y)]


def inline_event_log(orig_node: dict) -> list:
    x, y = orig_node["position"]
    inputs = orig_node["parameters"].get("workflowInputs", {}).get("value", {})
    event_type = inputs.get("event_type", "unknown")
    u = _strip_n8n_expr(inputs.get("user_id"))
    s = _strip_n8n_expr(inputs.get("session_id"))
    p = _strip_n8n_expr(inputs.get("payload"))
    body_js = (
        f"={{{{ JSON.stringify({{ "
        f"user_id: {u}, "
        f"session_id: {s}, "
        f'event_type: "{event_type}", '
        f"payload: {p}"
        f" }}) }}}}"
    )
    params = {
        "method": "POST",
        "url": "={{ $('Config').first().json._cfg.supabase_url }}/rest/v1/events",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "apikey",        "value": "={{ $('Config').first().json._cfg.supabase_key }}"},
            {"name": "Authorization", "value": "=Bearer {{ $('Config').first().json._cfg.supabase_key }}"},
            {"name": "Content-Type",  "value": "application/json"},
            {"name": "Prefer",        "value": "return=minimal"},
        ]},
        "sendBody": True,
        "specifyBody": "string",
        "body": body_js,
        "options": {
            "timeout": 5000,
            "response": {"response": {"neverError": True}},
        },
    }
    return [http_node("Log event", params, x, y)]


def inline_save_generation(orig_node: dict) -> list:
    x, y = orig_node["position"]
    _supa_url = _js(_ENV["SUPABASE_URL"])

    asm = code_node("Assemble row", ASSEMBLE_ROW_CODE, x, y)

    upload_params = {
        "method": "POST",
        "url": "={{ $('Config').first().json._cfg.supabase_url + '/storage/v1/object/' + $json.output_image_path }}",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "apikey",        "value": "={{ $('Config').first().json._cfg.supabase_key }}"},
            {"name": "Authorization", "value": "=Bearer {{ $('Config').first().json._cfg.supabase_key }}"},
            {"name": "Content-Type",  "value": "image/png"},
            {"name": "x-upsert",      "value": "true"},
        ]},
        "sendBody": True,
        "contentType": "binaryData",
        "inputDataFieldName": "output_png",
        "options": {"timeout": 60000},
    }
    upload = http_node("Upload PNG", upload_params, x + 240, y)

    insert_params = {
        "method": "POST",
        "url": "={{ $('Config').first().json._cfg.supabase_url }}/rest/v1/generations",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "apikey",        "value": "={{ $('Config').first().json._cfg.supabase_key }}"},
            {"name": "Authorization", "value": "=Bearer {{ $('Config').first().json._cfg.supabase_key }}"},
            {"name": "Content-Type",  "value": "application/json"},
            {"name": "Prefer",        "value": "return=representation"},
        ]},
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "=JSON.stringify($('Assemble row').first().json)",
        "options": {"timeout": 15000},
    }
    insert = http_node("Insert generation row", insert_params, x + 480, y)

    build_code = (
        "const row = Array.isArray($json) ? $json[0]\n"
        "          : ($json.body ? (Array.isArray($json.body) ? $json.body[0] : $json.body) : $json);\n"
        "const asm  = $('Assemble row').first().json;\n"
        f"const base = '{_supa_url}';\n"
        "return [{ json: {\n"
        "  generation_id:        row?.id || asm.generation_id,\n"
        "  user_id:              asm.user_id,\n"
        "  session_id:           asm.session_id,\n"
        "  kind:                 asm.kind,\n"
        "  parent_generation_id: asm.parent_generation_id,\n"
        "  model_id:             asm.model_id,\n"
        "  latency_ms:           asm.latency_ms,\n"
        "  cost_usd:             asm.cost_usd || 0,\n"
        "  room_type:            asm.room_type,\n"
        "  style_tag:            asm.style_tag,\n"
        "  output_url:           base + '/storage/v1/object/public/' + asm.output_image_path,\n"
        "  created_at:           row?.created_at || new Date().toISOString()\n"
        "} }];"
    )
    build = code_node("Build gen response", build_code, x + 720, y)

    return [asm, upload, insert, build]

# ── Env baking ────────────────────────────────────────────────────────────────

def _bake_code_env(code: str) -> str:
    def rep(m):
        var = m.group(1)
        val = _ENV.get(var)
        return f"'{_js(val)}'" if val is not None else m.group(0)
    return re.sub(r"\$env\.([A-Z_]+)", rep, code)


def _replace_http_env(obj, cfg_name: str = "Config"):
    """Replace $env.VAR in HTTP node parameters with Config node lookup."""
    def rep(m):
        var = m.group(1)
        key = ENV_TO_CFG.get(var)
        return f"$('{cfg_name}').first().json._cfg.{key}" if key else m.group(0)

    def walk(o):
        if isinstance(o, str):
            return re.sub(r"\$env\.([A-Z_]+)", rep, o)
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(i) for i in o]
        return o

    return walk(obj)

# ── IF condition fixer ────────────────────────────────────────────────────────

def _fix_if_conditions(nodes: list):
    for node in nodes:
        if node["type"] != "n8n-nodes-base.if":
            continue
        params = node.get("parameters", {})
        conds  = params.get("conditions", {})
        opts   = conds.get("options", {})
        if "typeValidation" in opts:
            opts["typeValidation"] = "loose"
        for cond in conds.get("conditions", []):
            op = cond.get("operator", {})
            lv = cond.get("leftValue", "")
            if "_error" in str(lv) and op.get("operation") == "exists":
                cond["leftValue"]  = "={{ $json._error ? 'err' : '' }}"
                cond["rightValue"] = ""
                cond["operator"]   = {"type": "string", "operation": "notEmpty"}

# ── Core builder ──────────────────────────────────────────────────────────────

def build_workflow(source_path: Path, title: str) -> dict:
    """
    Build a standalone, deployable workflow from a source file.
    - executeWorkflow nodes are inlined
    - $env is baked into Code nodes
    - A Config node is injected for HTTP nodes that need credentials
    """
    with open(source_path, encoding="utf-8") as f:
        wf = json.load(f)

    orig_nodes   = wf["nodes"]
    orig_conns   = wf.get("connections", {})

    # ── Pass 1: expand nodes ──────────────────────────────────────────────────
    # name_map[orig] -> first-inline-name (for incoming connections)
    # last_map[orig] -> last-inline-name  (for outgoing connections)
    name_map: dict = {}
    last_map: dict = {}
    expanded: list = []   # [(orig_name, [nodes])]

    for node in orig_nodes:
        orig = node["name"]
        x, y = node["position"]
        wf_id = (node.get("parameters", {}).get("workflowId") or {}).get("value", "")

        if node["type"] == "n8n-nodes-base.executeWorkflow":
            if wf_id == "wf_jwt_verify":
                inline = inline_jwt_verify(node)
            elif wf_id == "wf_jwt_sign":
                inline = inline_jwt_sign(node)
            elif wf_id == "wf_event_log":
                inline = inline_event_log(node)
            elif wf_id == "wf_save_generation":
                inline = inline_save_generation(node)
            else:
                new_node = deepcopy(node)
                new_node["id"] = _new_id()
                inline = [new_node]
        else:
            new_node = deepcopy(node)
            new_node["id"] = _new_id()
            inline = [new_node]

        name_map[orig] = inline[0]["name"]
        last_map[orig] = inline[-1]["name"]
        expanded.append((orig, inline))

    # ── Pass 2: bake $env in Code nodes ──────────────────────────────────────
    for _orig, inline in expanded:
        for n in inline:
            if n["type"] == "n8n-nodes-base.code":
                code = n["parameters"].get("jsCode", "")
                if "$env." in code:
                    n["parameters"]["jsCode"] = _bake_code_env(code)

    # ── Pass 3: collect all nodes ─────────────────────────────────────────────
    all_nodes: list = []
    for _orig, inline in expanded:
        all_nodes.extend(inline)

    # ── Pass 4: internal chains for multi-node replacements ───────────────────
    all_connections: dict = {}
    for _orig, inline in expanded:
        if len(inline) <= 1:
            continue
        for i in range(len(inline) - 1):
            src = inline[i]["name"]
            dst = inline[i + 1]["name"]
            all_connections.setdefault(src, {})
            all_connections[src]["main"] = [[{"node": dst, "type": "main", "index": 0}]]

    # ── Pass 5: remap original connections ───────────────────────────────────
    for src_orig, conns in orig_conns.items():
        src_new = last_map.get(src_orig, src_orig)
        all_connections.setdefault(src_new, {})
        for conn_type, outputs in conns.items():
            if conn_type in all_connections[src_new]:
                continue  # internal chain owns this slot
            new_outputs = []
            for output in outputs:
                new_out = []
                for c in output:
                    dst_new = name_map.get(c["node"], c["node"])
                    new_out.append({"node": dst_new, "type": c["type"], "index": c["index"]})
                new_outputs.append(new_out)
            all_connections[src_new][conn_type] = new_outputs

    # ── Pass 6: inject Config node + replace $env in HTTP nodes ──────────────
    has_env_in_http = any(
        "$env." in json.dumps(n["parameters"])
        for n in all_nodes if n["type"] == "n8n-nodes-base.httpRequest"
    )

    if has_env_in_http:
        trigger_types = {"n8n-nodes-base.webhook", "n8n-nodes-base.manualTrigger"}
        trigger_name = next(
            (n["name"] for n in all_nodes if n["type"] in trigger_types), None
        )
        if trigger_name:
            trigger_pos = next(
                (n["position"] for n in all_nodes if n["name"] == trigger_name), [240, 300]
            )
            cfg_node = code_node("Config", CONFIG_CODE, trigger_pos[0] + 240, trigger_pos[1])

            # Reroute trigger -> Config -> (old trigger targets)
            old_conns = all_connections.pop(trigger_name, {})
            all_connections[trigger_name] = {
                "main": [[{"node": "Config", "type": "main", "index": 0}]]
            }
            all_connections["Config"] = old_conns

            # Insert Config node right after trigger
            idx = next(
                (i for i, n in enumerate(all_nodes) if n["name"] == trigger_name),
                len(all_nodes)
            )
            all_nodes.insert(idx + 1, cfg_node)

        # Replace $env in all HTTP nodes
        for n in all_nodes:
            if n["type"] == "n8n-nodes-base.httpRequest":
                n["parameters"] = _replace_http_env(n["parameters"])

    # ── Pass 7: fix IF _error conditions ─────────────────────────────────────
    _fix_if_conditions(all_nodes)

    return {
        "name":        title,
        "nodes":       all_nodes,
        "connections": all_connections,
        "active":      False,
        "settings":    {"executionOrder": "v1"},
        "pinData":     {},
    }

# ── n8n API helpers ───────────────────────────────────────────────────────────

def _api(method: str, path: str, body: dict = None) -> dict:
    url  = f"{N8N_BASE}/api/v1{path}"
    data = json.dumps(body).encode() if body is not None else None
    req  = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "X-N8N-API-KEY":  N8N_API_KEY,
            "Content-Type":   "application/json",
        }
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {e.read().decode()[:300]}")


def list_workflows() -> dict:
    """Returns {title: id} for all workflows currently in n8n."""
    data = _api("GET", "/workflows?limit=100")
    return {wf["name"]: wf["id"] for wf in data.get("data", [])}


def deploy(wf_dict: dict, existing_id: str = None) -> str:
    """Create or update a workflow. Returns the workflow id."""
    body = {
        "name":        wf_dict["name"],
        "nodes":       wf_dict["nodes"],
        "connections": wf_dict["connections"],
        "settings":    wf_dict.get("settings", {}),
    }
    if existing_id:
        result = _api("PUT", f"/workflows/{existing_id}", body)
    else:
        result = _api("POST", "/workflows", body)
    return result["id"]


def activate(wf_id: str):
    _api("POST", f"/workflows/{wf_id}/activate")


def deactivate(wf_id: str):
    _api("POST", f"/workflows/{wf_id}/deactivate")

# ── Workflow list ─────────────────────────────────────────────────────────────
# (filename, title)

WORKFLOWS = [
    ("health.json",
     "Health Check  (GET /health -> status ok)"),

    ("auth_magic_link.json",
     "Magic-Link Login  (email -> token + user_id)"),

    ("auth_me.json",
     "Auth Me  (Bearer token -> user_id + email)"),

    ("uploads_room_photo.json",
     "Upload Room Photo  (image file -> upload_id + preview_url)"),

    ("retrieve_references.json",
     "Retrieve References  (upload_id + k -> top-k reference images)"),

    ("generate_draft.json",
     "Generate Draft  (upload + refs + style -> design image)"),

    ("generate_edit.json",
     "Generate Edit  (generation_id + instruction -> edited image)"),

    ("generate_commit.json",
     "Generate Commit  (parent_generation_id -> final image)"),

    ("generate_orchestrated.json",
     "Generate Orchestrated  (upload_id + brief -> AI-picked design)"),

    ("generations_session.json",
     "Session History  (session_id -> generations list)"),

    ("generations_export.json",
     "Generation Export  (generation_id -> download_url)"),

    ("admin_metrics.json",
     "Admin Metrics  (admin_token -> usage stats)"),

    ("_seed_nemotron_references.json",
     "Seed Embeddings  (manual trigger -> 104 reference embeddings)"),
]

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Fetching existing workflows from n8n ...")
    existing = list_workflows()

    # Step 1: deactivate the consolidated workflow so it releases the webhooks
    if CONSOLIDATED_WF_ID in existing.values():
        print(f"Deactivating consolidated workflow ({CONSOLIDATED_WF_ID}) ...")
        try:
            deactivate(CONSOLIDATED_WF_ID)
            print("  Consolidated workflow deactivated.")
        except RuntimeError as e:
            print(f"  Warning: could not deactivate consolidated — {e}")
    else:
        print("Consolidated workflow not found by ID — skipping deactivation.")

    # Step 2: build, deploy, and activate each individual workflow
    print()
    deployed_ids = {}
    for filename, title in WORKFLOWS:
        path = WF_DIR / filename
        if not path.exists():
            print(f"  SKIP (not found): {filename}")
            continue

        print(f"Building  [{title}] ...")
        try:
            wf_dict = build_workflow(path, title)
        except Exception as e:
            print(f"  ERROR building: {e}")
            continue

        existing_id = existing.get(title)
        action = "Updating" if existing_id else "Creating"
        print(f"  {action} in n8n ...")
        try:
            wf_id = deploy(wf_dict, existing_id)
            print(f"  Activating ({wf_id}) ...")
            activate(wf_id)
            deployed_ids[title] = wf_id
            print(f"  OK  {wf_id}")
        except RuntimeError as e:
            print(f"  ERROR deploying/activating: {e}")

    print(f"\nDone. {len(deployed_ids)}/{len(WORKFLOWS)} workflows deployed and active.")
    for title, wf_id in deployed_ids.items():
        print(f"  {wf_id}  {title}")
