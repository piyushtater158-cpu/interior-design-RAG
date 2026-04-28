# Backend Environment Variables

The backend loads variables from `<project-root>/.env` (same file the Phase 1 DB script uses). A template is at `backend/.env.example`.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | — | Postgres DSN (Supabase pooler, port 6543). Must be URL-encoded. The backend rewrites `postgresql://` → `postgresql+asyncpg://` at runtime. |
| `SUPABASE_URL` | Yes (for reference URLs) | — | Used only via stored `source_url` values; no direct fetch from the backend today, but kept for parity with Phase 1. |
| `SUPABASE_SERVICE_KEY` | Optional | — | Not used by the current routes — reserved for future Supabase-Storage writes. |
| `GEMINI_API_KEY` | **Yes** (when `IMAGE_BACKEND=gemini`) | falls back to `GOOGLE_AI_STUDIO_KEY` | Google AI Studio key. The backend first checks `GEMINI_API_KEY`, then `GOOGLE_AI_STUDIO_KEY`. |
| `JWT_SECRET` | **Yes** | `__REDACTED_JWT_SECRET__` | HS256 signing secret for the mock magic-link JWT. Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. |
| `JWT_TTL_HOURS` | No | `24` | Access-token lifetime. |
| `IMAGE_BACKEND` | No | `gemini` | `gemini` or `local_gpu`. Default adapter for all generation kinds. |
| `IMAGE_BACKEND_EDIT` | No | empty | Per-kind override — when set to `gemini` or `local_gpu`, only `kind="edit"` calls route here (draft/commit still use `IMAGE_BACKEND`). Empty = no override. Used to send edits to an open-source model (e.g. Qwen-Image-Edit) while keeping Gemini for draft/commit. |
| `LOCAL_GPU_URL` | Required when any backend is `local_gpu` | empty | Base URL of the BPA-provisioned GPU (or any self-hosted) instance exposing `POST /generate`. |
| `MODEL_CONFIG` | No | `A` | `A` (flash-image for all kinds) or `B` (pro for `commit`). Also togglable at runtime via `PUT /admin/ab-config`. |
| `STORAGE_PATH` | No | `./backend/data` | Root for uploads / outputs. Mounted at `/data` as FastAPI `StaticFiles`. |
| `ADMIN_TOKEN` | **Yes** | `dev-admin-token` | Required in `X-Admin-Token` header for all `/admin/*` routes. |
| `GEMINI_QUOTA_DAILY` | No | `1500` | Used by `/admin/metrics` to report remaining free-tier quota. Does not gate calls. |
| `RUN_LIVE_TESTS` | No | `0` | Set to `1` to enable live Gemini + DB e2e tests in `backend/tests/test_e2e.py`. |

## Generating secrets

```bash
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ADMIN_TOKEN=' + secrets.token_urlsafe(32))"
```

## Switching the generation backend

```bash
# Flip everything to the BPA GPU
echo 'IMAGE_BACKEND=local_gpu' >> .env
echo 'LOCAL_GPU_URL=https://<bpa-host>:8080' >> .env

# Or route only edits to the open-source model, leave draft/commit on Gemini
echo 'IMAGE_BACKEND=gemini' >> .env
echo 'IMAGE_BACKEND_EDIT=local_gpu' >> .env
echo 'LOCAL_GPU_URL=https://<edit-host>:8080' >> .env

# Or at runtime — no restart required
curl -X PUT http://localhost:8000/admin/ab-config \
     -H "X-Admin-Token: $ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"backend": "gemini", "backend_edit": "local_gpu"}'
```

See `backend/README.md` § "Switching to the BPA GPU" for the full procedure.
