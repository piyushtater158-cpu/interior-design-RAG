-- =============================================================
-- Migration 008 — retrieve_references() tiered fallback
-- =============================================================
-- Replaces the strict room_type+style_tag filter with a three-tier
-- fallback so the function always returns k results:
--
--   Tier 1: room_type AND style_tag both match  (ideal)
--   Tier 2: room_type matches only              (style had no DB coverage)
--   Tier 3: pure vector similarity              (room_type also unmatched)
--
-- Also renames parameters to _room_type/_style_tag to avoid the
-- PL/pgSQL conflict with the identically-named return columns.
-- =============================================================

DROP FUNCTION IF EXISTS retrieve_references(TEXT, TEXT, TEXT, INTEGER);

CREATE FUNCTION retrieve_references(
    q          TEXT,
    _room_type TEXT,
    _style_tag TEXT,
    k          INTEGER
) RETURNS TABLE (
    id          TEXT,
    url         TEXT,
    style_tags  TEXT[],
    room_type   TEXT,
    caption     TEXT,
    similarity  DOUBLE PRECISION
) LANGUAGE plpgsql STABLE AS $$
BEGIN
    -- Tier 1: exact room_type + style_tag match
    IF EXISTS (
        SELECT 1
          FROM reference_images ri
          JOIN reference_embeddings re ON re.reference_image_id = ri.id
         WHERE (_room_type IS NULL OR ri.room_type = _room_type)
           AND (_style_tag  IS NULL OR _style_tag  = ANY(ri.style_tags))
    ) THEN
        RETURN QUERY
        SELECT ri.id::text,
               ri.source_url,
               ri.style_tags,
               ri.room_type,
               ri.caption,
               (1 - (re.embedding <=> q::vector))::double precision
          FROM reference_images ri
          JOIN reference_embeddings re ON re.reference_image_id = ri.id
         WHERE (_room_type IS NULL OR ri.room_type = _room_type)
           AND (_style_tag  IS NULL OR _style_tag  = ANY(ri.style_tags))
         ORDER BY re.embedding <=> q::vector
         LIMIT k;
        RETURN;
    END IF;

    -- Tier 2: room_type only (no style_tag match found)
    IF EXISTS (
        SELECT 1 FROM reference_images ri
         WHERE (_room_type IS NULL OR ri.room_type = _room_type)
    ) THEN
        RETURN QUERY
        SELECT ri.id::text,
               ri.source_url,
               ri.style_tags,
               ri.room_type,
               ri.caption,
               (1 - (re.embedding <=> q::vector))::double precision
          FROM reference_images ri
          JOIN reference_embeddings re ON re.reference_image_id = ri.id
         WHERE (_room_type IS NULL OR ri.room_type = _room_type)
         ORDER BY re.embedding <=> q::vector
         LIMIT k;
        RETURN;
    END IF;

    -- Tier 3: pure vector similarity (no room_type match either)
    RETURN QUERY
    SELECT ri.id::text,
           ri.source_url,
           ri.style_tags,
           ri.room_type,
           ri.caption,
           (1 - (re.embedding <=> q::vector))::double precision
      FROM reference_images ri
      JOIN reference_embeddings re ON re.reference_image_id = ri.id
     ORDER BY re.embedding <=> q::vector
     LIMIT k;
END;
$$;

GRANT EXECUTE ON FUNCTION retrieve_references(TEXT, TEXT, TEXT, INTEGER) TO service_role;
