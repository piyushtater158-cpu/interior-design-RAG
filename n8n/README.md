# n8n Backend — Interior Design RAG

This directory contains the n8n workflows that replace the FastAPI backend under `backend/`. Every endpoint the frontend needs is implemented as a webhook-triggered workflow that runs on n8n Cloud or a self-hosted n8n instance (VPS / Docker).

## Architecture

```
Frontend ── HTTPS ──▶ n8n (webhooks) ──▶ Supabase (DB + Storage)
                              │
                              ├──▶ OpenRouter (Nemotron-VL embeddings, orchestrator LLM)
                              └──▶ Google Gemini (image generation)
```

Three external services only. No always-on Python service. No local disk.

## Directory layout

```
n8n/
├── migrations/              SQL migrations (004–008) applied to Supabase
├── prompts/                 Source of truth for prompt text (also inlined in Code nodes)
├── workflows/
│   ├── _shared/             Sub-workflows reused by main webhooks
│   └── *.json               Main webhook workflows
├── credentials/             Redacted credential skeletons (optional)
└── README.md                This file
```

## Environment variables

Set these in n8n → Settings → Variables. All workflow JSON references them via `{{$env.NAME}}`.

| Variable | Required | Purpose |
|---|---|---|
| `SUPABASE_URL`                  | yes | e.g. `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_KEY`          | yes | Supabase service-role key (not anon) |
| `OPENROUTER_API_KEY`            | yes | For Nemotron embeddings + orchestrator LLM |
| `OPENROUTER_BASE_URL`           | no  | Defaults to `https://openrouter.ai/api/v1` |
| `OPENROUTER_EMBED_MODEL`        | no  | Defaults to `nvidia/llama-nemotron-embed-vl-1b-v2:free` |
| `OPENROUTER_ORCHESTRATOR_MODEL` | no  | Defaults to `google/gemini-2.5-flash` |
| `OPENROUTER_RETRIEVER_MODEL`    | no  | Falls back to `OPENROUTER_ORCHESTRATOR_MODEL` |
| `GEMINI_API_KEY`                | yes | Google AI Studio key for image generation |
| `JWT_SECRET`                    | yes | HS256 secret used by `wf_jwt_sign` / `wf_jwt_verify` |
| `ADMIN_TOKEN`                   | yes | Opaque token checked by `admin_metrics` via `X-Admin-Token` header |

## Setup — from scratch

### 1. Supabase

Apply the migrations in order against the Supabase project (SQL editor or `psql`):

```
migrations/004_nemotron_embeddings.sql
migrations/005_app_config.sql
migrations/006_storage_buckets.sql
migrations/007_retrieval_rpc.sql
migrations/008_admin_metrics_rpc.sql
```

Verify:

- `SELECT COUNT(*) FROM app_config;` → ≥ 5 rows (includes `image_model`).
- `SELECT id, public FROM storage.buckets WHERE id IN ('user-uploads','user-outputs');` → both rows, `public=true`.
- `SELECT proname FROM pg_proc WHERE proname IN ('retrieve_references','generation_chain_depth','admin_metrics');` → 3 rows.

### 2. n8n (Cloud or self-hosted VPS)

**Cloud:** sign up at `n8n.cloud`. Your webhook base is `https://<workspace>.app.n8n.cloud/webhook`.

**Self-hosted VPS (Docker):**

```bash
docker run -d --name n8n \
  -p 5678:5678 \
  -e N8N_HOST=n8n.yourdomain.tld \
  -e WEBHOOK_URL=https://n8n.yourdomain.tld/ \
  -e N8N_PROTOCOL=https \
  -e N8N_PORT=5678 \
  -e GENERIC_TIMEZONE=UTC \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n
```

Put a reverse proxy (Caddy, nginx) in front for TLS. Your webhook base is `https://n8n.yourdomain.tld/webhook`.

### 3. Import workflows — order matters

n8n resolves sub-workflows by the string in `workflowId.value`. Import shared workflows first so the main workflows can bind to them.

1. `workflows/_shared/wf_jwt_sign.json`
2. `workflows/_shared/wf_jwt_verify.json`
3. `workflows/_shared/wf_event_log.json`
4. `workflows/_shared/wf_save_generation.json`
5. All main workflows under `workflows/*.json`

For each imported main workflow:
- Open it → confirm the `executeWorkflow` nodes resolve to the correct sub-workflow (dropdown shows the name). If n8n assigned a random ID instead of `wf_*`, edit the node and pick the correct sub-workflow from the list.
- Toggle **Active = ON** so the webhook becomes reachable.

### 4. Set environment variables + credentials

- Settings → Variables: set every variable listed above.
- Optional: import the redacted skeletons from `credentials/` and fill in real values. Every workflow can also run without named credentials because the HTTP nodes inline `{{$env.*}}` directly.

### 5. Seed Nemotron embeddings (one-time)

Open `_seed_nemotron_references` in the n8n UI → Execute workflow (manual trigger). Expect ~104 reference images × (fetch + embed + insert) in batches of 3 → ~5–10 minutes.

