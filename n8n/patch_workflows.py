#!/usr/bin/env python3
"""
Patches retrieve_references and generate_draft workflows to add prompt support.
  - retrieve_references: accepts prompt, LLM re-ranks references by prompt relevance
  - generate_draft: accepts prompt, injects it into the Gemini instruction
Pushes changes directly to the live n8n instance via REST API.
"""
import json, urllib.request, urllib.error, copy

N8N_BASE = "http://localhost:5678/api/v1"
N8N_KEY  = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiJmMGYzMzNlNi1jNTM0LTQxMDYtYWE0ZS1lZDdkMTIzNDE5YWMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiZDk3MGQzOTMtMjMzYi00YTMxLWIzODUtMzA4Nzg3ODk4NGE2IiwiaWF0IjoxNzc3MDAzMTQyLCJleHAiOjE3Nzk1MDg4MDB9"
    ".7BxoC8bG6LIKExWd_Jnuuct4y50xfNTiLoVFZe8dcfY"
)

HEADERS = {"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"}

def api_get(path):
    req = urllib.request.Request(f"{N8N_BASE}{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def api_put(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{N8N_BASE}{path}", data=body, headers=HEADERS, method="PUT")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# ─── NEW CODE STRINGS ────────────────────────────────────────────────────────

RETRIEVE_VALIDATE_BODY_JS = """\
const _raw = $('POST /retrieve/references').first().json.body || {};
const body = (() => {
  const keys = Object.keys(_raw);
  if (keys.length === 1 && String(keys[0]).trimStart().startsWith('{')) {
    try { return JSON.parse(keys[0]); } catch (_) {}
  }
  return _raw;
})();
const user_id = $json.user_id;
const cfg = $('Config').first().json._cfg;

const upload_id = (body.upload_id || '').toString().trim();
if (!upload_id) {
  return [{ json: { _error: { status: 400, body: { error: 'missing_upload_id', code: 'invalid_request' } } } }];
}

const k         = Math.min(Math.max(parseInt(body.k || 5, 10), 1), 20);
const room_type = body.room_type ? body.room_type.toString() : null;
const style_tag = body.style_tag ? body.style_tag.toString() : null;
const prompt    = body.prompt ? body.prompt.toString().trim() : null;

const storage_path = `user-uploads/${user_id}/${upload_id}`;
const upload_url   = `${cfg.supabase_url}/storage/v1/object/${storage_path}`;
const public_url   = `${cfg.supabase_url}/storage/v1/object/public/${storage_path}`;

return [{ json: { user_id, upload_id, k, room_type, style_tag, prompt, upload_url, public_url } }];\
"""

PROMPT_RERANK_JS = """\
const ctx   = $('Validate body').first().json;
const prompt = ctx.prompt;
const refs  = $input.all().map(i => i.json);

if (!prompt || !prompt.trim() || refs.length === 0) {
  return refs.map(r => ({ json: r }));
}

const cfg = $('Config').first().json._cfg;
const candidateList = refs.map((r, idx) => {
  const tags = Array.isArray(r.style_tags) ? r.style_tags.join(', ') : (r.style_tags || '');
  return `[${idx}] style: ${tags} | room: ${r.room_type || ''} | caption: ${r.caption || ''}`;
}).join('\\n');

const llmBody = {
  model: cfg.retriever_model || cfg.orch_model || 'google/gemini-2.5-flash',
  messages: [{
    role: 'user',
    content: `You are an interior design reference selector.\\n\\nUSER BRIEF: "${prompt}"\\n\\nCANDIDATE REFERENCES:\\n${candidateList}\\n\\nReturn ONLY a JSON array of indices ordered by relevance to the user brief, most relevant first. Example: [2,0,4,1,3]. No explanation, no markdown, no code fences.`
  }],
  max_tokens: 80,
  temperature: 0
};

let rerankedRefs = refs;
try {
  const llmResp = await this.helpers.httpRequest({
    method: 'POST',
    url: (cfg.openrouter_base || 'https://openrouter.ai/api/v1') + '/chat/completions',
    headers: {
      Authorization: 'Bearer ' + cfg.openrouter_key,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(llmBody),
    encoding: 'utf8'
  });
  const parsed = typeof llmResp === 'string' ? JSON.parse(llmResp) : llmResp;
  const rawContent = (parsed.choices?.[0]?.message?.content || '').trim();
  const match = rawContent.match(/\\[[\\d,\\s]+\\]/);
  if (match) {
    const order = JSON.parse(match[0]);
    const seen = new Set(order);
    const reordered = order.filter(i => refs[i] !== undefined).map(i => refs[i]);
    for (let i = 0; i < refs.length; i++) {
      if (!seen.has(i)) reordered.push(refs[i]);
    }
    rerankedRefs = reordered;
  }
} catch (_) {}

return rerankedRefs.map(r => ({ json: r }));\
"""

