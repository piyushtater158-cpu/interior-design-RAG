# Phase 2: Backend Implementation Plan

**Source PRD:** `c:\Users\asus\Downloads\prd-backend.md`
**Dependencies (Phase 1):** `contracts/schema.sql`, `contracts/schema.md`, `contracts/db-connection.md` — all present.
**Goal:** FastAPI backend with auth, upload, retrieval (CLIP + pgvector), generation (Gemini 2.5 Flash Image / Pro), A/B harness, and 4 contract deliverables.

---

## Context

Phase 1 delivered a seeded Postgres + pgvector database on Supabase with 104 interior design reference images + 104 CLIP ViT-B/32 embeddings. Phase 2 must build the REST API that consumes that schema and orchestrates Google Gemini image generation for a draft → edit → commit workflow. All four contract files listed in the PRD must be produced, or Phase 3 (Frontend) cannot start.

---

## Directory Layout (to be created)

```
backend/
  main.py                         # FastAPI app entrypoint
  config.py                       # Env var parsing + settings
  db.py                           # Async SQLAlchemy engine + session
  models.py                       # ORM models matching contracts/schema.md
  auth.py                         # JWT issuing + verification
  deps.py                         # FastAPI dependencies (current_user, db_session)
  storage.py                      # Local file storage helpers
  embeddings.py                   # CLIP ViT-B/32 wrapper (reuse Phase 1)
  gemini_client.py                # google-genai wrapper with retry/backoff
  routers/
    auth.py                       # /auth/*
    uploads.py                    # /uploads/*
    retrieve.py                   # /retrieve/*
    generate.py                   # /generate/*
    generations.py                # /generations/*
    admin.py                      # /admin/*
  schemas/
    auth.py                       # Pydantic request/response models
    upload.py
    retrieve.py
    generate.py
    admin.py
  prompts/
    draft.txt
    edit.txt
    commit.txt
  services/
    retrieval.py                  # Embedding + pgvector search logic
    generation.py                 # Model config A/B + Gemini orchestration
    events.py                     # events table writer
  tests/
    conftest.py                   # TestClient + DB fixtures
    test_api.py                   # Unit tests per endpoint
    test_e2e.py                   # Gated by RUN_LIVE_TESTS
    ab_harness.py                 # A/B comparison script
    rooms/                        # 10 committed test rooms (bedroom x3, dining x2, kitchen x2, mandir x2, ambiguous x1)
  outputs/                        # generated images (gitignored)
  data/
    uploads/                      # runtime uploads (gitignored)
    outputs/                      # runtime model outputs (gitignored)
  README.md
  requirements.txt
  .env.example
```

---

## Execution Sequence

### Step 1 — Bootstrap project skeleton
- Create `backend/` tree above (empty files + package `__init__.py`).
- Write `backend/requirements.txt`:
  - `fastapi>=0.115`, `uvicorn[standard]`, `sqlalchemy[asyncio]>=2.0`, `asyncpg`, `pgvector`, `pydantic>=2.7`, `pydantic-settings`, `python-multipart`, `python-jose[cryptography]`, `passlib`, `pillow`, `imagehash`, `google-genai`, `sentence-transformers`, `numpy`, `python-dotenv`, `pytest`, `pytest-asyncio`, `httpx`.
- Write `backend/.env.example` listing every required env var (see Step 11).
- `pip install -r backend/requirements.txt`.

### Step 2 — Config + Database + Models
- `config.py`: `Settings(BaseSettings)` reads `.env`, exposes `DATABASE_URL`, `GEMINI_API_KEY`, `JWT_SECRET`, `MODEL_CONFIG`, `STORAGE_PATH`, `JWT_TTL_HOURS`.
- `db.py`: async engine via `create_async_engine`, `AsyncSession` factory, IPv4 hack (reuse pattern from `database/db.py:20-22`).
- `models.py`: SQLAlchemy 2.0 declarative models mirroring `contracts/schema.md` — `User`, `ReferenceImage`, `ReferenceEmbedding` (`Vector(512)` from `pgvector.sqlalchemy`), `Generation`, `Event`.
- **No Alembic / no migrations** — schema is owned by Phase 1.

### Step 3 — Auth (mock JWT)
- `auth.py`: `create_access_token(user_id)` + `decode_token(tok)` using `python-jose` HS256.
- `routers/auth.py`:
  - `POST /auth/magic-link` — upsert `users` by email, issue JWT.
  - `GET /auth/me` — decode header, return `{user_id, email}`.
- `deps.py`: `get_current_user` dependency.

