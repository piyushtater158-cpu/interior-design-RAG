-- =============================================================
-- Migration 008 — admin_metrics() RPC
-- =============================================================
-- Aggregates counts + latency percentiles for the last 24h.
-- Called by workflows/admin_metrics.json via:
--   POST /rest/v1/rpc/admin_metrics
-- Returns a single JSONB row matching backend/schemas/admin.py::MetricsResponse.
-- =============================================================

BEGIN;

CREATE OR REPLACE FUNCTION admin_metrics()
RETURNS JSONB LANGUAGE sql STABLE AS $$
    WITH window_gen AS (
        SELECT model_config, status, latency_ms
          FROM generations
         WHERE created_at >= NOW() - INTERVAL '24 hours'
    ),
    agg AS (
        SELECT
            COUNT(*)                                                     AS generation_count,
            COUNT(*) FILTER (WHERE status = 'success')                   AS success_count,
            COUNT(*) FILTER (WHERE status <> 'success' OR status IS NULL) AS error_count,
            PERCENTILE_CONT(0.5)  WITHIN GROUP (ORDER BY latency_ms)     AS p50,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)     AS p95
          FROM window_gen
    ),
    by_cfg AS (
        SELECT COALESCE(jsonb_object_agg(model_config, cnt), '{}'::jsonb) AS cfg_map
          FROM (SELECT model_config, COUNT(*) AS cnt
                  FROM window_gen
                 GROUP BY model_config) t
    ),
    gemini_calls AS (
        SELECT COUNT(*) AS gemini_24h
          FROM events
         WHERE event_type IN ('draft_ok','edit_ok','commit_ok','orchestrated_ok')
           AND created_at >= NOW() - INTERVAL '24 hours'
    )
    SELECT jsonb_build_object(
        'window_hours',            24,
        'generation_count',        (SELECT generation_count FROM agg),
        'success_count',           (SELECT success_count    FROM agg),
        'error_count',             (SELECT error_count      FROM agg),
        'by_config',               (SELECT cfg_map          FROM by_cfg),
        'latency_p50_ms',          (SELECT p50              FROM agg),
        'latency_p95_ms',          (SELECT p95              FROM agg),
        'gemini_calls_24h',        (SELECT gemini_24h       FROM gemini_calls),
        'gemini_quota_remaining',  -1
    );
$$;

GRANT EXECUTE ON FUNCTION admin_metrics() TO service_role;

COMMIT;
