-- 017: Supabase Auth foundation — public.users mirror, trigger, and RLS
-- Canonical idempotent version of the auth migration applied to production.
-- Safe to re-apply on an already-migrated database.
-- Does NOT truncate any tables (destructive truncates were dev-only, not preserved here).

-- 1. Link public.users.id → auth.users.id (if not already set)
--    Allows service-side lookup by Supabase UID; cascade-deletes if auth user is removed.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'users_auth_fkey'
  ) THEN
    ALTER TABLE public.users ALTER COLUMN id DROP DEFAULT;
    ALTER TABLE public.users
      ADD CONSTRAINT users_auth_fkey
      FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;
  END IF;
END $$;

-- 2. Remove is_demo flag if it somehow survived (demo login was removed)
ALTER TABLE public.users DROP COLUMN IF EXISTS is_demo;

-- 3. Trigger function: mirror auth.users → public.users on every new sign-up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.users (id, email)
  VALUES (new.id, new.email)
  ON CONFLICT (id) DO UPDATE SET email = excluded.email;
  RETURN new;
END;
$$;

-- 4. Trigger: fires after every new auth.users insert
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 5. Enable RLS on all public tables
--    n8n uses SUPABASE_SERVICE_KEY which bypasses RLS; these policies protect direct client access.
ALTER TABLE public.users            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generations      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.events           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reference_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_config       ENABLE ROW LEVEL SECURITY;

-- 6. Policies (idempotent: CREATE POLICY is skipped if name already exists)

-- Users: read own row only
DO $$ BEGIN
  CREATE POLICY "users_select_own" ON public.users
    FOR SELECT USING (auth.uid() = id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Generations: full CRUD on own rows
DO $$ BEGIN
  CREATE POLICY "generations_select_own" ON public.generations
    FOR SELECT USING (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE POLICY "generations_insert_own" ON public.generations
    FOR INSERT WITH CHECK (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE POLICY "generations_update_own" ON public.generations
    FOR UPDATE USING (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Events: insert only from client (service key reads for analytics)
DO $$ BEGIN
  CREATE POLICY "events_insert_own" ON public.events
    FOR INSERT WITH CHECK (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- App config: publicly readable
DO $$ BEGIN
  CREATE POLICY "app_config_public_read" ON public.app_config
    FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
