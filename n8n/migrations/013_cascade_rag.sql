-- =============================================================
-- Migration 013 — Cascade RAG
-- =============================================================
-- Adds:
--   1. mood_tags TEXT[] on reference_images + GIN index
--   2. spatial_overlap(candidate JSONB, query_req JSONB) → FLOAT
--   3. retrieve_candidates_text() v2 — 3-tier cascade with
--      multi-dimensional scoring:
--      40% FTS · 25% spatial overlap · 20% mood tag overlap · 15% quality
--
-- PostgREST call from n8n:
--   POST /rest/v1/rpc/retrieve_candidates_text
--   { "p_search_text": "airy scandinavian bedroom natural light",
--     "p_room_type":   "bedroom",
--     "p_style_tag":   "scandinavian",
--     "p_user_id":     "<uuid>",
--     "p_spatial_req": {"ceiling_height":"high","window_wall":"back"},
--     "p_mood_tags":   ["airy","minimal"],
--     "p_k": 20 }
-- =============================================================

BEGIN;

-- 1. mood_tags column + GIN index
ALTER TABLE reference_images
  ADD COLUMN IF NOT EXISTS mood_tags TEXT[] DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_ref_mood_tags
  ON reference_images USING GIN(mood_tags);

-- 2. spatial_overlap
--    Compares a flat JSONB spatial_signature against a query spec.
--    Returns proportion of matched keys (0.0–1.0).
--    Returns 1.0 when query is NULL/empty (no spatial constraint = full score).
CREATE OR REPLACE FUNCTION spatial_overlap(candidate JSONB, query_req JSONB)
RETURNS FLOAT LANGUAGE plpgsql STABLE AS $$
DECLARE
  total   INT := 0;
  matched INT := 0;
  k       TEXT;
  v       TEXT;
BEGIN
  IF query_req IS NULL OR query_req = '{}'::JSONB THEN
    RETURN 1.0;
  END IF;
  FOR k, v IN SELECT * FROM jsonb_each_text(query_req) LOOP
    total   := total + 1;
    IF candidate ->> k = v THEN matched := matched + 1; END IF;
  END LOOP;
  IF total = 0 THEN RETURN 1.0; END IF;
  RETURN matched::FLOAT / total::FLOAT;
END;
$$;

GRANT EXECUTE ON FUNCTION spatial_overlap(JSONB, JSONB)
  TO service_role, anon, authenticated;

-- 3. Updated retrieve_candidates_text — drop old signatures first
DROP FUNCTION IF EXISTS retrieve_candidates_text(TEXT, TEXT, TEXT, INTEGER);
DROP FUNCTION IF EXISTS retrieve_candidates_text(TEXT, TEXT, TEXT, UUID, JSONB, TEXT[], INTEGER);

