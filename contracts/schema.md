# Database Schema Documentation

## Overview

Postgres on **Supabase** (no `pgvector`, no FTS). Tables: `users`, `reference_images`, `generations`, `events`, `app_config`.

Auth: **Google OAuth via Supabase Auth** (`auth.users` is Supabase-managed). Every `public.*` table is RLS-enabled with strict `owner_id = auth.uid()` — no NULL escape hatch.

Reference retrieval is an **inline PostgREST query** inside `generate_orchestrated` (no `retrieve_candidates_text` RPC, no `caption_fts` column). Query pattern:

```
GET /rest/v1/reference_images
  ?owner_id=eq.<uid>
  &room_type=eq.<room>
  &style_tags=cs.{<style>}
  &select=id,source_url,caption,spatial_signature
  &order=created_at.desc&limit=20
```

Canonical DDL: `contracts/schema.sql` (mirrors `supabase/migrations/100_reset_and_rebuild.sql`).

---

## Tables

### `users`

Mirror of `auth.users`, populated by an `AFTER INSERT` trigger on `auth.users`.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, FK → auth.users (cascade) | Supabase Auth user ID |
| `email` | TEXT | NOT NULL | Synced from Google identity |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Account creation time |

RLS: `SELECT` where `auth.uid() = id`.

---

### `reference_images`

Per-user reference catalog. Every row is owned by exactly one `auth.users` row.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Row ID |
| `owner_id` | UUID | NOT NULL, FK → auth.users (cascade) | Row owner — RLS key |
| `owner_email` | TEXT | nullable | Synced by trigger from auth.users |
| `source` | TEXT | NOT NULL | `'studio'` (user uploads) or `'local'` (seed) |
| `source_id` | TEXT | NOT NULL | UUID assigned at upload time |
| `source_url` | TEXT | NOT NULL | Public or signed URL |
| `license` | TEXT | nullable | e.g. `'owned'` |
| `storage_path` | TEXT | NOT NULL | Path inside `reference-images` bucket |
| `caption` | TEXT | nullable | Prose caption from `qwen/qwen3-vl-8b-instruct` |
| `spatial_signature` | JSONB | nullable | Structured 3D layout extraction (see below) |
| `room_type` | TEXT | NOT NULL, CHECK | One of the 6 valid room slugs |
| `style_tags` | TEXT[] | NOT NULL, CHECK | Singleton array — exactly 1 of 6 valid styles |
| `dominant_colors` | TEXT[] | nullable | Hex palette (tagger output) |
| `detected_objects` | TEXT[] | nullable | Object labels (tagger output) |
| `quality_score` | NUMERIC | nullable | 0–1 confidence score |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Insert time |

**Unique:** `(owner_id, source, source_id)`.

**CHECK constraints:**

```sql
check (room_type in ('bedroom','kids room','dining room','kitchen','mandir','living room'))
check (cardinality(style_tags) = 1
       and style_tags[1] in ('scandinavian','japandi','midcentury','traditional','industrial','boho'))
```

**RLS:** SELECT/INSERT/UPDATE/DELETE all require `owner_id = auth.uid()`. No service-role bypass for user-facing reads.

**`spatial_signature` shape** (written by `caption_generate` workflow):

```jsonc
{
  "declared_style": "scandinavian",       // verbatim copy of style_tag input
  "declared_room_type": "bedroom",        // verbatim copy of room_type input
  "style_signals_observed": ["..."],      // visible elements justifying the style
  "room_shape": "rectangular",
  "perceived_proportions": { "width_to_depth": "wider" },
  "ceiling": { "height": "standard", "treatment": null },
  "walls_visible": ["left", "rear"],
  "openings": [{ "wall": "rear", "type": "window", "approx_count": 1 }],
  "natural_light": { "direction": "front-left", "intensity": "medium" },
  "flooring": { "material": "hardwood", "coverage": "full" },
  "furniture": [{ "type": "bed", "wall_relation": "rear wall" }],
  "fixed_features": []
}
```

`declared_style` and `declared_room_type` are hard-validated at write time against the workflow's input tags — mismatches return 502 `tag_mismatch` and no DB row is inserted.

---

### `generations`

