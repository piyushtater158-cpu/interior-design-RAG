# n8n — Interior Design RAG

Workflows and SQL helpers for the interior stack: **n8n webhooks → Supabase (Postgres + Storage) → OpenRouter (chat) + Gemini (images)**. Auth for protected routes is **Supabase JWT** verification (`GET /auth/v1/user`), not custom HS256 in production unless you still run legacy nodes.

## Architecture

```
mobile-app (static) ── HTTPS ──▶ n8n (webhooks) ──▶ Supabase (DB + Storage)
                                         │
                                         ├──▶ OpenRouter (orchestrator / vision captioning)
                                         └──▶ Google Gemini (image generation)
```

Reference pool selection for `generate/orchestrated` uses **`retrieve_candidates_text`** (FTS on `caption_enhanced` / `caption`). Vector embeddings and **`retrieve_references`** are not part of the current schema (`supabase/migrations/100_reset_and_rebuild.sql`).

## Directory layout

```
n8n/
├── migrations/          SQL to apply on Supabase (order below)
├── prompts/             Prompt source text (also inlined in workflows)
├── workflows/           Main + consolidated JSON
├── WORKFLOW_SYSTEM.md   Node-by-node narrative (partially auto-synced)
└── README.md            This file
```

## Supabase SQL — apply in order

Use the Supabase SQL editor or CLI. Combine with **all** prior `supabase/migrations/*.sql` from the repo root for a greenfield project; for this repo’s curated n8n folder specifically:

1. `migrations/005_app_config.sql` — `app_config` seeds (`image_model`, `openrouter_base`, orchestrator, edit chain cap). No `embedding_model`.
2. `migrations/006_storage_buckets.sql` — storage buckets + policies.
3. `migrations/008_admin_metrics_rpc.sql` — `admin_metrics` RPC if used.
4. `migrations/012_enhanced_captions_spatial.sql` — `caption_enhanced`, `spatial_signature`, `caption_fts`, **`retrieve_candidates_text`**.

Then apply root **`supabase/migrations/100_reset_and_rebuild.sql`** on greenfield databases, followed by any newer `supabase/migrations/2026*.sql` and `database/migrations/*.sql` not already covered above.

**Sanity checks**

```sql
SELECT key FROM app_config ORDER BY key;
SELECT proname FROM pg_proc WHERE proname IN ('retrieve_candidates_text','generation_chain_depth','admin_metrics');
-- retrieve_references must NOT appear (FTS-only schema)
```

## n8n environment variables

Set in n8n → Settings → Variables (or your deployment env). Workflows may bake values into Code nodes instead of `$env` depending on how the consolidated workflow was built.

| Variable | Required | Purpose |
|---|---|---|
| `SUPABASE_URL` | yes | Project URL |
| `SUPABASE_SERVICE_KEY` | yes | Service role for REST from n8n |
| `SUPABASE_ANON_KEY` | often | If nodes verify JWT as anon |
| `OPENROUTER_API_KEY` | yes | Chat / vision (no embedding model var required for FTS path) |
| `OPENROUTER_BASE_URL` | no | Default `https://openrouter.ai/api/v1` |
| `OPENROUTER_ORCHESTRATOR_MODEL` | no | Agent 1 / 2 chat model |
| `GEMINI_API_KEY` | yes | Image generation |
| `ADMIN_TOKEN` | yes | `X-Admin-Token` for admin metrics |

## Importing workflows

Import the consolidated workflow (and any `_shared` pieces) from `n8n/workflows/`, activate it, and confirm webhook URLs match your deployment. Sub-workflows may be inlined; see `WORKFLOW_SYSTEM.md`.

## Wire **mobile-app**

Configure the mobile shell with your public **n8n webhook base** (e.g. `https://your-n8n.example.com/webhook`) and Supabase anon URL/key in whatever config surface that app uses (`mobile-app` static assets / env injection at hosting time).

## Webhook inventory (typical)

| Method | Path | Auth |
|---|---|---|
| GET | `/health` | none |
| GET | `/auth/me` | Bearer (Supabase JWT) |
| POST | `/uploads/room-photo` | Bearer |
| POST | `/generate/orchestrated` | Bearer |
| POST | `/generate/draft`, `/generate/edit`, `/generate/commit` | Bearer |
| GET | `/admin/metrics` | `X-Admin-Token` |

Legacy **`POST /retrieve/references`** may still exist inside an old consolidated export; it will fail against a DB migrated with **016** until those nodes are removed or reworked to FTS-only.

## Contracts

- `supabase/migrations/100_reset_and_rebuild.sql` — table shapes and policies (authoritative DDL).
- `contracts/openapi.yaml` — HTTP shapes where maintained.

## Docs

- `n8n/WORKFLOW_SYSTEM.md` — deep dive per endpoint.
- `database/README.md` — Python seed and local DB mirror.