CREATE FUNCTION retrieve_candidates_text(
  p_search_text TEXT,
  p_room_type   TEXT    DEFAULT NULL,
  p_style_tag   TEXT    DEFAULT NULL,
  p_user_id     UUID    DEFAULT NULL,
  p_spatial_req JSONB   DEFAULT NULL,
  p_mood_tags   TEXT[]  DEFAULT NULL,
  p_k           INTEGER DEFAULT 20
) RETURNS TABLE (
  id               UUID,
  source_url       TEXT,
  caption          TEXT,
  caption_enhanced TEXT,
  spatial_sig      JSONB,
  room_type        TEXT,
  style_tags       TEXT[],
  mood_tags        TEXT[],
  quality_score    FLOAT,
  score            FLOAT
) LANGUAGE sql STABLE AS $$
WITH
ts AS MATERIALIZED (
  SELECT plainto_tsquery('english', p_search_text) AS tsv
),
-- Tier 1: FTS match + hard filters → multi-dimensional score
tier1 AS MATERIALIZED (
  SELECT
    ri.id,
    ri.source_url,
    ri.caption,
    ri.caption_enhanced,
    ri.spatial_signature                                              AS spatial_sig,
    ri.room_type,
    ri.style_tags,
    ri.mood_tags,
    ri.quality_score,
    (   0.40 * ts_rank_cd(ri.caption_fts, (SELECT tsv FROM ts))
      + 0.25 * spatial_overlap(ri.spatial_signature, p_spatial_req)
      + 0.20 * CASE
                 WHEN p_mood_tags IS NULL OR cardinality(p_mood_tags) = 0 THEN 1.0
                 ELSE COALESCE(
                   (SELECT COUNT(*)::FLOAT / cardinality(p_mood_tags)
                    FROM unnest(p_mood_tags) m(tag) WHERE tag = ANY(ri.mood_tags)),
                   0.0)
               END
      + 0.15 * COALESCE(ri.quality_score, 0.5)
    )::FLOAT AS score
  FROM reference_images ri
  WHERE
    ri.caption_fts @@ (SELECT tsv FROM ts)
    AND (p_user_id    IS NULL OR ri.owner_id    = p_user_id)
    AND (p_room_type  IS NULL OR ri.room_type   = p_room_type)
    AND (p_style_tag  IS NULL OR p_style_tag    = ANY(ri.style_tags))
    AND (p_spatial_req IS NULL OR ri.spatial_signature @> p_spatial_req)
  ORDER BY score DESC
  LIMIT p_k
),
-- Tier 2: Room-type-only fallback when FTS yields nothing
tier2 AS MATERIALIZED (
  SELECT
    ri.id,
    ri.source_url,
    ri.caption,
    ri.caption_enhanced,
    ri.spatial_signature                                              AS spatial_sig,
    ri.room_type,
    ri.style_tags,
    ri.mood_tags,
    ri.quality_score,
    (   0.25 * spatial_overlap(ri.spatial_signature, p_spatial_req)
      + 0.20 * CASE
                 WHEN p_mood_tags IS NULL OR cardinality(p_mood_tags) = 0 THEN 1.0
                 ELSE COALESCE(
                   (SELECT COUNT(*)::FLOAT / cardinality(p_mood_tags)
                    FROM unnest(p_mood_tags) m(tag) WHERE tag = ANY(ri.mood_tags)),
                   0.0)
               END
      + 0.15 * COALESCE(ri.quality_score, 0.5)
    )::FLOAT AS score
  FROM reference_images ri
  WHERE
    NOT EXISTS (SELECT 1 FROM tier1)
    AND (p_user_id   IS NULL OR ri.owner_id  = p_user_id)
    AND (p_room_type IS NULL OR ri.room_type = p_room_type)
    AND (p_style_tag IS NULL OR p_style_tag  = ANY(ri.style_tags))
  ORDER BY score DESC NULLS LAST
  LIMIT p_k
),
-- Tier 3: Pure quality fallback — guarantees p_k results
tier3 AS MATERIALIZED (
  SELECT
    ri.id,
    ri.source_url,
    ri.caption,
    ri.caption_enhanced,
    ri.spatial_signature                                              AS spatial_sig,
    ri.room_type,
    ri.style_tags,
    ri.mood_tags,
    ri.quality_score,
    COALESCE(ri.quality_score, 0.0)::FLOAT                           AS score
  FROM reference_images ri
  WHERE
    NOT EXISTS (SELECT 1 FROM tier1)
    AND NOT EXISTS (SELECT 1 FROM tier2)
    AND (p_user_id IS NULL OR ri.owner_id = p_user_id)
  ORDER BY ri.quality_score DESC NULLS LAST
  LIMIT p_k
)
SELECT * FROM tier1
UNION ALL SELECT * FROM tier2
UNION ALL SELECT * FROM tier3;
$$;

GRANT EXECUTE ON FUNCTION
  retrieve_candidates_text(TEXT, TEXT, TEXT, UUID, JSONB, TEXT[], INTEGER)
  TO service_role, anon, authenticated;

COMMIT;

-- =============================================================
-- After applying this migration:
--   1. Run the updated uploads_reference workflow to auto-populate
--      mood_tags and caption_enhanced on new uploads.
--   2. For existing rows, run wf_enhance_caption against each
--      reference_image_id to back-fill caption_enhanced + mood_tags.
--
-- Verification:
--   SELECT id, mood_tags, caption_enhanced IS NOT NULL
--   FROM reference_images LIMIT 5;
--
--   SELECT * FROM retrieve_candidates_text(
--     'minimalist bedroom natural light',
--     'bedroom', 'scandinavian', NULL,
--     '{"ceiling_height":"high"}'::jsonb,
--     ARRAY['minimal','airy'], 5
--   );
-- =============================================================