Verify:

```sql
SELECT COUNT(*) FROM reference_embeddings WHERE embedding_type = 'nemotron-vl-1b-v2';
-- expected: 104
SELECT COUNT(*) FROM reference_embeddings WHERE embedding IS NULL;
-- expected: 0
```

### 6. Wire frontend

Edit `frontend/.env.local`:

```
NEXT_PUBLIC_BACKEND_URL=https://<workspace>.app.n8n.cloud/webhook
# or for self-hosted:
NEXT_PUBLIC_BACKEND_URL=https://n8n.yourdomain.tld/webhook
```

Restart `next dev`.

## Webhook inventory

| Method | Path | Workflow | Auth |
|---|---|---|---|
| GET  | `/health`                                       | `health`                     | none |
| POST | `/auth/magic-link`                              | `auth_magic_link`            | none |
| GET  | `/auth/me`                                      | `auth_me`                    | Bearer |
| POST | `/uploads/room-photo`                           | `uploads_room_photo`         | Bearer |
| POST | `/retrieve/references`                          | `retrieve_references`        | Bearer |
| POST | `/generate/draft`                               | `generate_draft`             | Bearer |
| POST | `/generate/edit`                                | `generate_edit`              | Bearer |
| POST | `/generate/commit`                              | `generate_commit`            | Bearer |
| POST | `/generate/orchestrated`                        | `generate_orchestrated`      | Bearer |
| GET  | `/generations/session/:session_id`              | `generations_session`        | Bearer |
| POST | `/generations/:generation_id/export`            | `generations_export`         | Bearer |
| GET  | `/admin/metrics`                                | `admin_metrics`              | `X-Admin-Token` |

## Shared sub-workflows

| ID | Input | Output | Used by |
|---|---|---|---|
| `wf_jwt_sign`       | `{user_id, email}`                                    | `{token, user_id, email}` | `auth_magic_link` |
| `wf_jwt_verify`     | `{authorization}`                                     | `{ok, user_id, email, error?, code?}` | all Bearer-gated endpoints |
| `wf_event_log`      | `{event_type, user_id?, session_id?, payload?}`       | `{logged:true}` (fire-and-forget) | every workflow |
| `wf_save_generation`| generation fields + `binary.output_png`                | `{generation_id, output_url, …}` | draft, edit, commit, orchestrated |

## Updating the image model

The image model is in the `app_config` table so it can be swapped without redeploying workflows:

```sql
UPDATE app_config SET value = '"gemini-3.5-flash-image-preview"' WHERE key = 'image_model';
```

Every generation workflow reads `image_model` at call time.

## Edit-chain cap

Enforced at 6 via the `generation_chain_depth` RPC in `generate_edit`. To change:

```sql
UPDATE app_config SET value = '8' WHERE key = 'max_edit_chain';
```

…and update the constant in `generate_edit.json`'s "Check cap" Code node (currently hardcoded to 6).

## Running workflows manually (from n8n UI)

Every webhook workflow can also be executed directly from the UI ("Execute Workflow" button) for testing. The Webhook trigger exposes a "Test URL" you can call from Postman / curl — useful when the workflow is not yet active.

## Troubleshooting

- **404 on webhook** — workflow is not Active. Toggle the switch at the top of the workflow view.
- **401 from OpenRouter** — `OPENROUTER_API_KEY` missing or wrong.
- **403 from Supabase Storage on upload** — bucket is not public OR service-role policies not applied. Re-run `006_storage_buckets.sql`.
- **Gemini returns `SAFETY` block** — the prompt tripped a safety filter. Log the full response and soften the language.
- **Sub-workflow "not found"** — after import, the `workflowId.value` on the `executeWorkflow` node doesn't match the sub-workflow's actual ID. Open the node, pick from the dropdown, save.
- **Multipart upload fails in `uploads_room_photo`** — confirm the Webhook trigger has `Binary Data: true` enabled. n8n Cloud sometimes resets this on import.
- **Seed workflow stalls** — OpenRouter rate-limits the free Nemotron tier. The seed already uses batch size 3 with 2 s retry; if it still fails, reduce `batchSize` to 1.

## Self-hosting notes (VPS)

- Use Postgres for n8n's own storage (`DB_TYPE=postgresdb`) if you expect > 1000 executions. SQLite is fine for demos.
- Persist `/home/node/.n8n` (credentials + workflow state).
- Put webhooks behind HTTPS — the frontend will refuse mixed content.
- If using Caddy, add `n8n.yourdomain.tld { reverse_proxy localhost:5678 }` — Caddy auto-provisions TLS.

## Contracts

The request/response shapes are maintained in `contracts/`:
- `contracts/openapi.yaml` — machine-readable spec.
- `contracts/api-spec.md` — human-readable examples.
- `contracts/backend-url.md` — which base URL the frontend should hit.
- `contracts/backend-env.md` — required env vars.

Keep `n8n/` and `contracts/` in sync when adding or renaming endpoints.