### Step 4 — Upload endpoint
- `storage.py`: `save_upload(user_id, file)` → validates JPG/PNG + max 10MB → writes to `{STORAGE_PATH}/uploads/{user_id}/{upload_id}.{ext}` → returns path.
- `routers/uploads.py`: `POST /uploads/room-photo` — multipart form → response `{upload_id, preview_url}`.
- Static mount at `/data` (FastAPI `StaticFiles`) so `preview_url` is directly fetchable.

### Step 5 — Retrieval endpoint
- `embeddings.py`: lazy-load `sentence-transformers/clip-ViT-B-32` once at app startup (reuse model from Phase 1 cache).
- `services/retrieval.py`:
  1. Load uploaded image from `upload_id` path.
  2. Encode → 512-dim vector.
  3. SQL: filter `reference_images` by `room_type` + `style_tags && ARRAY[:style_tag]`, join `reference_embeddings`, `ORDER BY embedding <=> :query LIMIT :k`.
  4. Return `[{id, url, style_tags, similarity}]` (similarity = `1 - distance`).
- `routers/retrieve.py`: `POST /retrieve/references`.

### Step 6 — Prompt templates
- Write `backend/prompts/draft.txt`, `edit.txt`, `commit.txt` verbatim from PRD §Prompt Templates.
- Helper `load_prompt(name, **kwargs)` in `services/generation.py`.

### Step 7 — Gemini client with A/B config
- `gemini_client.py`:
  - `generate_image(prompt, input_images: list[bytes], model_id) -> bytes` using `google.genai.Client.models.generate_content` with `response_modalities=['IMAGE']`.
  - Exponential backoff on 429 (0.5s, 1s, 2s, 4s, 8s, fail).
  - Returns raw PNG bytes + latency_ms + estimated cost_usd.
- `services/generation.py`:
  - `ACTIVE_CONFIG` read from DB-backed singleton table (or fallback to `MODEL_CONFIG` env).
  - `model_for(kind)` → returns model_id per config matrix in PRD §Model Strategy.
- Admin endpoints `GET/PUT /admin/ab-config` flip the singleton without redeploy.

### Step 8 — Generation endpoints
- `routers/generate.py`:
  - `POST /generate/draft` — load upload + reference images → load `draft.txt` → Gemini call → write output PNG → insert `generations` row (`kind='draft'`) → return `{generation_id, output_url, latency_ms, cost_usd}`.
  - `POST /generate/commit` — fetch parent generation → re-run with `commit.txt` template and commit model → insert `kind='commit'` row with `parent_generation_id` set.
  - `POST /generate/edit` — fetch parent → run with `edit.txt` and instruction → insert `kind='edit'` with `parent_generation_id`. Enforce chain cap of 6 edits (walk parent chain, 400 if exceeded).
- Every call writes a row to `events` with `event_type` matching the action.

### Step 9 — History + export
- `routers/generations.py`:
  - `GET /generations/session/{session_id}` — ordered list of all rows for that session.
  - `POST /generations/{id}/export` — returns pre-signed or static URL to the PNG.

### Step 10 — Admin + metrics
- `routers/admin.py`:
  - `GET/PUT /admin/ab-config` (header-protected with `ADMIN_TOKEN` env).
  - `POST /admin/run-ab-test` — kicks off `ab_harness.py` as background task.
  - `GET /admin/metrics` — 24h aggregates from `generations` + `events`: count, P50/P95 latency (use `PERCENTILE_CONT`), error rate.

### Step 11 — Env vars + README
- `.env.example` keys: `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` (for public URL generation), `GEMINI_API_KEY`, `JWT_SECRET`, `JWT_TTL_HOURS`, `MODEL_CONFIG=A`, `STORAGE_PATH=./data`, `ADMIN_TOKEN`, `RUN_LIVE_TESTS=0`.
- `backend/README.md`: prereqs, install, run (`uvicorn backend.main:app --reload`), test commands, A/B harness command, deploy hint.

### Step 12 — Unit + integration tests
- `tests/conftest.py`: `TestClient` fixture, `test_db_session` using the existing Supabase DB (or a local Postgres if `TEST_DATABASE_URL` is set).
- `tests/test_api.py`: one happy-path test per endpoint using FastAPI `TestClient`, Gemini mocked via `monkeypatch` returning a canned 1x1 PNG.
- `tests/test_e2e.py`: full upload → retrieve → draft → edit → commit against live DB + live Gemini, gated by `RUN_LIVE_TESTS=1`.

