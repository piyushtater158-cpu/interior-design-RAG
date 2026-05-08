-- 009: Switch auth from custom HMAC JWT to Supabase Auth
-- User data wiped at user's request (dev-only; no production data to preserve).
-- Reference catalog (reference_images, reference_embeddings, app_config) is preserved.

-- 1. Truncate user-linked tables (cascade handles FK-linked rows)
truncate table public.events;
truncate table public.generations;
truncate table public.users;

-- 2. Drop is_demo flag (demo login removed)
alter table public.users drop column if exists is_demo;

-- 3. Drop auto-gen UUID default — IDs now come from auth.users
alter table public.users alter column id drop default;

-- 4. Link public.users.id → auth.users.id
--    Allows service-side lookup by Supabase UID; cascade-deletes if auth user is removed
alter table public.users
  add constraint users_auth_fkey
  foreign key (id) references auth.users(id) on delete cascade;

-- 5. Trigger: mirror auth.users → public.users on every new sign-up
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.users (id, email)
  values (new.id, new.email)
  on conflict (id) do update set email = excluded.email;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- 6. Enable RLS on all public tables
--    n8n uses SUPABASE_SERVICE_KEY which bypasses RLS; these policies protect direct client access.
alter table public.users enable row level security;
alter table public.generations enable row level security;
alter table public.events enable row level security;
alter table public.reference_images enable row level security;
alter table public.reference_embeddings enable row level security;
alter table public.app_config enable row level security;

-- Users: read own row only
create policy "users_select_own" on public.users
  for select using (auth.uid() = id);

-- Generations: full CRUD on own rows
create policy "generations_select_own" on public.generations
  for select using (auth.uid() = user_id);
create policy "generations_insert_own" on public.generations
  for insert with check (auth.uid() = user_id);
create policy "generations_update_own" on public.generations
  for update using (auth.uid() = user_id);

-- Events: insert only from client (service key reads for analytics)
create policy "events_insert_own" on public.events
  for insert with check (auth.uid() = user_id);

-- Reference images + embeddings: publicly readable (design catalog)
create policy "reference_images_public_read" on public.reference_images
  for select using (true);
create policy "reference_embeddings_public_read" on public.reference_embeddings
  for select using (true);

-- App config: publicly readable
create policy "app_config_public_read" on public.app_config
  for select using (true);
