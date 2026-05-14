#!/usr/bin/env python3
"""
patch_orchestrated_phase5.py
Phase 5 changes to generate_orchestrated.json:
  1. validate: capture bearer_token from incoming Authorization header
  2. fetch_pool: add owner_id=eq.{user_id} filter; switch to user bearer + anon key
  3. fetch_pool_all: same
  4. fetch_pick_urls: switch to user bearer + anon key
  5. check_pool: add pool_empty flag
  6. Insert 'Empty pool?' IF node between check_pool and if_fallback
  7. Insert 'Respond no refs' node for empty-pool path
Usage:
  python n8n/patch_orchestrated_phase5.py --check
  python n8n/patch_orchestrated_phase5.py --apply
"""
import json, pathlib, sys, copy

ROOT = pathlib.Path(__file__).parent.parent
PATH = ROOT / "n8n" / "workflows" / "generate_orchestrated.json"

# ---------------------------------------------------------------------------
# Updated code / parameter snippets
# ---------------------------------------------------------------------------

VALIDATE_CODE = r"""const _raw = $('POST /generate/orchestrated').item.json.body || {};
const body = (() => {
  const keys = Object.keys(_raw);
  if (keys.length === 1 && String(keys[0]).trimStart().startsWith('{')) {
    try { return JSON.parse(keys[0]); } catch (_) {}
  }
  return _raw;
})();
const user_id    = $json.user_id;
// Capture bearer token for downstream RLS-scoped DB reads
const bearer_token = ($('POST /generate/orchestrated').item.json.headers?.authorization ||
                      $('POST /generate/orchestrated').item.json.headers?.Authorization || '')
                       .replace(/^Bearer\s+/i, '');
const upload_id  = (body.upload_id  || '').toString().trim();
const brief      = (body.brief      || '').toString().trim();
const session_id = body.session_id  ? body.session_id.toString() : null;
const room_type_raw = body.room_type   ? body.room_type.toString().trim() : null;
const UI_ROOM_TO_DB = { bedroom: 'bedroom', kids: 'kids room', dining: 'dining room', kitchen: 'kitchen', mandir: 'mandir', living: 'living room' };
const room_hint  = room_type_raw && UI_ROOM_TO_DB[room_type_raw] ? UI_ROOM_TO_DB[room_type_raw] : room_type_raw;
const style_tag  = body.style_tag   ? body.style_tag.toString().trim() : null;

const missing = [];
if (!upload_id) missing.push('upload_id');
if (!brief)     missing.push('brief');
if (missing.length) {
  return [{ json: { _error: { status: 400, body: { error: `missing_fields: ${missing.join(',')}`, code: 'invalid_request' } } } }];
}

const storage_path = `user-uploads/${user_id}/${upload_id}`;
const upload_url   = `https://uzghfpxboktnbcbbthns.supabase.co/storage/v1/object/public/${storage_path}`;
return [{ json: { user_id, bearer_token, upload_id, brief, session_id, room_hint, style_tag, upload_url, started_at_ms: Date.now() } }];"""

# fetch_pool URL: owner-scoped, room+style filtered, user bearer + anon key
FETCH_POOL_URL = (
    "={{ 'https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/reference_images"
    "?select=id,source_url,caption,room_type,style_tags,dominant_colors,detected_objects,quality_score"
    "&owner_id=eq.' + encodeURIComponent($json.user_id)"
    " + '&order=quality_score.desc.nullslast&limit=20'"
    " + ($json.inferred_room ? '&room_type=eq.' + encodeURIComponent($json.inferred_room) : '')"
    " + ($json.style_tag ? '&style_tags=cs.%7B' + encodeURIComponent($json.style_tag) + '%7D' : '')"
    " }}"
)

# Use user bearer + SUPABASE_ANON_KEY — RLS enforces owner_id
POOL_HEADERS = {
    "parameters": [
        {"name": "apikey",        "value": "={{ $env.SUPABASE_ANON_KEY }}"},
        {"name": "Authorization", "value": "=Bearer {{ $json.bearer_token }}"},
        {"name": "Accept",        "value": "application/json"},
    ]
}