COLLECT_REFS_JS = """\
const ctx = $('Validate body').first().json;
if (!ctx.room_type || !ctx.style_tag) return [];

const refs = $input.all().map(i => i.json);
const orig = $('POST /retrieve/references').first().json;
const auth = (orig.headers || {}).authorization || '';
const session_id = ((orig.body || {}).session_id) || null;

return [{ json: {
  upload_id:     ctx.upload_id,
  room_type:     ctx.room_type,
  style_tag:     ctx.style_tag,
  prompt:        ctx.prompt || null,
  reference_ids: refs.map(r => r.id).filter(Boolean),
  session_id,
  _auth:         auth
} }];\
"""

DRAFT_VALIDATE_BODY_JS = """\
const _raw = $('POST /generate/draft').item.json.body || {};
const body = (() => {
  const keys = Object.keys(_raw);
  if (keys.length === 1 && String(keys[0]).trimStart().startsWith('{')) {
    try { return JSON.parse(keys[0]); } catch (_) {}
  }
  return _raw;
})();
const user_id = $json.user_id;

const upload_id   = (body.upload_id || '').toString().trim();
const room_type   = (body.room_type || '').toString().trim();
const style_tag   = (body.style_tag || '').toString().trim();
const reference_ids = Array.isArray(body.reference_ids) ? body.reference_ids : [];
const session_id  = body.session_id ? body.session_id.toString() : null;
const prompt      = body.prompt ? body.prompt.toString().trim() : null;

const missing = [];
if (!upload_id) missing.push('upload_id');
if (missing.length) {
  return [{ json: { _error: { status: 400, body: { error: `missing_fields: ${missing.join(',')}`, code: 'invalid_request' } } } }];
}

const storage_path = `user-uploads/${user_id}/${upload_id}`;
const upload_url   = `${'https://uzghfpxboktnbcbbthns.supabase.co'}/storage/v1/object/${storage_path}`;

return [{ json: { user_id, upload_id, room_type, style_tag, prompt, reference_ids, session_id, upload_url, started_at_ms: Date.now() } }];\
"""

BUILD_GEMINI_JS = """\
// $json is the single row from Fetch image_model: {value: 'model-name'}
const model = $json.value || 'gemini-3.1-flash-image-preview';

const template = `You are an interior design rendering engine.

TASK: Generate a photorealistic image of the SAME room shown in the first input
image, redesigned in the style of the reference images provided.

HARD CONSTRAINTS:
- Preserve the input room's geometry exactly: wall positions, window positions
  and sizes, door positions, ceiling height.
- Preserve lighting direction from the input photo.
- Use furniture, materials, colors, and styling cues from the reference images.
- Output must be photorealistic, no illustrations or cartoons.
- Do not add text, watermarks, logos, or signatures.
- Do not add people.

STYLE: {style_tag}
ROOM TYPE: {room_type}
{user_brief}`;

const ctx = $('Collect image parts').first().json;
const userBriefSection = ctx.prompt
  ? `\\nUSER BRIEF (incorporate into the design):\\n${ctx.prompt}`
  : '';
const finalPrompt = template
  .replace('{style_tag}', ctx.style_tag || 'not specified')
  .replace('{room_type}', ctx.room_type || 'not specified')
  .replace('{user_brief}', userBriefSection);

const gemini_body = {
  contents: [{
    role: 'user',
    parts: [ { text: finalPrompt }, ...ctx.image_parts ]
  }],
  generationConfig: { responseModalities: ['IMAGE'] }
};

return [{ json: { ...ctx, model, prompt: finalPrompt, gemini_body } }];\
"""

# ─── PATCH retrieve_references ────────────────────────────────────────────────

