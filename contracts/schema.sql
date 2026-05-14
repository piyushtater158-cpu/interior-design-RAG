-- =============================================================
-- Interior Design Assistant — Full Database Schema (DDL)
-- Mirrors supabase/migrations/100_reset_and_rebuild.sql
-- Run ONLY after DROP SCHEMA public CASCADE; CREATE SCHEMA public; + auth.users cleared.
-- No caption_fts. No retrieve_candidates_text RPC.
-- =============================================================

create extension if not exists "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

create table public.users (
  id          uuid        primary key references auth.users(id) on delete cascade,
  email       text        not null,
  created_at  timestamptz not null default now()
);

create table public.reference_images (
  id                uuid        primary key default uuid_generate_v4(),
  owner_id          uuid        not null references auth.users(id) on delete cascade,
  owner_email       text,
  source            text        not null,
  source_id         text        not null,
  source_url        text        not null,
  license           text,
  storage_path      text        not null,
  caption           text,
  spatial_signature jsonb,
  room_type         text        not null,
  style_tags        text[]      not null,
  dominant_colors   text[],
  detected_objects  text[],
  quality_score     numeric,
  created_at        timestamptz not null default now(),
  unique (owner_id, source, source_id),
  check (room_type in ('bedroom','kids room','dining room','kitchen','mandir','living room')),
  check (
    cardinality(style_tags) = 1
    and style_tags[1] in ('scandinavian','japandi','midcentury','traditional','industrial','boho')
  )
);

create table public.generations (
  id                  uuid        primary key default uuid_generate_v4(),
  user_id             uuid        not null references auth.users(id) on delete cascade,
  session_id          text,
  parent_id           uuid        references public.generations(id) on delete set null,
  prompt              text,
  style_tag           text        check (style_tag is null or style_tag in ('scandinavian','japandi','midcentury','traditional','industrial','boho')),
  room_type           text        check (room_type is null or room_type in ('bedroom','kids room','dining room','kitchen','mandir','living room')),
  output_storage_path text,
  output_url          text,
  picked_refs         jsonb,
  created_at          timestamptz not null default now()
);

create table public.events (
  id          uuid        primary key default uuid_generate_v4(),
  user_id     uuid        references auth.users(id) on delete set null,
  event_type  text        not null,
  payload     jsonb,
  created_at  timestamptz not null default now()
);

create table public.app_config (
  key         text        primary key,
  value       text        not null,
  created_at  timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------
create index idx_ref_owner         on public.reference_images (owner_id);
create index idx_ref_room          on public.reference_images (owner_id, room_type);
create index idx_ref_style         on public.reference_images using gin (style_tags);
create index idx_ref_spatial       on public.reference_images using gin (spatial_signature);
create index idx_gen_user_time     on public.generations (user_id, created_at desc);
create index idx_gen_session       on public.generations (session_id) where session_id is not null;
create index idx_events_user       on public.events (user_id, created_at desc);

-- ---------------------------------------------------------------------------
-- Triggers
-- ---------------------------------------------------------------------------

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
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

create or replace function public.reference_images_sync_owner_email()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if new.owner_id is null then
    new.owner_email := null;
  else
    select au.email into new.owner_email
    from auth.users au
    where au.id = new.owner_id;
  end if;
  return new;
end;
$$;

drop trigger if exists tr_reference_images_sync_owner_email on public.reference_images;
create trigger tr_reference_images_sync_owner_email
  before insert or update of owner_id on public.reference_images
  for each row execute function public.reference_images_sync_owner_email();

-- ---------------------------------------------------------------------------
-- Row-Level Security
-- ---------------------------------------------------------------------------

alter table public.users             enable row level security;
alter table public.reference_images  enable row level security;
alter table public.generations       enable row level security;
alter table public.events            enable row level security;
alter table public.app_config        enable row level security;

-- users: read own row only
create policy "users_select_own" on public.users
  for select using (auth.uid() = id);

-- reference_images: strict per-user, no NULL escape hatch
create policy "ref_select_own" on public.reference_images
  for select using (owner_id = auth.uid());

create policy "ref_insert_own" on public.reference_images
  for insert to authenticated
  with check (owner_id = auth.uid());

create policy "ref_update_own" on public.reference_images
  for update to authenticated
  using (owner_id = auth.uid())
  with check (owner_id = auth.uid());

create policy "ref_delete_own" on public.reference_images
  for delete to authenticated
  using (owner_id = auth.uid());

-- generations: full CRUD on own rows
create policy "gen_select_own" on public.generations
  for select using (auth.uid() = user_id);

create policy "gen_insert_own" on public.generations
  for insert with check (auth.uid() = user_id);

create policy "gen_update_own" on public.generations
  for update using (auth.uid() = user_id);

create policy "gen_delete_own" on public.generations
  for delete using (auth.uid() = user_id);

-- events: client inserts only; service role reads for analytics
create policy "events_insert_own" on public.events
  for insert with check (auth.uid() = user_id);

-- app_config: public read
create policy "app_config_public_read" on public.app_config
  for select using (true);

-- ---------------------------------------------------------------------------
-- Storage bucket policies
-- reference-images: studio/{user_id}/{style}/{room}/{uuid}.{ext}
-- user-uploads:     {user_id}/{upload_id}
-- user-outputs:     outputs/{user_id}/{uuid}.png
-- ---------------------------------------------------------------------------

insert into storage.buckets (id, name, public)
values ('reference-images', 'reference-images', false)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('user-uploads', 'user-uploads', false)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('user-outputs', 'user-outputs', false)
on conflict (id) do nothing;

drop policy if exists "ref_images_objects_select" on storage.objects;
create policy "ref_images_objects_select"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'reference-images'
    and split_part(name, '/', 2) = auth.uid()::text
  );

