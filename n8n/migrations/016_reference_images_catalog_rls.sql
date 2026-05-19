-- Shared catalog read for authenticated users (Profile → Database in mobile-app).
-- Writes remain owner-scoped. Service role bypasses RLS (n8n seed/upload).

BEGIN;

ALTER TABLE reference_images ENABLE ROW LEVEL SECURITY;

-- SELECT: any signed-in user may browse the full reference catalog.
DROP POLICY IF EXISTS "reference_images_select_authenticated" ON reference_images;
CREATE POLICY "reference_images_select_authenticated"
  ON reference_images
  FOR SELECT
  TO authenticated
  USING (true);

-- INSERT: only create rows for yourself.
DROP POLICY IF EXISTS "reference_images_insert_own" ON reference_images;
CREATE POLICY "reference_images_insert_own"
  ON reference_images
  FOR INSERT
  TO authenticated
  WITH CHECK (owner_id = auth.uid());

-- UPDATE: only your rows.
DROP POLICY IF EXISTS "reference_images_update_own" ON reference_images;
CREATE POLICY "reference_images_update_own"
  ON reference_images
  FOR UPDATE
  TO authenticated
  USING (owner_id = auth.uid())
  WITH CHECK (owner_id = auth.uid());

-- DELETE: only your rows.
DROP POLICY IF EXISTS "reference_images_delete_own" ON reference_images;
CREATE POLICY "reference_images_delete_own"
  ON reference_images
  FOR DELETE
  TO authenticated
  USING (owner_id = auth.uid());

COMMIT;
