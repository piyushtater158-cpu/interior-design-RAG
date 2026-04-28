-- =============================================================
-- Migration 009 — fuzzy style_tag matching in retrieve_references()
-- =============================================================
-- Problem: callers pass values like "midcentury" but stored tags
--          use "mid-century-modern" — exact match returns 0 rows.
--
-- Fix: normalize both sides by stripping hyphens/spaces/underscores
--      and lowercasing, then do a bidirectional LIKE:
--        stored tag normalized CONTAINS search term normalized, OR
--        search term normalized CONTAINS stored tag normalized.
--
-- Examples that now match:
--   "midcentury"      ↔  "mid-century-modern"
--   "mid century"     ↔  "mid-century-modern"
--   "boho"            ↔  "bohemian"  (boho ⊂ bohemian)
--   "scandinavian"    ↔  "scandinavian"  (exact still works)
--   "minimalist"      ↔  "minimalist"    (exact still works)
-- =============================================================

BEGIN;

CREATE OR REPLACE FUNCTION retrieve_references(
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
    SELECT ri.id::text                                                       AS id,
           ri.source_url                                                     AS url,
           ri.style_tags                                                     AS style_tags,
           ri.room_type                                                      AS room_type,
           ri.caption                                                        AS caption,
           (1 - (re.embedding <=> q::vector))::double precision              AS similarity
      FROM reference_images ri
      JOIN reference_embeddings re ON re.reference_image_id = ri.id
     WHERE (retrieve_references.room_type IS NULL
            OR ri.room_type = retrieve_references.room_type)
       AND (retrieve_references.style_tag IS NULL
            OR EXISTS (
                SELECT 1
                  FROM unnest(ri.style_tags) t
                 WHERE regexp_replace(lower(t),           '[-_\s]+', '', 'g')
                       LIKE '%' || regexp_replace(lower(retrieve_references.style_tag), '[-_\s]+', '', 'g') || '%'
                    OR regexp_replace(lower(retrieve_references.style_tag), '[-_\s]+', '', 'g')
                       LIKE '%' || regexp_replace(lower(t), '[-_\s]+', '', 'g') || '%'
            ))
     ORDER BY re.embedding <=> q::vector
     LIMIT k;
$$;

GRANT EXECUTE ON FUNCTION retrieve_references(TEXT, TEXT, TEXT, INTEGER) TO service_role;

COMMIT;
