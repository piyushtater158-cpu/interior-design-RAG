# Continue Building n8n Workflow — Interior Design RAG

## Context

The goal is to run the entire Interior Design RAG backend as a **single n8n workflow** named "INTERIOR DESIGN RAG" on a self-hosted n8n at `http://localhost:5678`. All 17 original workflows (13 main endpoints + 4 shared sub-workflows) have been merged into one consolidated JSON via a Python build script. The workflow is already deployed and active in n8n. The remaining work is to unblock environment variable access so the endpoints actually work, then run smoke tests.

---

## Current State (as of 2026-04-23)

### What is DONE
- `n8n/build_consolidated.py` — build script that merges all 17 workflows into one
- `n8n/workflows/interior_design_rag_consolidated.json` — generated output, **220 nodes**, 177 connections
- All 4 sub-workflows fully inlined (zero `executeWorkflow` nodes remain)
- Per-branch Config Code nodes inject env vars into `$json._cfg` for HTTP nodes (12 Config nodes, one per branch that needs env vars)
- Health branch **correctly has NO Config node** — `GET /webhook/health` returns 200 already
- IF node v2 type-validation bug fixed (`_error` checks rewritten to string-truthy)
- Workflow deployed to n8n as workflow ID **`JbnB5CPdoqgCl75F`**, active = true
- n8n API key: set `N8N_API_KEY` in `.env` (never commit; rotate if previously exposed in git)

### Current Blocker — `$env` blocked in task runner sandbox
n8n's default task runner (`N8N_RUNNERS_ENABLED=true`) runs Code nodes in a sandboxed subprocess. In this sandbox **both `$env` AND `process.env` are blocked**. All branches that have a Config Code node (which reads `$env.SUPABASE_URL` etc.) fail with:

```
"access to env vars denied"
```

This means `/auth/magic-link`, `/auth/me`, and all other non-health endpoints fail. **The fix is a one-time Windows environment variable + n8n restart.**

---

## Critical Files

| File | Role |
|---|---|
| `n8n/build_consolidated.py` | Build script — run this to regenerate the consolidated JSON |
| `n8n/workflows/interior_design_rag_consolidated.json` | Generated output (do NOT hand-edit) |
| `n8n/workflows/wf_upload.json` | Stripped deploy payload (auto-generated) |
| `n8n/workflows/*.json` (13 files) | Source main workflows — read by build script |
| `n8n/workflows/_shared/*.json` (4 files) | Source sub-workflows — inlined by build script |
| `n8n/migrations/004_nemotron_embeddings.sql` … `008_admin_metrics_rpc.sql` | May still need applying to Supabase |
| `frontend/.env.local` | Update after n8n is fully working |

---

## Step-by-Step: What to Do When Resuming

### Step 1 — Collect the API keys you still need (do this FIRST, outside n8n)

You need the following values:

| Variable | Where to get it |
|---|---|
| `SUPABASE_SERVICE_KEY` | Supabase dashboard → `https://uzghfpxboktnbcbbthns.supabase.co` → Settings → API → **service_role** key |
| `OPENROUTER_API_KEY` | https://openrouter.ai → Settings → Keys → Create Key |
| `GEMINI_API_KEY` | https://aistudio.google.com → Get API Key |
| `JWT_SECRET` | Generate in PowerShell: `[Convert]::ToBase64String((1..48 \| ForEach-Object {Get-Random -Max 256}))` |
| `ADMIN_TOKEN` | Any random string ≥24 chars |

---

### Step 2 — Set Windows user environment variables permanently

Open **Start → Search "Edit the system environment variables" → Environment Variables → User variables → New** for each entry:

```
N8N_BLOCK_ENV_ACCESS_IN_NODE   = false
SUPABASE_URL                   = https://uzghfpxboktnbcbbthns.supabase.co
SUPABASE_SERVICE_KEY           = <your service-role key>
OPENROUTER_API_KEY             = <your sk-or-v1-... key>
GEMINI_API_KEY                 = <your AIzaSy... key>
OPENROUTER_BASE_URL            = https://openrouter.ai/api/v1
OPENROUTER_ORCHESTRATOR_MODEL  = google/gemini-2.5-flash
JWT_SECRET                     = <your generated base64 string>
ADMIN_TOKEN                    = <your random admin string>
```

`N8N_BLOCK_ENV_ACCESS_IN_NODE=false` is the critical one — it tells n8n to allow Code nodes to read `$env.X`. Without it all Config nodes fail.

---

### Step 3 — Restart n8n

Kill the current n8n process. Open a new terminal (so it picks up the new env vars) and start n8n again. Verify it's up at `http://localhost:5678`.

---

### Step 4 — Rebuild the consolidated workflow

```bash
cd "C:\Users\asus\OneDrive\Documents\Claude\Projects\Interior design RAG"
python n8n/build_consolidated.py
```

Expected output:
```
  Node names  : 220 unique OK
  Execute WF nodes : 0 remaining OK
  Node IDs    : 220 unique OK
Nodes  : 220
Conns  : 177
```

---

### Step 5 — Deploy to n8n via REST API

Run this from the project root. The Python one-liner strips the JSON, then curl PUTs it:

```bash
cd "C:\Users\asus\OneDrive\Documents\Claude\Projects\Interior design RAG"
N8N_KEY="${N8N_API_KEY:?set in .env}"

python -c "
import json
with open('n8n/workflows/interior_design_rag_consolidated.json') as f:
    wf = json.load(f)
upload = {k: wf[k] for k in ['name','nodes','connections','settings']}
with open('n8n/workflows/wf_upload.json', 'w') as f:
    json.dump(upload, f)
print('nodes:', len(upload['nodes']))
"

curl -s -X PUT "http://localhost:5678/api/v1/workflows/JbnB5CPdoqgCl75F" \
  -H "X-N8N-API-KEY: $N8N_KEY" \
  -H "Content-Type: application/json" \
  -d @"n8n/workflows/wf_upload.json" \
  | python -c "import sys,json; r=json.load(sys.stdin); print('PUT id:',r.get('id'),'active:',r.get('active'),'nodes:',len(r.get('nodes',[])))"

curl -s -X POST "http://localhost:5678/api/v1/workflows/JbnB5CPdoqgCl75F/activate" \
  -H "X-N8N-API-KEY: $N8N_KEY"
```

---

### Step 6 — Smoke test all endpoints

```bash
BASE="http://localhost:5678/webhook"

# 1. Health (no auth — already works)
curl $BASE/health
# expected: {"status":"ok","backend":"n8n-interior-design-assistant"}

# 2. Magic-link login
curl -X POST $BASE/auth/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
# expected: {"token":"<jwt>","user_id":"...","email":"test@example.com"}

# 3. Token verify (replace <jwt> with token from above)
curl $BASE/auth/me \
  -H "Authorization: Bearer <jwt>"
# expected: {"user_id":"...","email":"test@example.com"}

# 4. Admin metrics (replace <ADMIN_TOKEN> with your value)
curl $BASE/admin/metrics \
  -H "X-Admin-Token: <ADMIN_TOKEN>"
# expected: JSON with generation_count, latency percentiles
```

If any endpoint fails, open n8n UI → workflow → Executions tab to see which node errored.

---

### Step 7 — Apply missing Supabase migrations (if needed)

Check first:
```sql
SELECT proname FROM pg_proc
  WHERE proname IN ('retrieve_references','generation_chain_depth','admin_metrics');
-- 3 rows expected. If missing, apply migrations below.
```

Apply in order in the Supabase SQL editor (`https://uzghfpxboktnbcbbthns.supabase.co` → SQL Editor):
1. `n8n/migrations/004_nemotron_embeddings.sql`
2. `n8n/migrations/005_app_config.sql`
3. `n8n/migrations/006_storage_buckets.sql`
4. `n8n/migrations/007_retrieval_rpc.sql`
5. `n8n/migrations/008_admin_metrics_rpc.sql`

---

### Step 8 — Seed reference embeddings (one-time)

In n8n UI: open the INTERIOR DESIGN RAG workflow → scroll to the very bottom of the canvas (y≈14400) → find the Manual Trigger node (branch namespace: `seed`) → right-click → **Execute from here**.

Wait 5-10 minutes. Verify:
```sql
SELECT COUNT(*) FROM reference_embeddings WHERE embedding_type = 'nemotron-vl-1b-v2';
-- expected: 104
SELECT COUNT(*) FROM reference_embeddings WHERE embedding IS NULL;
-- expected: 0
```

---

### Step 9 — Wire the frontend

Edit `frontend/.env.local`:
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:5678/webhook
```
Restart `next dev` and test the full browser flow (login → upload → retrieve → generate).

---

## Architecture Notes

### Config node pattern (how env vars reach HTTP nodes)

Every branch that calls external APIs gets a `ns::Config` Code node inserted right after the Webhook trigger:

```
[ns::Webhook] → [ns::Config] → [ns::Validate body] → ...
```

The Config node reads ALL env vars into `$json._cfg`:
```js
return [{ json: { ...$json, _cfg: {
  supabase_url: $env.SUPABASE_URL || '',
  supabase_key: $env.SUPABASE_SERVICE_KEY || '',
  ...
} }, binary: $input.first().binary || {} }];
```

All downstream HTTP nodes reference config as `$('auth-ml::Config').first().json._cfg.supabase_url` etc. (no `$env` in HTTP nodes). Code nodes (JWT sign/verify) reference `$env.JWT_SECRET` directly. **Both require `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`.**

Health branch has no Config node (no env vars needed — just returns static JSON).

### Node namespace convention

All nodes prefixed with `ns::`:
- `health`, `auth-ml`, `auth-me`, `upload`, `retrieve`, `draft`, `edit`, `commit`, `orch`, `gen-sess`, `gen-exp`, `admin`, `seed`

### Sub-workflow inlining

| Original sub-workflow | Inlined as |
|---|---|
| `wf_jwt_verify` | 1 Code node — HS256 verify using `$env.JWT_SECRET` |
| `wf_jwt_sign` | 1 Code node — HS256 sign using `$env.JWT_SECRET` |
| `wf_event_log` | 1 HTTP Request node — POST to Supabase `/rest/v1/events` |
| `wf_save_generation` | 4 nodes: Assemble row → Upload PNG → Insert generation row → Build gen response |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Non-health endpoints return empty 200 | `N8N_BLOCK_ENV_ACCESS_IN_NODE` still true | Set env var, restart n8n |
| `"access to env vars denied"` in n8n logs | Same as above | Same fix |
| `"process is not defined"` in n8n logs | Stale workflow version in n8n | Rebuild + redeploy |
| 404 on any endpoint | Workflow not active | Re-run activate curl command |
| Health returns empty body | Config node accidentally in health branch | Rebuild — build_consolidated.py is already fixed |
| PUT returns "additional properties" error | Sending `active` or `pinData` fields | Use the strip step before curl |
| n8n API key rejected | Key expired (2026-05-23) | See below |

### If the n8n API key has expired
```bash
python -c "
import sqlite3
conn = sqlite3.connect(r'C:\Users\asus\.n8n\database.sqlite')
cur = conn.cursor()
cur.execute('SELECT apiKey FROM user_api_keys LIMIT 1')
print(cur.fetchone()[0])
conn.close()
"
```
Or generate a new one: n8n UI → Settings → n8n API → Create API Key.
