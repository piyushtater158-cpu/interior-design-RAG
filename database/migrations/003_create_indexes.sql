-- Phase 1: Create all indexes

-- Reference images indexes
CREATE INDEX IF NOT EXISTS idx_ref_room_type
    ON reference_images (room_type);

CREATE INDEX IF NOT EXISTS idx_ref_style_tags
    ON reference_images USING GIN (style_tags);

CREATE INDEX IF NOT EXISTS idx_ref_quality
    ON reference_images (quality_score);

-- Reference embeddings HNSW index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_ref_embeddings_hnsw
    ON reference_embeddings USING hnsw (embedding vector_cosine_ops);

-- Generations indexes
CREATE INDEX IF NOT EXISTS idx_gen_user_session
    ON generations (user_id, session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_gen_parent
    ON generations (parent_generation_id);

-- Events indexes
CREATE INDEX IF NOT EXISTS idx_events_user_time
    ON events (user_id, created_at DESC);
