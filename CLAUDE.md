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

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /gstack-office-hours
- Strategy/scope → invoke /gstack-plan-ceo-review
- Architecture → invoke /gstack-plan-eng-review
- Design system/plan review → invoke /gstack-design-consultation or /gstack-plan-design-review
- Full review pipeline → invoke /gstack-autoplan
- Bugs/errors → invoke /gstack-investigate
- QA/testing site behavior → invoke /gstack-qa or /gstack-qa-only
- Code review/diff check → invoke /gstack-review
- Visual polish → invoke /gstack-design-review
- Ship/deploy/PR → invoke /gstack-ship or /gstack-land-and-deploy
- Save progress → invoke /gstack-context-save
- Resume context → invoke /gstack-context-restore