# fetch_pool_all URL: owner-scoped, style+room filtered
FETCH_POOL_ALL_URL = (
    "={{ (() => {\n"
    "  const c = $json;\n"
    "  const base = 'https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/reference_images"
    "?select=id,source_url,caption,room_type,style_tags,dominant_colors,detected_objects,quality_score"
    "&owner_id=eq.' + encodeURIComponent(c.user_id)"
    " + '&order=quality_score.desc.nullslast&limit=20';\n"
    "  const st = (c.style_tag || '').toString().trim();\n"
    "  const rm = (c.inferred_room || c.room_hint || '').toString().trim();\n"
    "  const styleTop = st ? ('&style_tags=cs.%7B' + encodeURIComponent(st) + '%7D') : '';\n"
    "  const roomTop  = rm ? ('&room_type=eq.' + encodeURIComponent(rm)) : '';\n"
    "  return base + roomTop + styleTop;\n"
    "})() }}"
)

POOL_ALL_HEADERS = {
    "parameters": [
        {"name": "apikey",        "value": "={{ $env.SUPABASE_ANON_KEY }}"},
        {"name": "Authorization", "value": "=Bearer {{ $json.bearer_token }}"},
    ]
}

# check_pool: add pool_empty flag
CHECK_POOL_CODE = r"""let rows;
if (Array.isArray($json)) {
  rows = $json;
} else if (Array.isArray($json?.body)) {
  rows = $json.body;
} else if ($json?.body && typeof $json.body === 'object') {
  rows = [$json.body];
} else if ($json && typeof $json === 'object') {
  rows = [$json];
} else {
  rows = [];
}
function dedupePool(arr) {
  const seen = new Set();
  const seenUrl = new Set();
  const out = [];
  for (const r of arr) {
    if (!r || r.id == null) continue;
    const id = r.id.toString().toLowerCase();
    const u = (r.source_url || '').split('?')[0].trim().toLowerCase();
    if (seen.has(id)) continue;
    if (u && seenUrl.has(u)) continue;
    seen.add(id);
    if (u) seenUrl.add(u);
    out.push(r);
  }
  return out;
}
const pool = dedupePool(rows);
const ctx  = $('Parse Agent 1').item.json;
const pool_empty    = pool.length === 0;
const pool_fallback = pool.length > 0 && pool.length < 3;
return [{ json: { ...ctx, pool, pool_empty, pool_fallback } }];"""

# fetch_pick_urls: user bearer + anon key (RLS double-guard)
FETCH_PICK_URLS_HEADERS = {
    "parameters": [
        {"name": "apikey",        "value": "={{ $env.SUPABASE_ANON_KEY }}"},
        {"name": "Authorization", "value": "=Bearer {{ $json.bearer_token }}"},
    ]
}

# New nodes to inject
EMPTY_POOL_IF_NODE = {
    "id": "if_empty_pool",
    "name": "Empty pool?",
    "type": "n8n-nodes-base.if",
    "typeVersion": 2.2,
    "position": [3200, 540],
    "parameters": {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
            "conditions": [
                {
                    "id": "empty-pool",
                    "leftValue": "={{ $json.pool_empty }}",
                    "rightValue": True,
                    "operator": {"type": "boolean", "operation": "equals"},
                }
            ],
            "combinator": "and",
        },
        "options": {},
    },
}

RESPOND_NO_REFS_NODE = {
    "id": "respond_no_refs",
    "name": "Respond no refs",
    "type": "n8n-nodes-base.respondToWebhook",
    "typeVersion": 1.1,
    "position": [3440, 420],
    "parameters": {
        "respondWith": "json",
        "responseBody": "={ \"error\": \"no_reference_images\", \"code\": \"empty_catalog\", \"message\": \"Upload reference images first before generating designs.\" }",
        "options": {"responseCode": 200},
    },
}


