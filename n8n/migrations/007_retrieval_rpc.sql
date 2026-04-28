-- =============================================================
-- Migration 007 — retrieve_references() RPC
-- =============================================================
-- Wraps the pgvector similarity query so n8n can call it via PostgREST
-- without having to embed a pgvector literal in a URL or use the Postgres
-- node directly.
--
-- Called from workflows/retrieve_references.json via:
--   POST /rest/v1/rpc/retrieve_references
--   { q, room_type, style_tag, k }
-- =============================================================

BEGIN;

CREATE OR REPLACE FUNCTION retrieve_references(
    q          TEXT,    -- pgvector text literal e.g. '[0.1,0.2,...]'
    room_type  TEXT,    -- nullable
    style_tag  TEXT,    -- nullable
    k          INTEGER  -- 1..20
) RETURNS TABLE (
    id          TEXT,
    url         TEXT,
    style_tags  TEXT[],
    room_type   TEXT,
    caption     TEXT,
    similarity  DOUBLE PRECISION
) LANGUAGE sql STABLE AS $$
    SELECT ri.id::text                             AS id,
           ri.source_url                           AS url,
           ri.style_tags                           AS style_tags,
           ri.room_type                            AS room_type,
           ri.caption                              AS caption,
           (1 - (re.embedding <=> q::vector))::double precision AS similarity
      FROM reference_images ri
      JOIN reference_embeddings re
        ON re.reference_image_id = ri.id
     WHERE (retrieve_references.room_type IS NULL OR ri.room_type = retrieve_references.room_type)
       AND (retrieve_references.style_tag IS NULL OR retrieve_references.style_tag = ANY(ri.style_tags))
     ORDER BY re.embedding <=> q::vector
     LIMIT k;
$$;

-- PostgREST exposes functions in the `public` schema automatically.
-- Grant execute to the service role the n8n workflows use.
GRANT EXECUTE ON FUNCTION retrieve_references(TEXT, TEXT, TEXT, INTEGER) TO service_role;

-- =============================================================
-- generation_chain_depth() — how many ancestors does generation :id have?
-- Used by generate_edit workflow to enforce the 6-edit cap.
-- Returns 0 if :id has no parent; returns N if there are N ancestors.
-- =============================================================
CREATE OR REPLACE FUNCTION generation_chain_depth(gen_id UUID)
RETURNS INTEGER LANGUAGE sql STABLE AS $$
    WITH RECURSIVE chain AS (
        SELECT id, parent_generation_id, 0 AS depth
          FROM generations
         WHERE id = gen_id
        UNION ALL
        SELECT g.id, g.parent_generation_id, c.depth + 1
          FROM generations g
          JOIN chain c ON g.id = c.parent_generation_id
    )
    SELECT COALESCE(MAX(depth), 0) FROM chain;
$$;

GRANT EXECUTE ON FUNCTION generation_chain_depth(UUID) TO service_role;

COMMIT;