### Step 13 — A/B harness
- `tests/rooms/`: commit 10 sample room photos (3 bedroom, 2 dining, 2 kitchen, 2 mandir, 1 ambiguous).
- `tests/ab_harness.py`:
  1. For each room × 6 styles × {A, B} → call `/generate/draft`. 120 drafts total.
  2. Sample 20 → run draft → commit → 3 scripted edits.
  3. Save outputs to `tests/outputs/{config}/{room}/{style}/`.
  4. Emit `tests/outputs/metrics.csv` (latency, cost, config, room, style, status).
  5. Render `tests/outputs/report.html` with paired A/B thumbnails.
- Log spend throughout; abort with clear message if Gemini returns 429 after retries.

### Step 14 — Generate OpenAPI + contract files
- `contracts/openapi.yaml` — dump `app.openapi()` to YAML via script `backend/scripts/export_openapi.py`.
- `contracts/api-spec.md` — hand-written human docs with example JSON for every endpoint, auth header format, error schema, pagination notes (there are none, but document).
- `contracts/backend-env.md` — every env var with purpose, example, default.
- `contracts/backend-url.md` — `http://localhost:8000` for dev; staging URL after deploy (or "not deployed" placeholder).

### Step 15 — Deploy (optional but PRD-preferred)
- Add `Procfile`: `web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
- Railway or Render: connect repo, set env vars, deploy.
- Update `contracts/backend-url.md` with live URL.

### Step 16 — Verification + handoff
- Run `pytest backend/tests -k "not live"` → all green.
- Run `python backend/tests/ab_harness.py` (at least a 4-generation smoke variant) → `report.html` renders.
- Confirm all four contract files present and non-empty.
- Update Phase 1 `README.md` with pointer to `backend/README.md` if helpful.

---

## Critical Files to Reuse from Phase 1

| Phase 1 asset | Reuse in Phase 2 | Why |
|---|---|---|
| `database/db.py:20-22` (IPv4 getaddrinfo hack) | `backend/db.py` | Supabase IPv6 timeout fix |
| `database/seed/processors/embedder.py` | `backend/embeddings.py` | Same CLIP model; keeps retrieval and seed consistent per PRD §Tech Stack |
| `contracts/schema.md` | `backend/models.py` | Authoritative column list |
| Supabase Storage public URLs (already populated in `reference_images.source_url`) | `/retrieve/references` response | No re-upload needed |

---

## Open Decisions (flag before Step 1)

1. **Deployment target** — Railway, Render, or local-only? Affects Step 15 and `backend-url.md`.
2. **JWT secret source** — generated once and stored in `.env`, or pulled from a secret manager? Local dev = env var is fine.
3. **Storage path** — stick with local `./data` for MVP as PRD says, or cut over to Supabase Storage for outputs too? Recommend local for MVP.
4. **A/B harness smoke size** — real PRD asks for 120 drafts + 20 full flows. On free tier that's near the daily quota. Confirm we run full scope or a reduced smoke (e.g. 20 drafts + 4 full flows) for initial delivery.
5. **Gemini image model IDs in SDK** — PRD names `gemini-2.5-flash-image` and `gemini-3-pro-image`. Will verify exact IDs in `google-genai` when implementing Step 7.

---

## Definition of Done (Phase 2)

- [ ] All endpoints return shapes matching `contracts/openapi.yaml` (validated against PRD §API Endpoints).
- [ ] `pytest backend/tests` passes offline (mocked Gemini).
- [ ] `RUN_LIVE_TESTS=1 pytest backend/tests/test_e2e.py` passes end-to-end.
- [ ] `ab_harness.py` produces `report.html` + `metrics.csv`.
- [ ] Human A/B review completed; winning config written back to `MODEL_CONFIG`.
- [ ] `contracts/openapi.yaml` valid OpenAPI 3.1 (`openapi-spec-validator` clean).
- [ ] `contracts/api-spec.md` documents every endpoint with example payloads.
- [ ] `contracts/backend-env.md` lists every env var consumed by code.
- [ ] `contracts/backend-url.md` names the current dev URL (and staging if deployed).
- [ ] `backend/README.md` shows setup, run, test, deploy.

---

## Estimated Effort

| Block | Steps | Est. time |
|---|---|---|
| Skeleton + config + DB + auth | 1–3 | 1.5 h |
| Upload + retrieval + CLIP | 4–5 | 1.5 h |
| Gemini client + generation endpoints | 6–8 | 2.5 h |
| History + admin + metrics | 9–10 | 1 h |
| Tests (unit + E2E) | 12 | 1.5 h |
| A/B harness + 10 test rooms | 13 | 1.5 h |
| Contract files + README + deploy | 14–15 | 1 h |
| Verification | 16 | 0.5 h |
| **Total** | | **~11 h** (matches PRD 8–12 h target) |
