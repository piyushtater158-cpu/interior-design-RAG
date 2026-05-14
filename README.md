# Interior Design RAG

Reference-image catalog, Supabase Postgres, n8n webhooks (OpenRouter + Gemini), and a static **mobile-app** shell. There is no in-repo FastAPI service and no Next.js desktop app.

## Layout

| Path | Role |
|---|---|
| `supabase/migrations/` | Authoritative forward migrations (apply in filename order). `016_remove_embeddings_and_vector_rpcs.sql` drops pgvector, `reference_embeddings`, and `retrieve_references` RPCs. |
| `database/` | Local/mirror migrations, Python seed (`database/seed/`), and tests. |
| `n8n/` | Workflow JSON, SQL under `n8n/migrations/` (005, 006, 008, 012), prompts, docs. |
| `mobile-app/` | PWA / static client; point it at your n8n webhook base + Supabase anon settings. |
| `contracts/` | `schema.sql` / `schema.md`, `openapi.yaml` where present. |

## Retrieval

Orchestrated generation uses full-text search via Postgres RPC `retrieve_candidates_text` on `reference_images` (see `n8n/migrations/012_enhanced_captions_spatial.sql`). Vector embeddings are not part of the schema anymore.

## Seed images

The Python seed expects styled folders under **`reference_dataset/`** at the repo root (see `database/seed/config.py`). If your files still live in an older folder name, add a junction/symlink or move them into `reference_dataset/` with the same subfolder names expected by `STYLE_FOLDERS`.

## Agents

See root `CLAUDE.md` for the full pipeline and graphify usage.
