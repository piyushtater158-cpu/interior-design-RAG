-- Shared catalog read for authenticated users (Profile → Database in mobile-app).
-- Canonical copy: n8n/migrations/016_reference_images_catalog_rls.sql

BEGIN;

ALTER TABLE reference_images ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "reference_images_select_authenticated" ON reference_images;
CREATE POLICY "reference_images_select_authenticated"
  ON reference_images
  FOR SELECT
  TO authenticated
  USING (true);

DROP POLICY IF EXISTS "reference_images_insert_own" ON reference_images;
CREATE POLICY "reference_images_insert_own"
  ON reference_images
  FOR INSERT
  TO authenticated
  WITH CHECK (owner_id = auth.uid());

DROP POLICY IF EXISTS "reference_images_update_own" ON reference_images;
CREATE POLICY "reference_images_update_own"
  ON reference_images
  FOR UPDATE
  TO authenticated
  USING (owner_id = auth.uid())
  WITH CHECK (owner_id = auth.uid());

DROP POLICY IF EXISTS "reference_images_delete_own" ON reference_images;
CREATE POLICY "reference_images_delete_own"
  ON reference_images
  FOR DELETE
  TO authenticated
  USING (owner_id = auth.uid());

COMMIT;
