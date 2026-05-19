#!/usr/bin/env python3
"""
Merge all Interior Design RAG n8n workflows into one "INTERIOR DESIGN RAG" workflow.

Usage (from project root):
    python n8n/build_consolidated.py

Outputs:  n8n/workflows/interior_design_rag_consolidated.json
"""
import json
import os
import re
import uuid
from copy import deepcopy
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

PROJECT  = Path(__file__).parent.parent
WF_DIR   = PROJECT / "n8n" / "workflows"
OUT_FILE = WF_DIR  / "interior_design_rag_consolidated.json"

SEP = "::"   # namespace separator in node names  e.g.  "draft::Validate body"

# ── Runtime credentials (baked in at build time — no $env needed) ─────────────

def _load_env() -> dict:
    """Load credentials from project .env file and Windows environment variables."""
    file_env: dict = {}
    env_path = PROJECT / ".env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                file_env[k.strip()] = v.strip()

    def get(key: str, *alt_keys, default: str = "") -> str:
        for k in (key,) + alt_keys:
            if v := os.environ.get(k):
                return v
        for k in (key,) + alt_keys:
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
        "SUPABASE_ANON_KEY":             get("SUPABASE_ANON_KEY"),
        "ADMIN_TOKEN":                   get("ADMIN_TOKEN", "Admin Token"),
    }

_ENV = _load_env()

# ── Environment variable mapping (for HTTP node expression replacement) ───────

# Maps n8n $env.VAR_NAME → key inside the _cfg object
ENV_TO_CFG: dict = {
    "SUPABASE_URL":                  "supabase_url",
    "SUPABASE_SERVICE_KEY":          "supabase_key",
    "GEMINI_API_KEY":                "gemini_key",
    "OPENROUTER_API_KEY":            "openrouter_key",
    "OPENROUTER_BASE_URL":           "openrouter_base",
    "OPENROUTER_ORCHESTRATOR_MODEL": "orch_model",
    "OPENROUTER_RETRIEVER_MODEL":    "retriever_model",
    "OPENROUTER_EMBED_MODEL":        "embed_model",
    "SUPABASE_ANON_KEY":             "supabase_anon_key",
    "ADMIN_TOKEN":                   "admin_token",
}

def _js(s: str) -> str:
    """Escape a Python string as a JS single-quoted string literal."""
    return s.replace("\\", "\\\\").replace("'", "\\'")

# Config Code node bakes all credentials in — no $env access needed at runtime.
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
    f"      supabase_anon_key: '{_js(_ENV['SUPABASE_ANON_KEY'])}',\n"
    f"      admin_token:     '{_js(_ENV['ADMIN_TOKEN'])}'\n"
    "    }\n"
    "  },\n"
    "  binary: $input.first().binary || {}\n"
    "}];"
)