def patch_retrieve_references():
    print("Fetching retrieve_references …")
    wf = api_get("/workflows/Ai8JckgkEwez7D8D")

    nodes = wf["nodes"]
    node_by_id   = {n["id"]: n for n in nodes}
    node_by_name = {n["name"]: n for n in nodes}

    # 1. Update Validate body
    vb = node_by_id["f8c1eff9"]
    vb["parameters"]["jsCode"] = RETRIEVE_VALIDATE_BODY_JS
    print("  ✓ Validate body — added prompt field")

    # 2. Update Collect refs for draft
    cr = node_by_id["collect_refs_001"]
    cr["parameters"]["jsCode"] = COLLECT_REFS_JS
    print("  ✓ Collect refs for draft — pass prompt")

    # 3. Update Call generate/draft body to include prompt
    cg = node_by_id["call_generate_001"]
    cg["parameters"]["body"] = (
        "={{ JSON.stringify({ upload_id: $json.upload_id, room_type: $json.room_type,"
        " style_tag: $json.style_tag, prompt: $json.prompt,"
        " reference_ids: $json.reference_ids, session_id: $json.session_id }) }}"
    )
    print("  ✓ Call generate/draft — prompt in body")

    # 4. Add Prompt Re-rank node (position between RPC and fan-out)
    rpc_pos = node_by_name["RPC retrieve_references"]["position"]
    rerank_node = {
        "id": "prompt_rerank_001",
        "name": "Prompt Re-rank",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [rpc_pos[0] + 240, rpc_pos[1]],
        "parameters": {
            "mode": "runOnceForAllItems",
            "jsCode": PROMPT_RERANK_JS,
        },
    }
    # Only add if not already present
    if not any(n["id"] == "prompt_rerank_001" for n in nodes):
        nodes.append(rerank_node)
        print("  ✓ Prompt Re-rank node added")
    else:
        node_by_id["prompt_rerank_001"]["parameters"]["jsCode"] = PROMPT_RERANK_JS
        print("  ✓ Prompt Re-rank node updated (already existed)")

    # 5. Update connections: RPC → Prompt Re-rank → [Log event, Collect refs, Aggregate]
    conns = wf["connections"]
    # Reroute RPC output to go through Prompt Re-rank first
    rpc_fanout = conns.get("RPC retrieve_references", {}).get("main", [[]])[0]
    # Check if already routed through Prompt Re-rank
    if not any(t["node"] == "Prompt Re-rank" for t in rpc_fanout):
        # Save original fan-out targets (minus any already-present Prompt Re-rank)
        original_targets = [t for t in rpc_fanout]
        # Replace RPC output with single target: Prompt Re-rank
        conns["RPC retrieve_references"]["main"] = [[
            {"node": "Prompt Re-rank", "type": "main", "index": 0}
        ]]
        # Wire Prompt Re-rank → original fan-out
        conns["Prompt Re-rank"] = {"main": [original_targets]}
        print("  ✓ Connections: RPC → Prompt Re-rank → fan-out")
    else:
        print("  ✓ Connections already routed through Prompt Re-rank")

    # Push to n8n
    payload = {
        "name": wf["name"],
        "nodes": wf["nodes"],
        "connections": wf["connections"],
        "settings": wf.get("settings", {}),
        "staticData": wf.get("staticData"),
    }
    result = api_put("/workflows/Ai8JckgkEwez7D8D", payload)
    print(f"  → Pushed. updatedAt={result.get('updatedAt','?')}")
    return result


# ─── PATCH generate_draft ─────────────────────────────────────────────────────

def patch_generate_draft():
    print("Fetching generate_draft …")
    wf = api_get("/workflows/IkvnnbntRoK7OSgS")

    nodes = wf["nodes"]
    node_by_id = {n["id"]: n for n in nodes}

    # 1. Update Validate body
    vb = node_by_id["7bb0767b-a83d-43e3-93f6-fd1594f09a4a"]
    vb["parameters"]["jsCode"] = DRAFT_VALIDATE_BODY_JS
    print("  ✓ Validate body — added prompt, removed room_type/style_tag requirement")

    # 2. Update Build Gemini request
    bg = node_by_id["5403b89f-8e61-4a7c-91b6-5e4e820bc683"]
    bg["parameters"]["jsCode"] = BUILD_GEMINI_JS
    print("  ✓ Build Gemini request — prompt injected into instruction")

    payload = {
        "name": wf["name"],
        "nodes": wf["nodes"],
        "connections": wf["connections"],
        "settings": wf.get("settings", {}),
        "staticData": wf.get("staticData"),
    }
    result = api_put("/workflows/IkvnnbntRoK7OSgS", payload)
    print(f"  → Pushed. updatedAt={result.get('updatedAt','?')}")
    return result


if __name__ == "__main__":
    try:
        patch_retrieve_references()
        print()
        patch_generate_draft()
        print("\nAll patches applied successfully.")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code}: {body}")
        raise