def apply(wf: dict) -> list[str]:
    nodes_by_id = {n["id"]: n for n in wf["nodes"]}
    nodes_by_name = {n["name"]: n for n in wf["nodes"]}
    log = []

    def patch_field(nid, field, new_val, desc):
        n = nodes_by_id.get(nid)
        if not n:
            log.append(f"  MISSING node {nid}")
            return
        parts = field.split(".")
        obj = n
        for p in parts[:-1]:
            obj = obj[p]
        if obj[parts[-1]] == new_val:
            log.append(f"  ALREADY DONE: {desc}")
        else:
            obj[parts[-1]] = new_val
            log.append(f"  patched: {desc}")

    # 1. validate: add bearer_token capture
    patch_field("validate", "parameters.jsCode", VALIDATE_CODE, "validate -> capture bearer_token")

    # 2. fetch_pool: owner-scoped URL + user bearer
    patch_field("fetch_pool", "parameters.url", FETCH_POOL_URL, "fetch_pool -> owner-scoped URL + user bearer")
    patch_field("fetch_pool", "parameters.headerParameters", POOL_HEADERS, "fetch_pool -> user bearer headers")

    # 3. fetch_pool_all: owner-scoped URL + user bearer
    patch_field("fetch_pool_all", "parameters.url", FETCH_POOL_ALL_URL, "fetch_pool_all -> owner-scoped URL + user bearer")
    patch_field("fetch_pool_all", "parameters.headerParameters", POOL_ALL_HEADERS, "fetch_pool_all -> user bearer headers")

    # 4. check_pool: add pool_empty flag
    patch_field("check_pool", "parameters.jsCode", CHECK_POOL_CODE, "check_pool -> add pool_empty flag")

    # 5. fetch_pick_urls: user bearer + anon key
    patch_field("fetch_pick_urls", "parameters.headerParameters", FETCH_PICK_URLS_HEADERS, "fetch_pick_urls -> user bearer headers")

    # 6. Insert if_empty_pool and respond_no_refs nodes (idempotent)
    existing_ids = {n["id"] for n in wf["nodes"]}
    if "if_empty_pool" not in existing_ids:
        wf["nodes"].append(copy.deepcopy(EMPTY_POOL_IF_NODE))
        log.append("  inserted: Empty pool? IF node")
    else:
        log.append("  ALREADY DONE: Empty pool? node exists")

    if "respond_no_refs" not in existing_ids:
        wf["nodes"].append(copy.deepcopy(RESPOND_NO_REFS_NODE))
        log.append("  inserted: Respond no refs node")
    else:
        log.append("  ALREADY DONE: Respond no refs node exists")

    # 7. Update connections
    conns = wf.setdefault("connections", {})

    # Re-route: Check pool -> Empty pool? (was -> Need fallback?)
    check_pool_name = "Check pool"
    if check_pool_name in conns:
        old_target = conns[check_pool_name]["main"][0][0]["node"] if conns[check_pool_name]["main"][0] else None
        if old_target == "Need fallback?":
            conns[check_pool_name]["main"][0] = [{"node": "Empty pool?", "type": "main", "index": 0}]
            log.append("  rerouted: Check pool -> Empty pool?")
        elif old_target == "Empty pool?":
            log.append("  ALREADY DONE: Check pool -> Empty pool?")
        else:
            log.append(f"  WARNING: Check pool targets unexpected node: {old_target}")

    # Empty pool? true -> Respond no refs, false -> Need fallback?
    if "Empty pool?" not in conns:
        conns["Empty pool?"] = {
            "main": [
                [{"node": "Respond no refs", "type": "main", "index": 0}],
                [{"node": "Need fallback?",  "type": "main", "index": 0}],
            ]
        }
        log.append("  added connections: Empty pool? -> [Respond no refs, Need fallback?]")
    else:
        log.append("  ALREADY DONE: Empty pool? connections exist")

    return log


def main():
    dry_run = "--check" in sys.argv
    do_apply = "--apply" in sys.argv
    if not dry_run and not do_apply:
        print(__doc__)
        sys.exit(1)

    wf = json.loads(PATH.read_text(encoding="utf-8"))

    if dry_run:
        print("Would apply Phase 5 patches to generate_orchestrated.json:")
        print("  - validate: capture bearer_token")
        print("  - fetch_pool: owner_id filter + user bearer headers")
        print("  - fetch_pool_all: owner_id filter + user bearer headers")
        print("  - check_pool: pool_empty flag")
        print("  - fetch_pick_urls: user bearer headers")
        print("  - insert if_empty_pool IF node")
        print("  - insert respond_no_refs node")
        print("  - reroute Check pool -> Empty pool? -> [Respond no refs | Need fallback?]")
        return

    log = apply(wf)
    for line in log:
        print(line)

    PATH.write_text(json.dumps(wf, indent=2, ensure_ascii=False), encoding="utf-8")
    print("  -> written")

    # Verify no service key in pool fetch nodes
    text = PATH.read_text(encoding="utf-8")
    wf2 = json.loads(text)
    nodes_by_id = {n["id"]: n for n in wf2["nodes"]}
    for nid in ["fetch_pool", "fetch_pool_all", "fetch_pick_urls"]:
        node_txt = json.dumps(nodes_by_id.get(nid, {}))
        if "SUPABASE_SERVICE_KEY" in node_txt:
            print(f"  WARNING: {nid} still references SUPABASE_SERVICE_KEY")
        else:
            print(f"  OK: {nid} uses user bearer (no service key)")


if __name__ == "__main__":
    main()
