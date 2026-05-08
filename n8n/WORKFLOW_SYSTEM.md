# Interior Design RAG — n8n Backend: Every Linear Flow

Node-by-node explanation of every linear flow in the backend. This walks through all 13 HTTP endpoints and the 4 shared sub-workflows that compose them. Everything here has been merged into one consolidated n8n workflow (`JbnB5CPdoqgCl75F`, 220 nodes) — but each endpoint is still a distinct linear path through the canvas, namespaced by `ns::` (e.g. `draft::Validate body`).

The design rules every endpoint follows:
- All write/auth endpoints start with `Verify JWT` (calls `wf_supabase_verify`, rejects with 401 if absent/bad/expired).
- Auth uses **Supabase Auth** — tokens are verified by hitting `https://uzghfpxboktnbcbbthns.supabase.co/auth/v1/user` with the bearer token. No custom secret or HMAC involved.
- Validation errors short-circuit to `Respond 400`/`413`; parent-not-found → `404`; over-limit → `403`; upstream failures → `502`.
- Success always includes a fire-and-forget `Log event` to the `events` table.
- Credentials are **baked into code nodes at build time** (SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY, ADMIN_TOKEN) because the n8n task-runner sandbox blocks `$env`. HTTP nodes reference them via a per-branch `ns::Config` Code node that exposes `_cfg.*`.

> **Auto-sync:** The node tables in every section below are regenerated automatically from the workflow JSON files by `n8n/sync_workflow_docs.py`. The script runs via a Claude Code `PostToolUse` hook after any `Write` or `Edit` tool call. Only content between `<!-- WFSYNC:stem:START -->` / `<!-- WFSYNC:stem:END -->` markers is replaced — all prose is preserved.

---

## 1. Health — `GET /webhook/health`

Two-node flow, no auth, no external calls.

