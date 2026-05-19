-- Prerequisite for 016_reference_images_catalog_rls.sql.
-- Adds owner_id to reference_images if the column does not yet exist
-- (idempotent — safe to apply against a DB that already has the column).

BEGIN;

ALTER TABLE reference_images
  ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

COMMIT;