AI-generated design outputs.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Generation ID |
| `user_id` | UUID | NOT NULL, FK → auth.users (cascade) | Owner |
| `session_id` | TEXT | nullable | Client session ID |
| `parent_id` | UUID | FK → generations(id) ON DELETE SET NULL | Edit chain parent |
| `prompt` | TEXT | nullable | Model prompt text |
| `style_tag` | TEXT | CHECK (∈ 6 or NULL) | Target style |
| `room_type` | TEXT | CHECK (∈ 6 or NULL) | Target room |
| `output_storage_path` | TEXT | nullable | Output in `user-outputs` bucket |
| `output_url` | TEXT | nullable | Public/signed URL of output |
| `picked_refs` | JSONB | nullable | Array of 3 reference_image ids selected by orchestrator |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Created |

RLS: SELECT/INSERT/UPDATE/DELETE all require `auth.uid() = user_id`.

---

### `events`

Audit / analytics log.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Event ID |
| `user_id` | UUID | FK → auth.users ON DELETE SET NULL | Optional owner |
| `event_type` | TEXT | NOT NULL | Category string |
| `payload` | JSONB | nullable | Arbitrary event data |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Event time |

RLS: INSERT requires `auth.uid() = user_id`. No SELECT policy for clients — analytics reads use service role only.

---

### `app_config`

Key/value store for model IDs and feature flags.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `key` | TEXT | PK | Config key |
| `value` | TEXT | NOT NULL | Config value |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Set time |

RLS: SELECT public (any role). INSERT/UPDATE: service role only (no client policy).

Seeded values:

| Key | Value |
|---|---|
| `caption_model` | `qwen/qwen3-vl-8b-instruct` |
| `orchestrator_model` | `google/gemini-2.5-flash` |
| `image_model` | `google/gemini-3.1-flash-image-preview` |

---

## Indexes

| Name | Table | Type | Columns | Purpose |
|---|---|---|---|---|
| `idx_ref_owner` | reference_images | B-tree | `owner_id` | Owner lookup |
| `idx_ref_room` | reference_images | B-tree | `(owner_id, room_type)` | Per-user room filter |
| `idx_ref_style` | reference_images | GIN | `style_tags` | Array containment |
| `idx_ref_spatial` | reference_images | GIN | `spatial_signature` | JSON containment |
| `idx_gen_user_time` | generations | B-tree | `(user_id, created_at DESC)` | Session history |
| `idx_gen_session` | generations | B-tree | `session_id` (partial: NOT NULL) | Session lookup |
| `idx_events_user` | events | B-tree | `(user_id, created_at DESC)` | User timeline |

No FTS index. No `caption_fts` column. No `retrieve_candidates_text` RPC.

---

## Storage Buckets

All buckets are **private** (not public). Signed URLs or service-role access required.

| Bucket | Path pattern | Purpose |
|---|---|---|
| `reference-images` | `studio/{user_id}/{style}/{room}/{uuid}.{ext}` | User-uploaded reference images |
| `user-uploads` | `{user_id}/{upload_id}` | Room photos uploaded for generation |
| `user-outputs` | `outputs/{user_id}/{uuid}.png` | AI-generated design outputs |

Storage RLS scopes by `split_part(name, '/', 2) = auth.uid()::text` for `reference-images` and by `split_part(name, '/', 1) = auth.uid()::text` for the other two.

---

## Triggers

| Trigger | Table | When | Function | Effect |
|---|---|---|---|---|
| `on_auth_user_created` | `auth.users` | AFTER INSERT | `handle_new_user()` | Mirrors row into `public.users` (upsert) |
| `tr_reference_images_sync_owner_email` | `public.reference_images` | BEFORE INSERT OR UPDATE OF owner_id | `reference_images_sync_owner_email()` | Syncs `owner_email` from `auth.users` |

---

## Auth

- Provider: **Google OAuth** via Supabase Auth (`signInWithOAuth({ provider: 'google' })`).
- Session token: Supabase JWT issued after Google consent. Stored in `localStorage` via Supabase client.
- n8n verification: every webhook calls `wf_supabase_verify` sub-workflow which hits Supabase `/auth/v1/user` with the bearer token. No hand-rolled JWT decode in n8n.
- RLS: downstream DB reads use the **user's session bearer + supabase anon key** so `auth.uid()` resolves inside RLS policies. Service role key is only used for storage uploads (server-side, non-user-facing operations).