# Supabase verify normalizer — runs after HTTP Request to /auth/v1/user
_SUPABASE_VERIFY_NORMALIZE = (
    "const status = $json.statusCode || $json.status || 200;\n"
    "if (status !== 200 || !$json.id) {\n"
    "  return [{ json: { ok: false, status: 401, error: $json.error_description || 'invalid_token', code: 'invalid_token' } }];\n"
    "}\n"
    "return [{ json: { ok: true, user_id: $json.id, email: $json.email || null } }];"
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

# ── Helpers ──────────────────────────────────────────────────────────────────

def new_id() -> str:
    return str(uuid.uuid4())[:8]


def strip_n8n_expr(v) -> str:
    """Convert an n8n expression value (={{ … }} or =…) to a raw JS expression."""
    if v is None:
        return "null"
    if isinstance(v, (int, float, bool)):
        return json.dumps(v)
    s = str(v).strip()
    if s.startswith("={{") and s.endswith("}}"):
        return s[3:-2].strip()
    if s.startswith("="):
        return s[1:]
    # plain string literal — wrap in JSON quotes
    return json.dumps(s)


def update_node_refs(obj, name_map: dict):
    """
    Recursively walk obj and replace $('OldName') / $("OldName")
    with the namespaced node name from name_map.
    """
    if isinstance(obj, str):
        def _rep(m):
            q    = m.group(1)
            old  = m.group(2)
            new  = name_map.get(old, old)
            return f"$('{new}')" if q == "'" else f'$("{new}")'
        return re.sub(r"\$\((['\"])(.+?)\1\)", _rep, obj)
    if isinstance(obj, dict):
        return {k: update_node_refs(v, name_map) for k, v in obj.items()}
    if isinstance(obj, list):
        return [update_node_refs(item, name_map) for item in obj]
    return obj


def code_node(name: str, code: str, x: int, y: int) -> dict:
    return {
        "id": new_id(), "name": name,
        "type": "n8n-nodes-base.code", "typeVersion": 2,
        "position": [x, y],
        "parameters": {"jsCode": code},
    }


def http_node(name: str, params: dict, x: int, y: int) -> dict:
    return {
        "id": new_id(), "name": name,
        "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2,
        "position": [x, y],
        "parameters": params,
    }

# ── Sub-workflow inline factories ────────────────────────────────────────────

_SUPA_URL = _js(_ENV["SUPABASE_URL"])
_SUPA_ANON = _js(_ENV["SUPABASE_ANON_KEY"])

def inline_supabase_verify(name: str, x: int, y: int) -> list:
    """Inline wf_supabase_verify: HTTP Request to /auth/v1/user + normalize."""
    http_name = name + " (HTTP)"
    http_params = {
        "method": "GET",
        "url": f"{_ENV['SUPABASE_URL']}/auth/v1/user",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "Authorization", "value": "={{ $json.authorization || ($json.headers && $json.headers.authorization) || '' }}"},
            {"name": "apikey",        "value": _ENV["SUPABASE_ANON_KEY"]},
        ]},
        "options": {
            "timeout": 10000,
            "response": {"response": {"neverError": True}},
        },
    }
    normalize = code_node(name, _SUPABASE_VERIFY_NORMALIZE, x + 240, y)
    return [http_node(http_name, http_params, x, y), normalize]


def inline_event_log(name: str, inputs: dict, x: int, y: int) -> list:
    event_type = inputs.get("event_type", "unknown")
    u = strip_n8n_expr(inputs.get("user_id"))
    s = strip_n8n_expr(inputs.get("session_id"))
    p = strip_n8n_expr(inputs.get("payload"))
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
        "url": "={{$env.SUPABASE_URL}}/rest/v1/events",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "apikey",        "value": "={{$env.SUPABASE_SERVICE_KEY}}"},
            {"name": "Authorization", "value": "=Bearer {{$env.SUPABASE_SERVICE_KEY}}"},
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
    return [http_node(name, params, x, y)]


