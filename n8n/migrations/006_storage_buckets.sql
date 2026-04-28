-- =============================================================
-- Migration 006 — Supabase Storage buckets for user uploads + outputs
-- =============================================================
-- These replace the local ./backend/data/{uploads,outputs} tree.
-- Both buckets are public-read; writes are restricted via service role.
-- The n8n workflows use the service-role key and therefore bypass RLS.
-- =============================================================

BEGIN;

-- 1. Create two public buckets.
INSERT INTO storage.buckets (id, name, public)
VALUES
    ('user-uploads', 'user-uploads', true),
    ('user-outputs', 'user-outputs', true)
ON CONFLICT (id) DO UPDATE SET public = EXCLUDED.public;

-- 2. Public-read RLS policies (so <img src="..."> works without auth).
DROP POLICY IF EXISTS "public read user-uploads"  ON storage.objects;
DROP POLICY IF EXISTS "public read user-outputs"  ON storage.objects;

CREATE POLICY "public read user-uploads"
    ON storage.objects FOR SELECT
    USING (bucket_id = 'user-uploads');

CREATE POLICY "public read user-outputs"
    ON storage.objects FOR SELECT
    USING (bucket_id = 'user-outputs');

-- 3. No INSERT/UPDATE/DELETE policies are defined here on purpose:
--    n8n performs writes with the service-role key, which bypasses RLS.
--    If you later want anon / authenticated writes, add them explicitly.

COMMIT;
