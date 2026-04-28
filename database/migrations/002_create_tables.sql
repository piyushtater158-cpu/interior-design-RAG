-- Phase 1: Create all tables

-- Users (mock auth for MVP)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    is_demo BOOLEAN DEFAULT true
);

-- Reference images (seed interior design images)
CREATE TABLE IF NOT EXISTS reference_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,                       -- 'local', 'synthetic'
    source_id TEXT,                              -- filename stem e.g. '1', '2'
    source_url TEXT NOT NULL,                    -- Supabase Storage public URL
    license TEXT NOT NULL,                       -- 'owned'
    storage_path TEXT NOT NULL,                  -- path in Supabase Storage bucket
    caption TEXT,                                -- pre-written caption from .txt file
    room_type TEXT NOT NULL,                     -- 'bedroom', 'dining', 'kitchen', 'mandir', etc.
    style_tags TEXT[] NOT NULL,                  -- ['scandinavian', 'minimalist', ...]
    dominant_colors TEXT[],                      -- ['#e8d4b8', ...] — optional
    detected_objects TEXT[],                     -- ['bed', 'lamp', ...] — optional
    quality_score FLOAT,                         -- auto-tag confidence 0–1
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_source_source_id UNIQUE (source, source_id)
);

-- Reference embeddings (CLIP vectors)
CREATE TABLE IF NOT EXISTS reference_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_image_id UUID NOT NULL REFERENCES reference_images(id) ON DELETE CASCADE,
    embedding_type TEXT NOT NULL,                -- 'clip-vit-b32'
    embedding vector(512),                       -- pgvector type, CLIP ViT-B/32 dim
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Generations (AI-generated design outputs)
CREATE TABLE IF NOT EXISTS generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id TEXT,                             -- client session grouping
    parent_generation_id UUID REFERENCES generations(id),  -- for edit chain
    kind TEXT NOT NULL,                          -- 'draft', 'commit', 'edit'
    input_image_path TEXT,                       -- user-uploaded room photo path
    room_type TEXT,
    style_tag TEXT,
    reference_image_ids UUID[],                  -- which references were used
    prompt TEXT,                                 -- full prompt sent to model
    model_config TEXT NOT NULL,                  -- 'A' or 'B'
    model_id TEXT,                               -- e.g. 'gemini-2.5-flash-image'
    output_image_path TEXT,
    latency_ms INTEGER,
    cost_usd NUMERIC(10, 6),
    status TEXT,                                 -- 'success', 'failed', 'retried'
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Events (analytics)
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id TEXT,
    event_type TEXT NOT NULL,                    -- 'session_start', 'upload', etc.
    payload JSONB,                               -- flexible event data
    created_at TIMESTAMPTZ DEFAULT now()
);
