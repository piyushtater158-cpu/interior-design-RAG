# Database Schema Documentation

## Overview

Postgres 17 with pgvector extension, hosted on Supabase. Five tables supporting an AI-powered interior design assistant.

---

## Tables

### `users`

Mock auth table for MVP. All users are demo users.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, auto-generated | Unique user ID |
| `email` | TEXT | UNIQUE, NOT NULL | User email |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Account creation time |
| `is_demo` | BOOLEAN | DEFAULT true | All true for MVP |

**Example row:**
```
id:         a1b2c3d4-e5f6-7890-abcd-ef1234567890
email:      demo@interiordesign.ai
created_at: 2026-04-18T00:00:00+05:30
is_demo:    true
```

---

### `reference_images`

Seed interior design images with metadata, captions, and auto-generated tags.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, auto-generated | Image row ID |
| `source` | TEXT | NOT NULL | Origin: `'local'` or `'synthetic'` |
| `source_id` | TEXT | UNIQUE with source | Filename stem (e.g. `'1'`, `'42'`) |
| `source_url` | TEXT | NOT NULL | Supabase Storage public URL |
| `license` | TEXT | NOT NULL | Always `'owned'` for this dataset |
| `storage_path` | TEXT | NOT NULL | Path in Supabase Storage bucket |
| `caption` | TEXT | nullable | Pre-written image description |
| `room_type` | TEXT | NOT NULL | `'bedroom'`, `'kitchen'`, `'living room'`, `'study room'`, `'kids room'`, `'mandir'`, `'hallway'`, `'dining room'` |
| `style_tags` | TEXT[] | NOT NULL | Array of style names: `['industrial', 'japandi', ...]` |
| `dominant_colors` | TEXT[] | nullable | Hex color codes: `['#e8d4b8', ...]` |
| `detected_objects` | TEXT[] | nullable | Detected items: `['bed', 'lamp', ...]` |
| `quality_score` | FLOAT | nullable | Auto-tag confidence 0.0–1.0 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Insertion timestamp |

**Unique constraint:** `(source, source_id)` — prevents duplicate inserts.

**Example row:**
```
id:               b2c3d4e5-f6a7-8901-bcde-f12345678901
source:           local
source_id:        42
source_url:       https://xxx.supabase.co/storage/v1/object/public/reference-images/minimalist/42.png
license:          owned
storage_path:     minimalist/42.png
caption:          Minimalist style bedroom design with wooden table and green plants
room_type:        bedroom
style_tags:       {minimalist}
dominant_colors:  {#f5f0eb,#8b7355,#2d5a27}
detected_objects: {bed,table,plant,lamp}
quality_score:    0.92
```

---

### `reference_embeddings`

CLIP ViT-B/32 image embeddings for vector similarity search.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, auto-generated | Embedding row ID |
| `reference_image_id` | UUID | FK → reference_images(id), CASCADE | Parent image |
| `embedding_type` | TEXT | NOT NULL | Model identifier: `'clip-vit-b32'` |
| `embedding` | vector(512) | pgvector | 512-dimensional CLIP embedding |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Insertion timestamp |

**Example row:**
```
id:                 c3d4e5f6-a7b8-9012-cdef-123456789012
reference_image_id: b2c3d4e5-f6a7-8901-bcde-f12345678901
embedding_type:     clip-vit-b32
embedding:          [0.0234, -0.1456, 0.0892, ...] (512 floats)
```

**Vector search example:**
```sql
SELECT ri.room_type, ri.caption, 
       1 - (re.embedding <=> '[0.02,...]'::vector) AS similarity
FROM reference_embeddings re
JOIN reference_images ri ON re.reference_image_id = ri.id
ORDER BY re.embedding <=> '[0.02,...]'::vector
LIMIT 5;
```

---

### `generations`

AI-generated design outputs. Populated in Phase 2 (backend).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Generation ID |
| `user_id` | UUID | FK → users(id) | Who requested it |
| `session_id` | TEXT | nullable | Client session grouping |
| `parent_generation_id` | UUID | FK → generations(id) | Edit chain parent |
| `kind` | TEXT | NOT NULL | `'draft'`, `'commit'`, `'edit'` |
| `input_image_path` | TEXT | nullable | User-uploaded room photo |
| `room_type` | TEXT | nullable | Target room type |
| `style_tag` | TEXT | nullable | Target style |
| `reference_image_ids` | UUID[] | nullable | Referenced seed images |
| `prompt` | TEXT | nullable | Full prompt sent to model |
| `model_config` | TEXT | NOT NULL | `'A'` or `'B'` |
| `model_id` | TEXT | nullable | Model identifier |
| `output_image_path` | TEXT | nullable | Generated image path |
| `latency_ms` | INTEGER | nullable | Generation time |
| `cost_usd` | NUMERIC(10,6) | nullable | API cost |
| `status` | TEXT | nullable | `'success'`, `'failed'`, `'retried'` |
| `error_message` | TEXT | nullable | Error details if failed |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Generation timestamp |

---

### `events`

Analytics event log for tracking user interactions.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Event ID |
| `user_id` | UUID | FK → users(id) | Associated user |
| `session_id` | TEXT | nullable | Client session |
| `event_type` | TEXT | NOT NULL | Event category |
| `payload` | JSONB | nullable | Flexible event data |
| `created_at` | TIMESTAMPTZ | DEFAULT now() | Event timestamp |

**Event types:** `'session_start'`, `'upload'`, `'retrieve'`, `'draft_ok'`, `'edit_ok'`, `'commit_ok'`, `'download'`, `'error'`

---

## Indexes

| Name | Table | Type | Columns | Purpose |
|---|---|---|---|---|
| `idx_ref_room_type` | reference_images | B-tree | `room_type` | Filter by room |
| `idx_ref_style_tags` | reference_images | GIN | `style_tags` | Array containment queries |
| `idx_ref_quality` | reference_images | B-tree | `quality_score` | Quality filtering |
| `idx_ref_embeddings_hnsw` | reference_embeddings | HNSW | `embedding` (cosine) | Vector similarity search |
| `idx_gen_user_session` | generations | B-tree | `(user_id, session_id, created_at DESC)` | User session lookup |
| `idx_gen_parent` | generations | B-tree | `parent_generation_id` | Edit chain traversal |
| `idx_events_user_time` | events | B-tree | `(user_id, created_at DESC)` | User event history |
