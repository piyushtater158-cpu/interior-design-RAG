-- =============================================================
-- Migration 005 — app_config key/value table
-- =============================================================
-- Holds runtime-swappable settings that workflows read per execution.
-- Kept as a table (not env vars) so values can be changed from SQL
-- without redeploying n8n workflows.
-- =============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS app_config (
    key        TEXT PRIMARY KEY,
    value      JSONB       NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed the active image-generation model.
INSERT INTO app_config (key, value)
VALUES ('image_model', '"gemini-3.1-flash-image-preview"'::jsonb)
ON CONFLICT (key) DO UPDATE
    SET value = EXCLUDED.value,
        updated_at = now();

-- OpenRouter base URL (chat / orchestration; not used for image embeddings)
INSERT INTO app_config (key, value)
VALUES
    ('openrouter_base',   '"https://openrouter.ai/api/v1"'::jsonb),
    ('orchestrator_model','"google/gemma-4-31b-it:free"'::jsonb),
    ('max_edit_chain',    '6'::jsonb)
ON CONFLICT (key) DO UPDATE
    SET value = EXCLUDED.value,
        updated_at = now();

COMMIT;
