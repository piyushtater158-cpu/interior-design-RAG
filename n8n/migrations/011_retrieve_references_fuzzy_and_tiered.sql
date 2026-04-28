-- =============================================================
-- Migration 011 — fuzzy style_tag matching AND tiered fallback
-- =============================================================
-- Combines the tiered fallback (from 010) with the fuzzy style matching
-- (from the old 009) to ensure both robustness and correct routing.
-- =============================================================

BEGIN;

DROP FUNCTION IF EXISTS retrieve_references(TEXT, TEXT, TEXT, INTEGER);

CREATE FUNCTION retrieve_references(
    q          TEXT,
    room_type  TEXT,
    style_tag  TEXT,
    k          INTEGER,
    prompt     TEXT DEFAULT NULL
) RETURNS TABLE (
    id          TEXT,
    url         TEXT,
    style_tag   TEXT,
    room_type   TEXT,
    caption     TEXT,
    prompt      TEXT,
    similarity  DOUBLE PRECISION
) LANGUAGE sql STABLE AS $$
WITH
tier1 AS MATERIALIZED (
    SELECT ri.id::text                             AS id,
           ri.source_url                           AS url,
           COALESCE(retrieve_references.style_tag, ri.style_tags[1]) AS style_tag,
           ri.room_type                            AS room_type,
           ri.caption                              AS caption,
           retrieve_references.prompt              AS prompt,
           (1-(re.embedding<=>q::vector))::float8  AS similarity
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
     LIMIT k
),
tier2 AS MATERIALIZED (
    SELECT ri.id::text                             AS id,
           ri.source_url                           AS url,
           COALESCE(retrieve_references.style_tag, ri.style_tags[1]) AS style_tag,
           ri.room_type                            AS room_type,
           ri.caption                              AS caption,
           retrieve_references.prompt              AS prompt,
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
           COALESCE(retrieve_references.style_tag, ri.style_tags[1]) AS style_tag,
           ri.room_type                            AS room_type,
           ri.caption                              AS caption,
           retrieve_references.prompt              AS prompt,
           (1-(re.embedding<=>q::vector))::float8  AS similarity
      FROM reference_images ri
      JOIN reference_embeddings re ON re.reference_image_id = ri.id
     WHERE NOT EXISTS (SELECT 1 FROM tier1)
       AND NOT EXISTS (SELECT 1 FROM tier2)
     ORDER BY re.embedding <=> q::vector
     LIMIT k
)
SELECT id, url, style_tag, room_type, caption, prompt, similarity FROM tier1
UNION ALL
SELECT id, url, style_tag, room_type, caption, prompt, similarity FROM tier2
UNION ALL
SELECT id, url, style_tag, room_type, caption, prompt, similarity FROM tier3;
$$;

GRANT EXECUTE ON FUNCTION retrieve_references(TEXT, TEXT, TEXT, INTEGER, TEXT) TO service_role;

COMMIT;