def inline_save_generation(ns: str, x: int, y: int) -> list:
    """Return 4 nodes that replace wf_save_generation."""
    asm_name    = f"{ns}{SEP}Assemble row"
    upload_name = f"{ns}{SEP}Upload PNG"
    insert_name = f"{ns}{SEP}Insert generation row"
    build_name  = f"{ns}{SEP}Build gen response"

    asm_node = code_node(asm_name, ASSEMBLE_ROW_CODE, x, y)

    upload_params = {
        "method": "POST",
        "url": "={{ $env.SUPABASE_URL + '/storage/v1/object/' + $json.output_image_path }}",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "apikey",        "value": "={{$env.SUPABASE_SERVICE_KEY}}"},
            {"name": "Authorization", "value": "=Bearer {{$env.SUPABASE_SERVICE_KEY}}"},
            {"name": "Content-Type",  "value": "image/png"},
            {"name": "x-upsert",      "value": "true"},
        ]},
        "sendBody": True,
        "contentType": "binaryData",
        "inputDataFieldName": "output_png",
        "options": {"timeout": 60000},
    }
    upload_node_obj = http_node(upload_name, upload_params, x + 240, y)

    insert_params = {
        "method": "POST",
        "url": "={{$env.SUPABASE_URL}}/rest/v1/generations",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "apikey",        "value": "={{$env.SUPABASE_SERVICE_KEY}}"},
            {"name": "Authorization", "value": "=Bearer {{$env.SUPABASE_SERVICE_KEY}}"},
            {"name": "Content-Type",  "value": "application/json"},
            {"name": "Prefer",        "value": "return=representation"},
        ]},
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": f'=JSON.stringify($("{asm_name}").first().json)',
        "options": {"timeout": 15000},
    }
    insert_node_obj = http_node(insert_name, insert_params, x + 480, y)

    _supa_url = _js(_ENV["SUPABASE_URL"])
    build_code = (
        "const row = Array.isArray($json) ? $json[0]\n"
        "          : ($json.body ? (Array.isArray($json.body) ? $json.body[0] : $json.body) : $json);\n"
        f'const asm  = $("{asm_name}").first().json;\n'
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
    build_node_obj = code_node(build_name, build_code, x + 720, y)

    return [asm_node, upload_node_obj, insert_node_obj, build_node_obj]

# ── Merger ───────────────────────────────────────────────────────────────────

class WorkflowMerger:
    def __init__(self):
        self.all_nodes: list        = []
        self.all_connections: dict  = {}

    def add_workflow(self, path: Path, ns: str, y_offset: int):
        with open(path, encoding="utf-8") as f:
            wf = json.load(f)

        nodes       = wf["nodes"]
        connections = wf["connections"]

        # ── Pass 1: expand nodes, build name maps ──────────────────────────
        # name_map[orig]      → first inline node name  (incoming connections point here)
        # last_map[orig]      → last inline node name   (outgoing connections leave here)
        # expanded: list of (orig_name, [new_node, ...])

        name_map: dict  = {}
        last_map: dict  = {}
        expanded: list  = []

        for node in nodes:
            orig  = node["name"]
            x, y  = node["position"]
            ny    = y + y_offset
            nname = f"{ns}{SEP}{orig}"

            if node["type"] == "n8n-nodes-base.executeWorkflow":
                wf_id  = node["parameters"]["workflowId"]["value"]
                inputs = node["parameters"].get("workflowInputs", {}).get("value", {})

                if wf_id in ("56BlN6jqFkXVszX2", "wf_supabase_verify", "wf_jwt_verify", "iPfGe1kcq5Uz1bLV", "PN5YANsmuOGA6qGe"):
                    inline = inline_supabase_verify(nname, x, ny)
                elif wf_id == "wf_event_log":
                    inline = inline_event_log(nname, inputs, x, ny)
                elif wf_id == "wf_save_generation":
                    inline = inline_save_generation(ns, x, ny)
                else:
                    print(f"  WARN: unknown sub-workflow '{wf_id}' in '{orig}' — keeping as execute node")
                    new_node = deepcopy(node)
                    new_node["id"]       = new_id()
                    new_node["name"]     = nname
                    new_node["position"] = [x, ny]
                    inline = [new_node]

            else:
                new_node = deepcopy(node)
                new_node["id"]       = new_id()
                new_node["name"]     = nname
                new_node["position"] = [x, ny]
                inline = [new_node]

            name_map[orig] = inline[0]["name"]
            last_map[orig] = inline[-1]["name"]
            expanded.append((orig, inline))

        # ── Pass 2: update $('OldName') refs in parameters ──────────────
        for _orig, inline in expanded:
            for node in inline:
                node["parameters"] = update_node_refs(node["parameters"], name_map)

        # ── Pass 3: accumulate nodes ──────────────────────────────────────
        for _orig, inline in expanded:
            self.all_nodes.extend(inline)

        # ── Pass 4: internal chains for multi-node replacements ───────────
        for _orig, inline in expanded:
            if len(inline) <= 1:
                continue
            for i in range(len(inline) - 1):
                src = inline[i]["name"]
                dst = inline[i + 1]["name"]
                self.all_connections.setdefault(src, {})
                self.all_connections[src]["main"] = [[{"node": dst, "type": "main", "index": 0}]]

        # ── Pass 5: rebuild original connections ──────────────────────────
        for src_orig, conns in connections.items():
            src_new = last_map.get(src_orig, f"{ns}{SEP}{src_orig}")
            self.all_connections.setdefault(src_new, {})
            for conn_type, outputs in conns.items():
                if conn_type in self.all_connections[src_new]:
                    # already set by internal chain — skip to avoid overwriting
                    continue
                new_outputs = []
                for output in outputs:
                    new_out = []
                    for c in output:
                        dst_orig = c["node"]
                        dst_new  = name_map.get(dst_orig, f"{ns}{SEP}{dst_orig}")
                        new_out.append({"node": dst_new, "type": c["type"], "index": c["index"]})
                    new_outputs.append(new_out)
                self.all_connections[src_new][conn_type] = new_outputs

        # ── Pass 6: inject Config node + replace $env in HTTP nodes ──────
        # Only do this when the branch has HTTP nodes that actually reference $env.
        # Branches like "health" have no env refs and must NOT get a Config node —
        # n8n's task runner sandbox blocks $env, so inserting it would crash them.
        ns_http_params = json.dumps([
            n["parameters"] for n in self.all_nodes
            if n["type"] == "n8n-nodes-base.httpRequest"
            and n["name"].startswith(f"{ns}{SEP}")
        ])
        # Always bake $env in Code nodes (sandbox blocks $env in Code nodes)
        self._replace_env_in_code_nodes(ns)

        if re.search(r"\$env\.", ns_http_params):
            trigger_types = {"n8n-nodes-base.webhook", "n8n-nodes-base.manualTrigger"}
            trigger_orig = next(
                (n["name"] for n in nodes if n["type"] in trigger_types), None
            )
            if trigger_orig:
                trigger_new = name_map.get(trigger_orig, f"{ns}{SEP}{trigger_orig}")
                cfg_name = self._insert_config_node(ns, trigger_new)
                self._replace_env_in_http_nodes(ns, cfg_name)

    def _insert_config_node(self, ns: str, trigger_new_name: str):
        """
        Insert a Config Code node between the trigger and its first child.
        The Config node reads all $env vars into $json._cfg so downstream
        HTTP nodes can use $json._cfg.X instead of the blocked $env.X.
        """
        cfg_name = f"{ns}{SEP}Config"

        # Find the trigger node's canvas position
        trigger_pos = next(
            (n["position"] for n in self.all_nodes if n["name"] == trigger_new_name),
            [240, 0]
        )
        cfg_node = code_node(cfg_name, CONFIG_CODE, trigger_pos[0] + 240, trigger_pos[1])

        # Intercept the trigger's outgoing connections → reroute through Config
        old_trigger_conns = self.all_connections.pop(trigger_new_name, {})
        self.all_connections[trigger_new_name] = {
            "main": [[{"node": cfg_name, "type": "main", "index": 0}]]
        }
        self.all_connections[cfg_name] = old_trigger_conns

        # Insert into node list right after the trigger
        idx = next(
            (i for i, n in enumerate(self.all_nodes) if n["name"] == trigger_new_name),
            len(self.all_nodes)
        )
        self.all_nodes.insert(idx + 1, cfg_node)
        return cfg_name

    def _replace_env_in_code_nodes(self, ns: str):
        """
        For Code nodes in namespace `ns` (from source workflows, not inline templates):
        replace $env.VAR with the baked literal value so the sandbox never needs $env.
        """
        def bake(s: str) -> str:
            def rep(m):
                var = m.group(1)
                val = _ENV.get(var)
                if val is not None:
                    return f"'{_js(val)}'"
                return m.group(0)
            return re.sub(r"\$env\.([A-Z_]+)", rep, s)

        for node in self.all_nodes:
            if node["type"] != "n8n-nodes-base.code":
                continue
            if not node["name"].startswith(f"{ns}{SEP}"):
                continue
            code = node["parameters"].get("jsCode", "")
            if "$env." in code:
                node["parameters"]["jsCode"] = bake(code)

    def _replace_env_in_http_nodes(self, ns: str, cfg_name: str):
        """
        For HTTP Request nodes in namespace `ns`: replace $env.VAR with
        $('cfg_name').first().json._cfg.varkey so env vars work even when
        N8N_BLOCK_ENV_ACCESS_IN_NODE=true (the default in newer n8n).
        """
        def replace_env(s: str) -> str:
            def rep(m):
                var = m.group(1)
                key = ENV_TO_CFG.get(var)
                if key:
                    return f"$('{cfg_name}').first().json._cfg.{key}"
                return m.group(0)
            return re.sub(r"\$env\.([A-Z_]+)", rep, s)

        def walk(obj):
            if isinstance(obj, str):
                return replace_env(obj)
            if isinstance(obj, dict):
                return {k: walk(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [walk(item) for item in obj]
            return obj

        for node in self.all_nodes:
            if node["type"] != "n8n-nodes-base.httpRequest":
                continue
            if not node["name"].startswith(f"{ns}{SEP}"):
                continue
            node["parameters"] = walk(node["parameters"])

    def _fix_if_conditions(self):
        """
        n8n IF v2 throws "can't be converted to object" when checking
        $json._error with operator {type:'object', operation:'exists'}
        because undefined evaluates to '' in n8n expressions.

        Fix: replace every such condition with a string-truthy check:
          leftValue  = "={{ $json._error ? 'err' : '' }}"
          rightValue = ""
          operator   = {type:'string', operation:'notEmpty'}
        """
        for node in self.all_nodes:
            if node["type"] != "n8n-nodes-base.if":
                continue
            params = node.get("parameters", {})
            conds  = params.get("conditions", {})
            opts   = conds.get("options", {})
            # relax typeValidation as a belt-and-suspenders measure
            if "typeValidation" in opts:
                opts["typeValidation"] = "loose"
            for cond in conds.get("conditions", []):
                op = cond.get("operator", {})
                lv = cond.get("leftValue", "")
                # Target: leftValue references _error, operator is object-exists
                if "_error" in str(lv) and op.get("operation") == "exists":
                    cond["leftValue"]  = "={{ $json._error ? 'err' : '' }}"
                    cond["rightValue"] = ""
                    cond["operator"]   = {"type": "string", "operation": "notEmpty"}

    def build(self, name: str = "INTERIOR DESIGN RAG") -> dict:
        self._fix_if_conditions()
        # ── Validation ─────────────────────────────────────────────────────
        node_names = [n["name"] for n in self.all_nodes]
        dupes = {n for n in node_names if node_names.count(n) > 1}
        if dupes:
            print(f"  WARNING duplicate node names: {dupes}")
        else:
            print(f"  Node names  : {len(node_names)} unique OK")

        exec_remaining = [n for n in self.all_nodes if n["type"] == "n8n-nodes-base.executeWorkflow"]
        if exec_remaining:
            print(f"  WARNING executeWorkflow nodes remain: {[n['name'] for n in exec_remaining]}")
        else:
            print("  Execute WF nodes : 0 remaining OK")

        node_ids = [n["id"] for n in self.all_nodes]
        if len(node_ids) != len(set(node_ids)):
            print("  WARNING duplicate node IDs!")
        else:
            print(f"  Node IDs    : {len(node_ids)} unique OK")

        return {
            "name":        name,
            "nodes":       self.all_nodes,
            "connections": self.all_connections,
            "active":      False,
            "settings":    {"executionOrder": "v1"},
            "pinData":     {},
        }

# ── Workflow list ─────────────────────────────────────────────────────────────
# (filename, namespace, y_offset)

WORKFLOWS = [
    ("health.json",                "health",    0),
    ("auth_me.json",               "auth-me",   1200),
    ("uploads_room_photo.json",    "upload",    2400),
    ("uploads_reference_bulk.json","ref-bulk",  3600),
    ("generate_edit.json",         "edit",      4800),
    ("generate_commit.json",       "commit",    6000),
    ("generate_orchestrated.json", "orch",      7200),
    ("generations_session.json",   "gen-sess",  8400),
    ("generations_export.json",    "gen-exp",   9600),
    ("admin_metrics.json",         "admin",     10800),
]

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    merger = WorkflowMerger()

    for filename, ns, y_offset in WORKFLOWS:
        path = WF_DIR / filename
        if not path.exists():
            print(f"SKIP (not found): {filename}")
            continue
        print(f"[{ns}] {filename}  (y+{y_offset})")
        merger.add_workflow(path, ns, y_offset)

    print("\nBuilding consolidated workflow …")
    result = merger.build()

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nOutput : {OUT_FILE}")
    print(f"Nodes  : {len(result['nodes'])}")
    print(f"Conns  : {len(result['connections'])}")
