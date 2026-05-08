-- 010: Add retrieve_candidates_text RPC for text-based candidate retrieval
-- Called by generate_orchestrated "Fetch candidate pool" with:
--   p_search_text (FTS over caption + room_type + style_tags)
--   p_room_type   (optional hard filter)
--   p_style_tag   (optional hard filter)
--   p_k           (max rows to return)
-- Returns all columns expected by Build Agent 2 request; caption_enhanced and
-- spatial_signature are NULL until migration 011 adds those columns.

CREATE OR REPLACE FUNCTION public.retrieve_candidates_text(
  p_search_text text    DEFAULT NULL,
  p_room_type   text    DEFAULT NULL,
  p_style_tag   text    DEFAULT NULL,
  p_k           integer DEFAULT 20
)
RETURNS TABLE(
  id               uuid,
  source_url       text,
  caption          text,
  caption_enhanced text,
  spatial_signature jsonb,
  room_type        text,
  style_tags       text[],
  dominant_colors  text[],
  detected_objects text[],
  quality_score    double precision
)
LANGUAGE sql
STABLE
AS $$
SELECT
  ri.id,
  ri.source_url,
  ri.caption,
  NULL::text             AS caption_enhanced,
  NULL::jsonb            AS spatial_signature,
  ri.room_type,
  ri.style_tags,
  ri.dominant_colors,
  ri.detected_objects,
  ri.quality_score
FROM public.reference_images ri
WHERE
  (p_room_type IS NULL OR ri.room_type = p_room_type)
  AND (p_style_tag IS NULL OR p_style_tag = ANY(ri.style_tags))
ORDER BY
  CASE
    WHEN p_search_text IS NOT NULL AND p_search_text <> ''
    THEN ts_rank(
      to_tsvector('english',
        coalesce(ri.caption,  '') || ' ' ||
        coalesce(ri.room_type, '') || ' ' ||
        coalesce(array_to_string(ri.style_tags, ' '), '')
      ),
      plainto_tsquery('english', p_search_text)
    )
    ELSE 0.0::float4
  END DESC,
  ri.quality_score DESC NULLS LAST
LIMIT p_k;
$$;
