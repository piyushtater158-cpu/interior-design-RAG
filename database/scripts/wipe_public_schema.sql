-- Wipe public schema to an empty Supabase-compatible public schema.
-- Run as postgres / service_role via direct session (not transaction-pooled) if DROP fails.
-- Order matters: auth trigger references public functions.

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- App storage metadata (files may remain in object storage until re-uploaded)
DELETE FROM storage.objects
WHERE bucket_id IN ('reference-images', 'user-uploads', 'user-outputs');

DROP POLICY IF EXISTS "ref_images_objects_select" ON storage.objects;
DROP POLICY IF EXISTS "ref_images_objects_insert" ON storage.objects;
DROP POLICY IF EXISTS "ref_images_objects_update" ON storage.objects;
DROP POLICY IF EXISTS "ref_images_objects_delete" ON storage.objects;
DROP POLICY IF EXISTS "user_uploads_objects_insert" ON storage.objects;
DROP POLICY IF EXISTS "user_uploads_objects_select" ON storage.objects;
DROP POLICY IF EXISTS "user_uploads_objects_delete" ON storage.objects;
DROP POLICY IF EXISTS "user_outputs_objects_insert" ON storage.objects;
DROP POLICY IF EXISTS "user_outputs_objects_select" ON storage.objects;

DELETE FROM storage.buckets
WHERE id IN ('reference-images', 'user-uploads', 'user-outputs');

DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres, anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO postgres, anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres, anon, authenticated, service_role;
