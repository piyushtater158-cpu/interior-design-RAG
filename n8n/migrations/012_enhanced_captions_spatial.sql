-- =============================================================
-- Migration 012 — Enhanced captions + spatial indexing
-- =============================================================
-- Drops vector embeddings as the primary retrieval signal and
-- replaces them with LLM-generated enhanced captions that include
-- 3D spatial structure reasoning.
--
-- Indexing strategy (replaces 2048-dim sequential scan):
--   1. GIN on caption_fts (generated tsvector)  — O(1) full-text
--   2. GIN on spatial_signature JSONB           — structural containment
--   3. B-tree on room_type (existing)           — equality pre-filter
--   4. GIN on style_tags[] (existing)           — array containment
--
-- Query path in generate_orchestrated Agent 2:
--   room_type filter → FTS rank on caption_enhanced → Agent 2 spatial pick
-- =============================================================

BEGIN;

-- 1. Add enhanced caption + spatial signature columns to reference_images
ALTER TABLE reference_images
  ADD COLUMN IF NOT EXISTS caption_enhanced    TEXT,
  ADD COLUMN IF NOT EXISTS spatial_signature   JSONB,
  ADD COLUMN IF NOT EXISTS caption_enhanced_at TIMESTAMPTZ;

-- 2. Generated tsvector column for full-text search
--    COALESCE: uses caption_enhanced when available, falls back to original caption
ALTER TABLE reference_images
  ADD COLUMN IF NOT EXISTS caption_fts TSVECTOR
  GENERATED ALWAYS AS (
    to_tsvector('english', COALESCE(caption_enhanced, caption, ''))
  ) STORED;

-- 3. GIN index on full-text search column (enables @@ operator in O(1))
CREATE INDEX IF NOT EXISTS idx_ref_caption_fts
  ON reference_images USING GIN(caption_fts);

-- 4. GIN index on spatial_signature JSONB
--    Supports: spatial_signature @> '{"ceiling_height":"high"}'
CREATE INDEX IF NOT EXISTS idx_ref_spatial_sig
  ON reference_images USING GIN(spatial_signature);

-- 5. Text-based candidate retrieval RPC
--    Used by generate_orchestrated to pre-filter candidate pool via FTS
--    before passing cards to Agent 2. Replaces vector similarity scan.
DROP FUNCTION IF EXISTS retrieve_candidates_text(TEXT, TEXT, TEXT, INTEGER);

CREATE FUNCTION retrieve_candidates_text(
  p_search_text TEXT,
  p_room_type   TEXT    DEFAULT NULL,
  p_style_tag   TEXT    DEFAULT NULL,
  p_k           INTEGER DEFAULT 20
) RETURNS TABLE (
  id               UUID,
  source_url       TEXT,
  caption          TEXT,
  caption_enhanced TEXT,
  spatial_sig      JSONB,
  room_type        TEXT,
  style_tags       TEXT[],
  dominant_colors  TEXT[],
  detected_objects TEXT[],
  quality_score    FLOAT,
  fts_rank         FLOAT
) LANGUAGE sql STABLE AS $$
WITH
tier1 AS MATERIALIZED (
  -- FTS match with optional room_type pre-filter
  SELECT ri.id, ri.source_url, ri.caption, ri.caption_enhanced,
         ri.spatial_signature AS spatial_sig, ri.room_type, ri.style_tags,
         ri.dominant_colors, ri.detected_objects, ri.quality_score,
         ts_rank_cd(ri.caption_fts,
           plainto_tsquery('english', p_search_text))::float AS fts_rank
    FROM reference_images ri
   WHERE ri.caption_fts @@ plainto_tsquery('english', p_search_text)
     AND (p_room_type IS NULL OR ri.room_type = p_room_type)
   ORDER BY fts_rank DESC
   LIMIT p_k
),
tier2 AS MATERIALIZED (
  -- Room-type-only fallback when FTS yields nothing
  SELECT ri.id, ri.source_url, ri.caption, ri.caption_enhanced,
         ri.spatial_signature AS spatial_sig, ri.room_type, ri.style_tags,
         ri.dominant_colors, ri.detected_objects, ri.quality_score,
         (COALESCE(ri.quality_score, 0))::float AS fts_rank
    FROM reference_images ri
   WHERE NOT EXISTS (SELECT 1 FROM tier1)
     AND (p_room_type IS NULL OR ri.room_type = p_room_type)
   ORDER BY ri.quality_score DESC NULLS LAST
   LIMIT p_k
),
tier3 AS MATERIALIZED (
  -- Pure quality fallback — guarantees p_k results
  SELECT ri.id, ri.source_url, ri.caption, ri.caption_enhanced,
         ri.spatial_signature AS spatial_sig, ri.room_type, ri.style_tags,
         ri.dominant_colors, ri.detected_objects, ri.quality_score,
         (COALESCE(ri.quality_score, 0))::float AS fts_rank
    FROM reference_images ri
   WHERE NOT EXISTS (SELECT 1 FROM tier1)
     AND NOT EXISTS (SELECT 1 FROM tier2)
   ORDER BY ri.quality_score DESC NULLS LAST
   LIMIT p_k
)
SELECT * FROM tier1
UNION ALL SELECT * FROM tier2
UNION ALL SELECT * FROM tier3;
$$;

GRANT EXECUTE ON FUNCTION retrieve_candidates_text(TEXT, TEXT, TEXT, INTEGER) TO service_role;

COMMIT;

-- =============================================================
-- After applying this migration, run wf_enhance_caption against
-- all 104 reference images to populate caption_enhanced and
-- spatial_signature. Until that completes, FTS falls back to
-- the original plain-text caption column.
--
-- Verification:
--   SELECT COUNT(*) FROM reference_images WHERE caption_enhanced IS NOT NULL;
--   SELECT * FROM retrieve_candidates_text('minimalist bedroom natural light', 'bedroom', NULL, 5);
-- =============================================================