drop policy if exists "ref_images_objects_insert" on storage.objects;
create policy "ref_images_objects_insert"
  on storage.objects for insert to authenticated
  with check (
    bucket_id = 'reference-images'
    and split_part(name, '/', 1) = 'studio'
    and split_part(name, '/', 2) = auth.uid()::text
  );

drop policy if exists "ref_images_objects_update" on storage.objects;
create policy "ref_images_objects_update"
  on storage.objects for update to authenticated
  using (
    bucket_id = 'reference-images'
    and split_part(name, '/', 2) = auth.uid()::text
  );

drop policy if exists "ref_images_objects_delete" on storage.objects;
create policy "ref_images_objects_delete"
  on storage.objects for delete to authenticated
  using (
    bucket_id = 'reference-images'
    and split_part(name, '/', 2) = auth.uid()::text
  );

drop policy if exists "user_uploads_objects_insert" on storage.objects;
create policy "user_uploads_objects_insert"
  on storage.objects for insert to authenticated
  with check (
    bucket_id = 'user-uploads'
    and split_part(name, '/', 1) = auth.uid()::text
  );

drop policy if exists "user_uploads_objects_select" on storage.objects;
create policy "user_uploads_objects_select"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'user-uploads'
    and split_part(name, '/', 1) = auth.uid()::text
  );

drop policy if exists "user_uploads_objects_delete" on storage.objects;
create policy "user_uploads_objects_delete"
  on storage.objects for delete to authenticated
  using (
    bucket_id = 'user-uploads'
    and split_part(name, '/', 1) = auth.uid()::text
  );

drop policy if exists "user_outputs_objects_insert" on storage.objects;
create policy "user_outputs_objects_insert"
  on storage.objects for insert to authenticated
  with check (
    bucket_id = 'user-outputs'
    and split_part(name, '/', 1) = auth.uid()::text
  );

drop policy if exists "user_outputs_objects_select" on storage.objects;
create policy "user_outputs_objects_select"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'user-outputs'
    and split_part(name, '/', 1) = auth.uid()::text
  );

-- ---------------------------------------------------------------------------
-- App config seed
-- ---------------------------------------------------------------------------
insert into public.app_config (key, value)
values
  ('caption_model',       'qwen/qwen3-vl-8b-instruct'),
  ('orchestrator_model',  'google/gemini-2.5-flash'),
  ('image_model',         'google/gemini-3.1-flash-image-preview')
on conflict (key) do update set value = excluded.value;
