-- =============================================================
-- Migration 004 — replace CLIP ViT-B/32 (512d) with Nemotron-VL-1B-v2
-- =============================================================
-- Context: retrieval moves from in-process CLIP to OpenRouter-hosted
--          nvidia/llama-nemotron-embed-vl-1b-v2:free. The embedding
--          dimension below must match whatever that model returns.
--
-- HOW TO SET THE DIMENSION:
--   1. Before applying this file, make one test call to OpenRouter's
--      embeddings endpoint with a small image, then inspect
--      data[0].embedding.length in the response.
--   2. Replace every occurrence of 1024 below with that integer.
--   3. Then run this migration against the Supabase project.
--
-- CONFIRMED: nvidia/llama-nemotron-embed-vl-1b-v2:free returns 2048 dims.
-- NOTE: pgvector HNSW index max is 2000 dims, so no HNSW index is created.
--       With 104 reference images a sequential scan is fast enough.
-- =============================================================

BEGIN;

-- 1. Drop the HNSW index (it won't be recreated — 2048 > 2000 dim limit).
DROP INDEX IF EXISTS idx_ref_embeddings_hnsw;

-- 2. Clear any old rows.
DELETE FROM reference_embeddings;

-- 3. Change the vector column to 2048 dimensions.
ALTER TABLE reference_embeddings
    ALTER COLUMN embedding TYPE vector(2048);

COMMIT;

-- =============================================================
-- Verification (run manually after COMMIT):
--   SELECT atttypmod FROM pg_attribute
--     WHERE attrelid = 'reference_embeddings'::regclass
--       AND attname = 'embedding';
-- The returned value equals the dimension (e.g. 1024).
-- =============================================================