<!-- WFSYNC:health:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `GET /health` | Webhook | Receive `GET /webhook/health` |
| 2 | `Respond OK` | Respond | Respond 200 — ={{ JSON.stringify({ status: 'ok', backend: 'n8n-interior-de |
<!-- WFSYNC:health:END -->

Used by monitoring, container orchestrators, and smoke tests.

---

## 2. Auth — Supabase Magic Link

**Removed** — `POST /webhook/auth/magic-link` is no longer used. Auth is handled directly by Supabase Auth:

- Frontend calls `supabase.auth.signInWithOtp({ email })` → Supabase sends the magic link email.
- User clicks the link → redirects to `/auth/callback` (Next.js) or `window.origin/` (mobile) with `#access_token=...` in the URL hash.
- `detectSessionInUrl: true` resolves the session automatically. The access token is a standard Supabase JWT.
- All n8n protected endpoints verify the token via `wf_supabase_verify` (ID: `56BlN6jqFkXVszX2`), which calls `GET /auth/v1/user` on the Supabase project.

**Deleted workflows:** `wf_jwt_sign`, `wf_jwt_verify`, `auth_magic_link` (archived on server).

---

## 3. Token verify — `GET /webhook/auth/me`

Header: `Authorization: Bearer <jwt>` → returns the caller's `{ user_id, email }`.

<!-- WFSYNC:auth_me:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `GET /auth/me` | Webhook | Receive `GET /webhook/auth/me` |
| 2 | `Verify JWT` | SubWF | Call sub-workflow `56BlN6jqFkXVszX2` (sync) |
| 3 | `Token valid?` | IF | Route on `={{ $json.ok }}` equals |
| 4 | `Fetch user` | HTTP | `GET` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/users?id=eq.…&select |
| 5 | `Respond 401` | Respond | Respond 401 — ={{ JSON.stringify({ error: $json.error, code: $json.code }) |
| 6 | `Shape response` | Code | Code |
| 7 | `Respond` | Respond | Respond ={{ $json._status }} — ={{ JSON.stringify($json._body) }} |
<!-- WFSYNC:auth_me:END -->

---

## 4. Upload room photo — `POST /webhook/uploads/room-photo`

Multipart upload (binary field `file`) of a room photo. Stores in `user-uploads/<user_id>/<upload_id>`.

<!-- WFSYNC:uploads_room_photo:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `POST /uploads/room-photo` | Webhook | Receive `POST /webhook/uploads/room-photo` |
| 2 | `Verify JWT` | SubWF | Call sub-workflow `56BlN6jqFkXVszX2` (sync) |
| 3 | `Token valid?` | IF | Route on `={{ $json.ok }}` equals |
| 4 | `Validate + name` | Code | Input: verify step returned { ok, user_id, email }. |
| 5 | `Respond 401` | Respond | Respond 401 — ={{ JSON.stringify({ error: $json.error, code: $json.code }) |
| 6 | `Validation error?` | IF | Route on `={{ $json._error || '' }}` notEmpty |
| 7 | `Respond validation err` | Respond | Respond ={{ $json._error.status }} — ={{ JSON.stringify($json._error.body) }} |
| 8 | `Upload to storage` | HTTP | `POST` =https://uzghfpxboktnbcbbthns.supabase.co/storage/v1/object/user-uploa |
| 9 | `Build preview_url` | Code | Build the public URL for the uploaded object. |
| 10 | `Log event` | SubWF | Call sub-workflow `Hycihwac8DqZzBje` (fire-and-forget) |
| 11 | `Respond 200` | Respond | Respond 200 — ={{ JSON.stringify({ upload_id: $json.upload_id, preview_url |
<!-- WFSYNC:uploads_room_photo:END -->

---

## 5. Retrieve references — `POST /webhook/retrieve/references`

Body: `{ upload_id, room_type?, style_tag?, prompt?, k?, session_id? }`.

**Embedding strategy — three-field text + image query vector:**

`Build embeddings request` builds a combined text string from all three available context fields:

```
textInput = prompt + ". style: " + style_tag + ". room type: " + room_type
```

Any combination of the three fields is supported — e.g. only `style_tag`, only `prompt`, all three together. The text string and the image data URI are then sent as `input: [textInput, imageDataUri]` to Nemotron VL 1B v2, which returns **two** 2048-dim embeddings. `Shape vector` averages them into a single 2048-dim query vector.

This means the vector search retrieves reference images that are nearest to the **combined semantic space** of the user's design intent (prompt), their target aesthetic (style_tag), and the room category (room_type) — not just visual similarity to the upload alone.

When no text context is present at all (no prompt, no style_tag, no room_type), the embedder falls back to `input: [imageDataUri]` — image-only retrieval.

After the vector search, `Prompt Re-rank` calls the LLM (retriever_model) to semantically re-order the candidates using the raw `prompt` text. This is a second-pass refinement on top of the vector ranking.

**Prompt parsing:** `Validate body` extracts `body.prompt`, `body.style_tag`, `body.room_type`, and `body.session_id` using the single-key-wrap parser so malformed Content-Type submissions are handled. All four fields are on `ctx.*` and available to every downstream node — embedding, re-ranking, and the fire-and-forget `Call generate/draft` trigger.

<!-- WFSYNC:retrieve_references:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `POST /retrieve/references` | Webhook | Receive `POST /webhook/retrieve/references` |
| 2 | `Config` | Code | Code |
| 3 | `Verify JWT` | Code | Code |
| 4 | `Token valid?` | IF | Route on `={{ $json.ok }}` equals |
| 5 | `Validate body` | Code | Code |
| 6 | `Respond 401` | Respond | Respond 200 — ={{ JSON.stringify({ error: $json.error, code: $json.code }) |
| 7 | `Body valid?` | IF | Route on `={{ $json._error ? 'err' : '' }}` notEmpty |
| 8 | `Respond 400` | Respond | Respond 200 — ={{ JSON.stringify($json._error.body) }} |
| 9 | `Fetch upload bytes` | HTTP | `GET` =… |
| 10 | `Build embeddings request` | Code | Embed upload image + text query → single 2048-dim vector matching _seed_nemotron_references storage  |
| 11 | `OpenRouter embed` | HTTP | `POST` =… |
| 12 | `Shape vector` | Code | Extract embedding from response; averaging path kept for resilience but normally dataArr.length ===  |
| 13 | `RPC retrieve_references` | HTTP | `POST` =…/rest/v1/rpc/retrieve_references |
| 14 | `Prompt Re-rank` | Code | Re-rank RPC results by semantic relevance to the user prompt; falls back to vector order if no promp |
| 15 | `Aggregate for response` | Code | Shape the final references array (id, url, style_tag, room_type, caption, prompt, similarity) for th |
| 16 | `Log event` | HTTP | `POST` =…/rest/v1/events |
| 17 | `Collect refs for draft` | Code | Package retrieve results to fire-and-forget generate/draft after retrieve response is sent |
| 18 | `Respond 200` | Respond | Respond 200 — ={{ JSON.stringify({ references: $json }) }} |
| 19 | `Call generate/draft` | HTTP | `POST` https://n8n.srv1649259.hstgr.cloud/webhook/generate/draft |
<!-- WFSYNC:retrieve_references:END -->

---

## 6. Generate draft — `POST /webhook/generate/draft`

Body: `{ upload_id, reference_image_ids[], room_type, style_tag, prompt?, session_id?, criteria? }`. Gemini takes the empty room + 3 refs and returns a designed room.

<!-- WFSYNC:generate_draft:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `POST /generate/draft` | Webhook | Receive `POST /webhook/generate/draft` |
| 2 | `Sticky Note` | stickyNote | stickyNote |
| 3 | `Config` | Code | Code |
| 4 | `Verify JWT` | Code | Code |
| 5 | `Token valid?` | IF | Route on `={{ $json.ok }}` equals |
| 6 | `Validate body` | Code | Code |
| 7 | `Respond 401` | Respond | Respond 200 — ={{ JSON.stringify({ error: $json.error, code: $json.code }) |
| 8 | `Body valid?` | IF | Route on `={{ $json._error ? 'err' : '' }}` notEmpty |
| 9 | `Respond 400` | Respond | Respond 200 — ={{ JSON.stringify($json._error.body) }} |
| 10 | `Fetch reference URLs` | HTTP | `GET` =…/rest/v1/reference_images…&select=id,source_url |
| 11 | `Order fetch list` | Code | Ordered list of URLs to fetch: upload first, then references in order. |
| 12 | `Fetch image bytes` | HTTP | `GET` =… |
| 13 | `Collect image parts` | Code | Code |
| 14 | `Fetch image_model` | HTTP | `GET` =…/rest/v1/app_config?key=eq.image_model&select=value |
| 15 | `Build Gemini request` | Code | $json is the single row from Fetch image_model: {value: 'model-name'} |
| 16 | `Call Gemini` | HTTP | `POST` =https://generativelanguage.googleapis.com/v1beta/models/…:generateCon |
| 17 | `Extract output PNG` | Code | Code |
| 18 | `Gen error?` | IF | Route on `={{ $json._error ? 'err' : '' }}` notEmpty |
| 19 | `Respond 502` | Respond | Respond 200 — ={{ JSON.stringify($json._error.body) }} |
| 20 | `Assemble row` | Code | Code |
| 21 | `Upload PNG` | HTTP | `POST` =… |
| 22 | `Insert generation row` | HTTP | `POST` =…/rest/v1/generations |
| 23 | `Build gen response` | Code | Code |
| 24 | `Respond 200` | Respond | Respond 200 — ={{ JSON.stringify({   generation_id: $json.generation_id,   |
| 25 | `Log event` | HTTP | `POST` =…/rest/v1/events |
<!-- WFSYNC:generate_draft:END -->

---

## 7. Generate edit — `POST /webhook/generate/edit`

Body: `{ generation_id, instruction }`. Takes an existing generation as the parent and asks Gemini to apply a natural-language edit. Chain depth capped at 6.

<!-- WFSYNC:generate_edit:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `POST /generate/edit` | Webhook | Receive `POST /webhook/generate/edit` |
| 2 | `Verify JWT` | SubWF | Call sub-workflow `56BlN6jqFkXVszX2` (sync) |
| 3 | `Token valid?` | IF | Route on `={{ $json.ok }}` equals |
| 4 | `Validate body` | Code | Code |
| 5 | `Respond 401` | Respond | Respond 401 — ={{ JSON.stringify({ error: $json.error, code: $json.code }) |
| 6 | `Body valid?` | IF | Route on `={{ $json._error }}` notEmpty |
| 7 | `Respond 400` | Respond | Respond ={{ $json._error.status }} — ={{ JSON.stringify($json._error.body) }} |
| 8 | `Fetch parent generation` | HTTP | `GET` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/generations?id=eq.…& |
| 9 | `Shape parent` | Code | Code |
| 10 | `Parent ok?` | IF | Route on `={{ $json._error }}` notEmpty |
| 11 | `Respond parent err` | Respond | Respond ={{ $json._error.status }} — ={{ JSON.stringify($json._error.body) }} |
| 12 | `Chain depth RPC` | HTTP | `POST` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/rpc/generation_chain |
| 13 | `Check cap` | Code | Parent itself consumes depth N ancestors; this new edit adds 1 more. |
| 14 | `Under cap?` | IF | Route on `={{ $json._error }}` notEmpty |
| 15 | `Respond cap exceeded` | Respond | Respond ={{ $json._error.status }} — ={{ JSON.stringify($json._error.body) }} |
| 16 | `Fetch parent PNG` | HTTP | `GET` =… |
| 17 | `Build Gemini request` | Code | Code |
| 18 | `Fetch image_model` | HTTP | `GET` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/app_config?key=eq.im |
| 19 | `Attach model` | Code | Code |
| 20 | `Call Gemini` | HTTP | `POST` =https://generativelanguage.googleapis.com/v1beta/models/…:generateCon |
| 21 | `Extract output PNG` | Code | Code |
| 22 | `Extract ok?` | IF | Route on `={{ $json._error }}` notEmpty |
| 23 | `Respond 502` | Respond | Respond ={{ $json._error.status }} — ={{ JSON.stringify($json._error.body) }} |
| 24 | `Save generation` | SubWF | Call sub-workflow `CdB8jeEoxr2p3Nht` (sync) |
| 25 | `Log event` | SubWF | Call sub-workflow `Hycihwac8DqZzBje` (fire-and-forget) |
| 26 | `Respond 200` | Respond | Respond 200 — ={{ JSON.stringify({   generation_id: $json.generation_id,   |
<!-- WFSYNC:generate_edit:END -->

---

## 8. Generate commit — `POST /webhook/generate/commit`

Body: `{ parent_generation_id }`. Produces a polished "final deliverable" from an existing generation.

<!-- WFSYNC:generate_commit:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `POST /generate/commit` | Webhook | Receive `POST /webhook/generate/commit` |
| 2 | `Verify JWT` | SubWF | Call sub-workflow `56BlN6jqFkXVszX2` (sync) |
| 3 | `Token valid?` | IF | Route on `={{ $json.ok }}` equals |
| 4 | `Validate body` | Code | Code |
| 5 | `Respond 401` | Respond | Respond 401 — ={{ JSON.stringify({ error: $json.error, code: $json.code }) |
| 6 | `Body valid?` | IF | Route on `={{ $json._error }}` notEmpty |
| 7 | `Respond 400` | Respond | Respond ={{ $json._error.status }} — ={{ JSON.stringify($json._error.body) }} |
| 8 | `Fetch parent generation` | HTTP | `GET` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/generations?id=eq.…& |
| 9 | `Shape parent` | Code | Code |
| 10 | `Parent ok?` | IF | Route on `={{ $json._error }}` notEmpty |
| 11 | `Respond parent err` | Respond | Respond ={{ $json._error.status }} — ={{ JSON.stringify($json._error.body) }} |
| 12 | `Fetch reference URLs` | HTTP | `GET` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/reference_images?id= |
| 13 | `Order fetch list` | Code | Build ordered fetch list: parent input (original room), then parent output, |
| 14 | `Fetch image bytes` | HTTP | `GET` =… |
| 15 | `Collect image parts` | Code | Code |
| 16 | `Fetch image_model` | HTTP | `GET` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/app_config?key=eq.im |
| 17 | `Build Gemini request` | Code | Code |
| 18 | `Call Gemini` | HTTP | `POST` =https://generativelanguage.googleapis.com/v1beta/models/…:generateCon |
| 19 | `Extract output PNG` | Code | Code |
| 20 | `Gen error?` | IF | Route on `={{ $json._error }}` notEmpty |
| 21 | `Respond 502` | Respond | Respond ={{ $json._error.status }} — ={{ JSON.stringify($json._error.body) }} |
| 22 | `Save generation` | SubWF | Call sub-workflow `CdB8jeEoxr2p3Nht` (sync) |
| 23 | `Log event` | SubWF | Call sub-workflow `Hycihwac8DqZzBje` (fire-and-forget) |
| 24 | `Respond 200` | Respond | Respond 200 — ={{ JSON.stringify({   generation_id: $json.generation_id,   |
<!-- WFSYNC:generate_commit:END -->

---

## 9. Generate orchestrated — `POST /webhook/generate/orchestrated`  ← PRIMARY GENERATION PATH

Body: `{ upload_id, brief, style_tag?, room_type?, session_id? }`.

**This is the primary generation path.** When the user uploads a photo, selects a style, and writes a brief, this endpoint handles everything in a single call — no separate retrieve step needed.

Three-agent pipeline:
- **Agent 1 (Orchestrator)**: Reads upload image + brief + optional style_tag. Produces `===CRITERIA===` (3D spatial structure notes + style intent for Agent 2) and `===PROMPT===` (Gemini generation brief). Also derives `fts_search_text` (brief + style + room) for pool pre-filtering.
- **Agent 2 (Spatial-aware Retriever)**: Receives candidate pool cards that include `caption_enhanced` + `spatial_signature` JSONB. Picks 3 references: Reference 1 → spatial/layout match, Reference 2 → style/materials match, Reference 3 → lighting/ambience match.
- **Agent 3 (Gemini)**: Generates the final designed-room image from Agent 1's prompt + [upload, ref1, ref2, ref3] images.

**Pool fetching**: Uses `retrieve_candidates_text` Supabase RPC (FTS on `caption_enhanced`) instead of vector similarity — no 2048-dim sequential scan needed. Falls back to quality-ordered unfiltered pool if FTS yields < 3 results.

**Edit flow after this**: Call `POST /generate/edit` with the returned `generation_id` to iterate on the result.

<!-- WFSYNC:generate_orchestrated:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `POST /generate/orchestrated` | Webhook | Receive `POST /webhook/generate/orchestrated` |
| 2 | `Verify JWT` | SubWF | Call sub-workflow `56BlN6jqFkXVszX2` (sync) |
| 3 | `Token valid?` | IF | Route on `={{ $json.ok }}` equals |
| 4 | `Validate body` | Code | Code |
| 5 | `Respond 401` | Respond | Respond 200 — ={{ JSON.stringify({ error: $json.error, code: $json.code }) |
| 6 | `Body valid?` | IF | Route on `={{ $json._error }}` notEmpty |
| 7 | `Respond 400` | Respond | Respond 200 — ={{ JSON.stringify($json._error.body) }} |
| 8 | `Fetch & encode upload` | Code | Code |
| 9 | `Build Agent 1 request` | Code | Code |
| 10 | `Agent 1 (Orchestrator)` | HTTP | `POST` =… |
| 11 | `Parse Agent 1` | Code | Code |
| 12 | `Agent 1 ok?` | IF | Route on `={{ $json._error }}` notEmpty |
| 13 | `Respond Agent 1 err` | Respond | Respond 200 — ={{ JSON.stringify($json._error.body) }} |
| 14 | `Log Agent 1` | SubWF | Call sub-workflow `Hycihwac8DqZzBje` (fire-and-forget) |
| 15 | `Fetch candidate pool` | HTTP | `GET` =… |
| 16 | `Check pool` | Code | Code |
| 17 | `Need fallback?` | IF | Route on `={{ $json.pool_fallback }}` equals |
| 18 | `Fetch candidate pool (all)` | HTTP | `GET` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/reference_images?sel |
| 19 | `Build Agent 2 request` | Code | Code |
| 20 | `Shape pool (fallback)` | Code | Code |
| 21 | `Agent 2 build ok?` | IF | Route on `={{ $json._error }}` notEmpty |
| 22 | `Respond pool err` | Respond | Respond 200 — ={{ JSON.stringify($json._error.body) }} |
| 23 | `Agent 2 (Retriever)` | HTTP | `POST` =… |
| 24 | `Parse Agent 2` | Code | Code |
| 25 | `Agent 2 ok?` | IF | Route on `={{ $json._error }}` notEmpty |
| 26 | `Respond Agent 2 err` | Respond | Respond 200 — ={{ JSON.stringify($json._error.body) }} |
| 27 | `Log Agent 2` | SubWF | Call sub-workflow `Hycihwac8DqZzBje` (fire-and-forget) |
| 28 | `Fetch picked URLs` | HTTP | `GET` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/reference_images?id= |
| 29 | `Order fetch list` | Code | Code |
| 30 | `Fetch image bytes` | HTTP | `GET` =… |
| 31 | `Collect image parts` | Code | Code |
| 32 | `Fetch image_model` | HTTP | `GET` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/app_config?key=eq.im |
| 33 | `Build Gemini request` | Code | Code |
| 34 | `Agent 3 (Gemini)` | HTTP | `POST` =https://generativelanguage.googleapis.com/v1beta/models/…:generateCon |
| 35 | `Extract output PNG` | Code | Code |
| 36 | `Gen error?` | IF | Route on `={{ $json._error }}` notEmpty |
| 37 | `Respond 502` | Respond | Respond 200 — ={{ JSON.stringify($json._error.body) }} |
| 38 | `Save generation` | SubWF | Call sub-workflow `CdB8jeEoxr2p3Nht` (sync) |
| 39 | `Log orchestrated_ok` | SubWF | Call sub-workflow `Hycihwac8DqZzBje` (fire-and-forget) |
| 40 | `Respond 200` | Respond | Respond 200 — ={{ JSON.stringify({   generation_id:       $json.generation |
<!-- WFSYNC:generate_orchestrated:END -->

---

## 10. Session listing — `GET /webhook/generations/session/:session_id`

Returns every generation in one session in chronological order so the UI can render the edit chain.

<!-- WFSYNC:generations_session:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `GET /generations/session/:session_id` | Webhook | Receive `GET /webhook/generations/session/:session_id` |
| 2 | `Verify JWT` | SubWF | Call sub-workflow `56BlN6jqFkXVszX2` (sync) |
| 3 | `Token valid?` | IF | Route on `={{ $json.ok }}` equals |
| 4 | `Validate params` | Code | Code |
| 5 | `Respond 401` | Respond | Respond 401 — ={{ JSON.stringify({ error: $json.error, code: $json.code }) |
| 6 | `Params valid?` | IF | Route on `={{ $json._error }}` notEmpty |
| 7 | `Respond 400` | Respond | Respond ={{ $json._error.status }} — ={{ JSON.stringify($json._error.body) }} |
| 8 | `Fetch session generations` | HTTP | `GET` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/generations?session_ |
| 9 | `Shape response` | Code | Code |
| 10 | `Respond 200` | Respond | Respond 200 — ={{ JSON.stringify($json) }} |
<!-- WFSYNC:generations_session:END -->

---

## 11. Generation export — `POST /webhook/generations/:generation_id/export`

Gives the user a download URL for a specific generation.

<!-- WFSYNC:generations_export:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `POST /generations/:generation_id/export` | Webhook | Receive `POST /webhook/generations/:generation_id/export` |
| 2 | `Verify JWT` | SubWF | Call sub-workflow `56BlN6jqFkXVszX2` (sync) |
| 3 | `Token valid?` | IF | Route on `={{ $json.ok }}` equals |
| 4 | `Validate params` | Code | Code |
| 5 | `Respond 401` | Respond | Respond 401 — ={{ JSON.stringify({ error: $json.error, code: $json.code }) |
| 6 | `Params valid?` | IF | Route on `={{ $json._error }}` notEmpty |
| 7 | `Respond 400` | Respond | Respond ={{ $json._error.status }} — ={{ JSON.stringify($json._error.body) }} |
| 8 | `Fetch generation` | HTTP | `GET` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/generations?id=eq.…& |
| 9 | `Build download URL` | Code | Code |
| 10 | `Row exists?` | IF | Route on `={{ $json._error }}` notEmpty |
| 11 | `Respond 404` | Respond | Respond ={{ $json._error.status }} — ={{ JSON.stringify($json._error.body) }} |
| 12 | `Log event` | SubWF | Call sub-workflow `Hycihwac8DqZzBje` (fire-and-forget) |
| 13 | `Respond 200` | Respond | Respond 200 — ={{ JSON.stringify({ download_url: $json.download_url }) }} |
<!-- WFSYNC:generations_export:END -->

---

## 12. Admin metrics — `GET /webhook/admin/metrics`

Header: `X-Admin-Token: <ADMIN_TOKEN>` — no JWT, admin-token only.

<!-- WFSYNC:admin_metrics:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `GET /admin/metrics` | Webhook | Receive `GET /webhook/admin/metrics` |
| 2 | `Check admin token` | Code | Code |
| 3 | `Token valid?` | IF | Route on `={{ $json._error }}` notEmpty |
| 4 | `Respond error` | Respond | Respond ={{ $json._error.status }} — ={{ JSON.stringify($json._error.body) }} |
| 5 | `RPC admin_metrics` | HTTP | `POST` =https://uzghfpxboktnbcbbthns.supabase.co/rest/v1/rpc/admin_metrics |
| 6 | `Shape response` | Code | admin_metrics RPC returns a single JSONB. PostgREST may wrap it as an array. |
| 7 | `Respond 200` | Respond | Respond 200 — ={{ JSON.stringify($json) }} |
<!-- WFSYNC:admin_metrics:END -->

---

## 13. Seed enhanced captions (manual trigger, not an HTTP endpoint)

One-time (or incremental) population of `caption_enhanced` + `spatial_signature` for the reference image library. Calls `wf_enhance_caption` once per image with a 4-second rate-limit delay between calls (OpenRouter free-tier safe). Skips images that already have `caption_enhanced`. Run this once after applying migration 012.

<!-- WFSYNC:_seed_enhanced_captions:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `Manual trigger` | Manual | Manual trigger (n8n UI) |
| 2 | `Config` | Code | Code |
| 3 | `Fetch all reference_images` | HTTP | `GET` =…/rest/v1/reference_images?select=id,source_url,caption,caption_enhan |
| 4 | `One item per pending row` | Code | Flatten response. Skip images that already have caption_enhanced. |
| 5 | `Process one at a time` | Batch | Process ? at a time |
| 6 | `Enhance caption` | SubWF | Call sub-workflow `wf_enhance_caption` (sync) |
| 7 | `Summary` | Code | splitInBatches done-branch: all items processed. |
| 8 | `Rate limit (4s)` | wait | wait |
<!-- WFSYNC:_seed_enhanced_captions:END -->

---

## 14. Seed Nemotron embeddings (manual trigger, legacy)

One-time population of `reference_embeddings` for the 104 pre-loaded `reference_images`. **Optional in the new pipeline** — embeddings are no longer the primary retrieval signal (replaced by FTS on `caption_enhanced`). Run if you want the old `retrieve_references` endpoint to continue working for fallback. *In this project the seed flow was bypassed and run as a standalone Python script (`n8n/seed_embeddings.py`) because n8n's test-mode loop execution didn't iterate the `splitInBatches` loop.* The flow still lives in the workflow.

<!-- WFSYNC:_seed_nemotron_references:START -->
| Step | Node | Type | What it does |
|---|---|---|---|
| 1 | `Manual trigger` | Manual | Manual trigger (n8n UI) |
| 2 | `Config` | Code | Code |
| 3 | `Fetch all reference_images` | HTTP | `GET` =…/rest/v1/reference_images?select=id,source_url,source_id,caption&ord |
| 4 | `One item per row` | Code | Flatten response into one item per reference image row. |
| 5 | `Batch (3/loop)` | Batch | Process 3 at a time |
| 6 | `Summary` | Code | After Batch drains, summarise counts. |
| 7 | `Fetch image bytes` | HTTP | `GET` =… |
| 8 | `Build embed body` | Code | Build Nemotron embed request: concat caption + dataUri into ONE string (matches retrieve_references  |
| 9 | `OpenRouter embed` | HTTP | `POST` =… |
| 10 | `Shape insert row` | Code | Code |
| 11 | `Has embedding?` | IF | Route on `={{ $json.embedding }}` notEmpty |
| 12 | `Delete existing embedding` | HTTP | `DELETE` =…/rest/v1/reference_embeddings?reference_image_id=eq.…&embedding_type |
| 13 | `Note skip` | Code | Skipped row — keep going. Return a marker so the summary tracks failures. |
| 14 | `Insert embedding` | HTTP | `POST` =…/rest/v1/reference_embeddings |
| 15 | `Loop tail` | Code | Re-enter the batch loop until drained. |
<!-- WFSYNC:_seed_nemotron_references:END -->

---

## Shared sub-workflows (inlined at build time)

All four originally lived as separate n8n workflows and were called via `executeWorkflow`. The build script (`n8n/build_consolidated.py`) now *inlines* them into every branch that used them — so there are zero `executeWorkflow` nodes in the deployed workflow.

- **`wf_jwt_sign`** → 1 Code node. Input `{user_id, email}`. Builds an HS256 JWT using a baked `JWT_SECRET` and a pure-JS SHA-256 + HMAC implementation (no `require('crypto')` because the task-runner sandbox blocks built-ins). Output `{token, user_id, email}`, TTL 24 h.
- **`wf_jwt_verify`** → 1 Code node. Input `{authorization: "Bearer <token>"}`. Splits the token, recomputes HMAC, compares, decodes the payload, checks `exp`. Returns `{ok:true, user_id, email}` or `{ok:false, status:401, error, code}` with distinct codes for each failure class (`missing_token`, `malformed_token`, `invalid_token`, `token_expired`).
- **`wf_event_log`** → 1 HTTP node. Input `{event_type, user_id?, session_id?, payload?}`. Fire-and-forget POST to Supabase `/rest/v1/events` with `Prefer: return=minimal` and `neverError: true` so logging failures never break the caller.
- **`wf_save_generation`** → 4 nodes. Input: full generation fields + binary `output_png`. **(a)** `Assemble row` Code adds `generation_id = crypto.randomUUID()` and builds `output_image_path = user-outputs/<user_id>/<gen_id>.png`. **(b)** `Upload PNG` HTTP PUTs the binary to Supabase Storage with `x-upsert: true`. **(c)** `Insert generation row` HTTP POSTs to `/rest/v1/generations` with `Prefer: return=representation`. **(d)** `Build gen response` composes `{ generation_id, user_id, session_id, kind, parent_generation_id, model_id, latency_ms, cost_usd, room_type, style_tag, output_url, created_at }`.
- **`wf_enhance_caption`** → 7 nodes. Input: `{ reference_image_id, source_url, caption? }`. Fetches the reference image binary, calls OpenRouter vision LLM with a structured prompt, parses `===CAPTION===` (3–5 sentence rich description) and `===SPATIAL===` (JSON with keys: `room_shape`, `depth_cues`, `ceiling_height`, `window_wall`, `light_direction`, `focal_wall`, `floor_visible_pct`, `symmetry`, `open_to`) blocks from the response, then PATCHes `reference_images` with `caption_enhanced`, `spatial_signature`, and `caption_enhanced_at`. Parse failures are logged and swallowed (the loop continues). Called by `_seed_enhanced_captions` during batch seeding and can be called directly whenever a new reference image is imported.

---

## Common building blocks you'll see everywhere

| Block | Where | Role |
|---|---|---|
| `ns::Config` Code node | Right after the webhook of every branch that touches Supabase/OpenRouter/Gemini | Exposes baked creds as `$('ns::Config').first().json._cfg.{supabase_url, supabase_key, gemini_key, openrouter_key, openrouter_base, orch_model, retriever_model, embed_model, admin_token, jwt_secret, jwt_ttl}`. Needed because HTTP nodes can't read `$env` in the sandbox. |
| JWT gate | Every authed endpoint (everything except `/health`, `/auth/magic-link`, `/admin/metrics`) | `Verify JWT` Code → `Token valid?` IF → `Respond 401` on false |
| Validation Code + `Body/Params valid?` IF | Every endpoint with input | Code node returns `{_error:{status, body:{error, code}}}` on failure; the IF routes to a pre-built `Respond <status>` node. Error codes are stable machine strings (`invalid_email`, `chain_too_long`, `missing_upload_id`, ...) |
| `Log event` | Every success path | Fire-and-forget Supabase insert; never blocks the response |
| Supabase REST | All DB reads/writes | Auth via `apikey` + `Authorization: Bearer <service_key>` headers; uses `?on_conflict=` and `Prefer: resolution=merge-duplicates,return=representation` for upserts |
| Supabase Storage | `user-uploads/*`, `user-outputs/*`, `reference-images/*` | Binary PUT/GET through `/storage/v1/object/` |
| Gemini image model | draft, edit, commit, orchestrated | Model ID read from `app_config.key=image_model` at request time, not hard-coded |
| OpenRouter chat | Orchestrator (Agent 1, Agent 2) | `chat/completions` with multimodal `image_url` content |
| OpenRouter embeddings | retrieve, seed | Nemotron VL 1B v2 free; **critical**: `input` must be an array of strings (`[dataUri]` or `[promptText, dataUri]`), not an array of `{type,image_url}` objects. Returns 2048 dims per input item. When multiple items are sent, `Shape vector` averages all returned embeddings into one query vector. |

---

## Verification

1. `curl https://n8n.srv1649259.hstgr.cloud/webhook/health` → `{"status":"ok",...}`
2. `curl -X POST https://n8n.srv1649259.hstgr.cloud/webhook/auth/magic-link -H "Content-Type: application/json" -d '{"email":"you@test.com"}'` → returns `{token, user_id}`
3. `curl https://n8n.srv1649259.hstgr.cloud/webhook/auth/me -H "Authorization: Bearer <token>"` → returns `{user_id, email}`
4. `curl https://n8n.srv1649259.hstgr.cloud/webhook/admin/metrics -H "X-Admin-Token: __REDACTED_ADMIN_TOKEN__"` → returns metrics JSON
5. In the n8n UI (`https://n8n.srv1649259.hstgr.cloud`), open workflow `JbnB5CPdoqgCl75F` → Executions tab → any execution shows the exact nodes that ran and their per-node inputs/outputs.

---

## Auto-sync system

**How the tables stay current:**

```
n8n/workflows/*.json  ──edit──▶  Claude Code PostToolUse hook
                                         │
                                         ▼
                              python n8n/sync_workflow_docs.py
                                         │
                                         ▼
                     WORKFLOW_SYSTEM.md  (only <!-- WFSYNC:…:START/END --> blocks replaced)
```

**Files involved:**
- `n8n/sync_workflow_docs.py` — the sync script (reads JSONs, generates tables, does marker-based replacement)
- `.claude/settings.local.json` — registers the `PostToolUse` hook on `Write|Edit`
- `WORKFLOW_SYSTEM.md` — this file; markers delimit auto-managed table regions

**Rules:**
- Only content **between** `<!-- WFSYNC:stem:START -->` and `<!-- WFSYNC:stem:END -->` is replaced.
- All prose, headings, and sections without markers are never touched by the script.
- The `stem` must match the filename (without `.json`) of the corresponding workflow file.
- If a workflow JSON has no matching marker in this file, the script silently skips it.
- The script is idempotent — running it twice produces the same result.
