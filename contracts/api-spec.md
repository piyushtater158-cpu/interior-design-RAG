# API Specification

**Base URL (dev):** `http://localhost:8000`
**OpenAPI:** `/openapi.json` · machine-readable spec at `contracts/openapi.yaml`
**Interactive docs:** `/docs`

All non-admin endpoints require a JWT in `Authorization: Bearer <token>`. Admin endpoints require `X-Admin-Token: <token>`.

Error shape for unhandled exceptions:

```json
{ "error": "<message>", "code": "internal_error" }
```

FastAPI validation errors use the standard Pydantic 422 shape.

---

## 1. Auth

### POST `/auth/magic-link`

Mock magic-link. Any email upserts into `users` and gets a JWT.

**Request:**
```json
{ "email": "demo@example.com" }
```

**Response 200:**
```json
{ "token": "eyJhbGciOiJIUzI1NiIs...", "user_id": "a1b2c3d4-..." }
```

### GET `/auth/me`

**Headers:** `Authorization: Bearer <token>`

**Response 200:**
```json
{ "user_id": "a1b2c3d4-...", "email": "demo@example.com" }
```

---

## 2. Upload

### POST `/uploads/room-photo`

**Headers:** `Authorization: Bearer <token>`
**Body:** `multipart/form-data` with a `file` field. JPG or PNG, ≤ 10 MB.

**Response 200:**
```json
{ "upload_id": "0a1b2c3d...", "preview_url": "/data/uploads/<user>/0a1b2c3d.png" }
```

**Errors:** `400` empty / wrong extension · `413` > 10 MB.

---

## 3. Retrieval

### POST `/retrieve/references`

CLIP encodes the uploaded photo, filters `reference_images` by `room_type`/`style_tag`, and runs an HNSW cosine search over `reference_embeddings`.

**Request:**
```json
{
  "upload_id": "0a1b2c3d",
  "room_type": "bedroom",
  "style_tag": "minimalist",
  "k": 5
}
```

`room_type` and `style_tag` are both optional — omit either to skip that filter.

**Response 200:**
```json
{
  "references": [
    {
      "id": "b2c3d4e5-...",
      "url": "https://<project>.supabase.co/storage/v1/object/public/reference-images/minimalist/42.png",
      "style_tags": ["minimalist", "scandinavian"],
      "room_type": "bedroom",
      "caption": "Minimalist bedroom...",
      "similarity": 0.87
    }
  ]
}
```

---

## 4. Generation

Every endpoint below returns the same shape:

```json
{
  "generation_id": "<uuid>",
  "output_url": "/data/outputs/<user>/<gen>.png",
  "latency_ms": 4321,
  "cost_usd": 0.0,
  "model_id": "gemini-2.5-flash-image",
  "backend_id": "gemini"
}
```

### POST `/generate/draft`

```json
{
  "upload_id": "0a1b2c3d",
  "room_type": "bedroom",
  "style_tag": "minimalist",
  "reference_ids": ["b2c3d4e5-..."],
  "session_id": "client-session-123"
}
```

### POST `/generate/commit`

```json
{ "generation_id": "<uuid>", "session_id": "client-session-123" }
```

Re-renders the parent with the `commit.txt` prompt (and, for Config B, the pro model).

### POST `/generate/edit`

```json
{
  "generation_id": "<parent uuid>",
  "instruction": "Swap the rug for a natural jute weave",
  "session_id": "client-session-123"
}
```

Edit chains are capped at **6** per parent. Exceeding the cap returns `400`.

---

## 5. History / Export

### GET `/generations/session/{session_id}`

Returns all generations the current user produced in a session, ordered by creation time.

```json
[
  {
    "generation_id": "<uuid>",
    "kind": "draft",
    "output_url": "/data/outputs/<user>/<gen>.png",
    "parent_generation_id": null,
    "model_id": "gemini-2.5-flash-image",
    "created_at": "2026-04-18T10:12:03+00:00"
  }
]
```

### POST `/generations/{generation_id}/export`

```json
{ "download_url": "/data/outputs/<user>/<gen>.png" }
```

---

## 6. Admin

All admin endpoints require `X-Admin-Token`. Missing or bad token → `403`.

### GET `/admin/ab-config`
```json
{ "config": "A", "backend": "gemini", "backend_edit": "" }
```

`backend_edit` is an optional per-kind override — when set, only `kind="edit"` calls use it. Empty string means no override (edits follow `backend`).

### PUT `/admin/ab-config`
```json
{ "config": "B", "backend": "gemini", "backend_edit": "local_gpu" }
```

All fields are optional. Changes take effect immediately across all subsequent generations. Pass `"backend_edit": ""` to clear the edit override.

### POST `/admin/run-ab-test`

Launches `backend/tests/ab_harness.py --smoke` as a background subprocess. Non-blocking.

```json
{ "started": true, "message": "A/B harness launched in smoke mode" }
```

### GET `/admin/metrics`

Rolling 24-hour aggregates.

```json
{
  "window_hours": 24,
  "generation_count": 87,
  "success_count": 85,
  "error_count": 2,
  "by_config": { "A": 50, "B": 37 },
  "latency_p50_ms": 3800.0,
  "latency_p95_ms": 7400.0,
  "gemini_calls_24h": 87,
  "gemini_quota_remaining": 1413
}
```

---

## 7. Health

### GET `/health`
```json
{ "status": "ok", "backend": "interior-design-assistant" }
```

---

## Auth header reference

- User routes: `Authorization: Bearer <jwt>` (obtained from `/auth/magic-link`)
- Admin routes: `X-Admin-Token: <token>` (matches `ADMIN_TOKEN` env var)

## Status codes

| Code | Meaning |
|---|---|
| 200 | OK |
| 400 | Bad request (bad body, invalid UUID, edit chain cap exceeded) |
| 401 | Missing / invalid bearer token |
| 403 | Missing / invalid admin token |
| 404 | upload_id / generation_id not found |
| 413 | Upload exceeds 10 MB |
| 422 | Pydantic validation error (standard FastAPI shape) |
| 500 | Unhandled server error — `{ "error": ..., "code": "internal_error" }` |

## Swappable generation backend

The backend calls a single `ImageGenerator` adapter (`backend/generation/base.py`). Two adapters are shipped:

- `gemini` (default) — uses the `google-genai` SDK with per-model token buckets and exponential backoff on 429.
- `local_gpu` — POSTs to `${LOCAL_GPU_URL}/generate` with `{prompt, kind, config, images_b64}`.

Switch at runtime via `PUT /admin/ab-config {"backend": "local_gpu"}` or via the `IMAGE_BACKEND` env var. Use `backend_edit` / `IMAGE_BACKEND_EDIT` to route only `kind="edit"` to an open-source model while keeping Gemini for draft/commit. Frontend code does not need to change — the response shape is identical for both adapters.
