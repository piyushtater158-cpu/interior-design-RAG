-- =============================================================
-- Migration 009 — retrieve_references() restore original param names
-- =============================================================
-- Migration 008 used PL/pgSQL and renamed parameters to _room_type/_style_tag
-- to avoid the naming conflict with return columns. This broke PostgREST,
-- which matches JSON body keys to parameter names exactly — so the body
-- {q, room_type, style_tag, k} produced a 404 (function not found).
--
-- Fix: drop and recreate using LANGUAGE sql, which allows qualifying
-- parameters as retrieve_references.room_type to disambiguate from the
-- identically-named return column. Tiered CTE fallback is preserved:
--   Tier 1: room_type + style_tag exact match
--   Tier 2: room_type only (style_tag had no DB coverage)
--   Tier 3: pure vector similarity
-- =============================================================

DROP FUNCTION IF EXISTS retrieve_references(TEXT, TEXT, TEXT, INTEGER);

CREATE FUNCTION retrieve_references(
    q          TEXT,
    room_type  TEXT,
    style_tag  TEXT,
    k          INTEGER
) RETURNS TABLE (
    id          TEXT,
    url         TEXT,
    style_tags  TEXT[],
    room_type   TEXT,
    caption     TEXT,
    similarity  DOUBLE PRECISION
) LANGUAGE sql STABLE AS $$
WITH
tier1 AS MATERIALIZED (
    SELECT ri.id::text                             AS id,
           ri.source_url                           AS url,
           ri.style_tags                           AS style_tags,
           ri.room_type                            AS room_type,
           ri.caption                              AS caption,
           (1-(re.embedding<=>q::vector))::float8  AS similarity
      FROM reference_images ri
      JOIN reference_embeddings re ON re.reference_image_id = ri.id
     WHERE (retrieve_references.room_type IS NULL
            OR ri.room_type = retrieve_references.room_type)
       AND (retrieve_references.style_tag  IS NULL
            OR retrieve_references.style_tag = ANY(ri.style_tags))
     ORDER BY re.embedding <=> q::vector
     LIMIT k
),
tier2 AS MATERIALIZED (
    SELECT ri.id::text                             AS id,
           ri.source_url                           AS url,
           ri.style_tags                           AS style_tags,
           ri.room_type                            AS room_type,
           ri.caption                              AS caption,
           (1-(re.embedding<=>q::vector))::float8  AS similarity
      FROM reference_images ri
      JOIN reference_embeddings re ON re.reference_image_id = ri.id
     WHERE NOT EXISTS (SELECT 1 FROM tier1)
       AND (retrieve_references.room_type IS NULL
            OR ri.room_type = retrieve_references.room_type)
     ORDER BY re.embedding <=> q::vector
     LIMIT k
),
tier3 AS MATERIALIZED (
    SELECT ri.id::text                             AS id,
           ri.source_url                           AS url,
           ri.style_tags                           AS style_tags,
           ri.room_type                            AS room_type,
           ri.caption                              AS caption,
           (1-(re.embedding<=>q::vector))::float8  AS similarity
      FROM reference_images ri
      JOIN reference_embeddings re ON re.reference_image_id = ri.id
     WHERE NOT EXISTS (SELECT 1 FROM tier1)
       AND NOT EXISTS (SELECT 1 FROM tier2)
     ORDER BY re.embedding <=> q::vector
     LIMIT k
)
SELECT id, url, style_tags, room_type, caption, similarity FROM tier1
UNION ALL
SELECT id, url, style_tags, room_type, caption, similarity FROM tier2
UNION ALL
SELECT id, url, style_tags, room_type, caption, similarity FROM tier3;
$$;

GRANT EXECUTE ON FUNCTION retrieve_references(TEXT, TEXT, TEXT, INTEGER) TO service_role;
