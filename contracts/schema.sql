-- =============================================================
-- Interior Design Assistant — Full Database Schema (DDL)
-- Generated from Phase 1 migrations
-- =============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================
-- Table: users
-- Mock auth users for MVP
-- =============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    is_demo BOOLEAN DEFAULT true
);

-- =============================================================
-- Table: reference_images
-- Seed interior design images with metadata and tags
-- =============================================================
CREATE TABLE IF NOT EXISTS reference_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,                       -- 'local', 'synthetic'
    source_id TEXT,                              -- filename stem e.g. '1', '2'
    source_url TEXT NOT NULL,                    -- Supabase Storage public URL
    license TEXT NOT NULL,                       -- 'owned'
    storage_path TEXT NOT NULL,                  -- path in Supabase Storage bucket
    caption TEXT,                                -- pre-written caption from .txt file
    room_type TEXT NOT NULL,                     -- 'bedroom', 'kitchen', 'living room', etc.
    style_tags TEXT[] NOT NULL,                  -- ['scandinavian', 'minimalist', ...]
    dominant_colors TEXT[],                      -- ['#e8d4b8', ...] — optional
    detected_objects TEXT[],                     -- ['bed', 'lamp', ...] — optional
    quality_score FLOAT,                         -- auto-tag confidence 0–1
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_source_source_id UNIQUE (source, source_id)
);

-- =============================================================
-- Table: reference_embeddings
-- CLIP ViT-B/32 image embeddings (512-dim vectors)
-- =============================================================
CREATE TABLE IF NOT EXISTS reference_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_image_id UUID NOT NULL REFERENCES reference_images(id) ON DELETE CASCADE,
    embedding_type TEXT NOT NULL,                -- 'clip-vit-b32'
    embedding vector(512),                       -- pgvector type
    created_at TIMESTAMPTZ DEFAULT now()
);

-- =============================================================
-- Table: generations
-- AI-generated design outputs (Phase 2+)
-- =============================================================
CREATE TABLE IF NOT EXISTS generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id TEXT,
    parent_generation_id UUID REFERENCES generations(id),
    kind TEXT NOT NULL,                          -- 'draft', 'commit', 'edit'
    input_image_path TEXT,
    room_type TEXT,
    style_tag TEXT,
    reference_image_ids UUID[],
    prompt TEXT,
    model_config TEXT NOT NULL,                  -- 'A' or 'B'
    model_id TEXT,
    output_image_path TEXT,
    latency_ms INTEGER,
    cost_usd NUMERIC(10, 6),
    status TEXT,                                 -- 'success', 'failed', 'retried'
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- =============================================================
-- Table: events
-- Analytics event log
-- =============================================================
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id TEXT,
    event_type TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- =============================================================
-- Indexes
-- =============================================================

-- Reference images
CREATE INDEX IF NOT EXISTS idx_ref_room_type ON reference_images (room_type);
CREATE INDEX IF NOT EXISTS idx_ref_style_tags ON reference_images USING GIN (style_tags);
CREATE INDEX IF NOT EXISTS idx_ref_quality ON reference_images (quality_score);

-- Reference embeddings — HNSW for fast cosine similarity search
CREATE INDEX IF NOT EXISTS idx_ref_embeddings_hnsw
    ON reference_embeddings USING hnsw (embedding vector_cosine_ops);

-- Generations
CREATE INDEX IF NOT EXISTS idx_gen_user_session
    ON generations (user_id, session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_gen_parent
    ON generations (parent_generation_id);

-- Events
CREATE INDEX IF NOT EXISTS idx_events_user_time
    ON events (user_id, created_at DESC);
