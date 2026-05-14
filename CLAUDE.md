## Product stack

- **Supabase**: Postgres + Auth + Storage; migrations under `supabase/migrations/` (includes FTS `retrieve_candidates_text`, no pgvector).
- **n8n**: Webhook API and orchestration (`n8n/workflows/`, `n8n/migrations/`).
- **Client**: `mobile-app/` static shell only (no `frontend/` Next.js app in this repo).

## Full Pipeline
1. Read CLAUDE.md and understand project context.
2. Run `/gstack-autoplan` to review approach (CEO + eng + design).
3. Implement the approved plan. Follow planning discipline.
4. Run `/gstack-ship` to create a PR with tests, changelog, and version bump.
5. Report: PR URL, what shipped, decisions, anything uncertain.

## graphify
This project has a knowledge graph at `graphify-out/`.
- Before architecture/codebase questions: read `graphify-out/GRAPH_REPORT.md` for god nodes
- Cross-module questions: use `graphify query "<q>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` instead of grep
- After code changes: run `graphify update .`
- Before any bug investigation: run `graphify query "<error>"` first — do not start with file reads
