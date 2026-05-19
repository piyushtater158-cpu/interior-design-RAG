# Database Layer — Phase 1

AI-Powered Interior Design Assistant: database schema, seed pipeline, and full-text reference retrieval (`retrieve_candidates_text` on `reference_images`).

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Supabase project (Postgres)
- API keys in `.env` (see `.env.example`)

### 2. Install Dependencies

```bash
pip install -r database/requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your keys:

```
DATABASE_URL=postgresql://postgres:<password>@db.<ref>.supabase.co:6543/postgres
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_SERVICE_KEY=<service-role-key>
GOOGLE_AI_STUDIO_KEY=<gemini-api-key>
```

### 4. Run Migrations

```bash
python database/migrate.py
```

This runs, in order, every `*.sql` file in **`database/migrations/`** and **`supabase/migrations/`** (sorted by filename). The canonical rebuild is **`supabase/migrations/100_reset_and_rebuild.sql`** (tables, RLS, storage policies, app_config seed).

**If `migrate.py` fails to connect** (pooler `tenant/user … not found`, timeout, etc.): fix `DATABASE_URL` in `.env` to match [Supabase connect settings](https://supabase.com/dashboard/project/_/settings/database) (direct `db.<ref>.supabase.co:5432` or pooler `…:6543` with the correct username format for your pool mode). Alternatively, open **SQL Editor** in the dashboard and run pending `supabase/migrations/*.sql` in filename order.

**Verify after apply:** run `database/scripts/verify_reference_catalog.sql` in the SQL editor; the first two queries should return **zero rows**.

### 5. Run Seed Pipeline

```bash
# Full pipeline (tag + upload + insert)
python database/seed/run_seed.py

# Tag only (useful for testing Gemini tagging)
python database/seed/run_seed.py --tag-only

# Skip steps
python database/seed/run_seed.py --skip-tag       # Use cached tags
python database/seed/run_seed.py --skip-upload     # Use cached upload URLs
python database/seed/run_seed.py --no-insert       # Don't insert into DB
```

### 6. Verify Seed

```bash
python database/tests/verify_seed.py
```

Runs assertions on catalog shape and FTS RPC. Exits 0 if all pass.

---

## Project Structure

```
database/
  migrate.py              # Migration runner
  db.py                   # Shared DB connection utility
  requirements.txt        # Python dependencies
  migrations/
    001_extensions.sql     # uuid-ossp
    002_create_tables.sql  # Core tables (no vector embeddings)
    003_create_indexes.sql # GIN + B-tree indexes
  seed/
    config.py              # Paths (IMAGES_DIR → reference_dataset/), styles, thresholds
    run_seed.py            # Main orchestrator
    uploader.py            # Supabase Storage upload
    inserter.py            # Database insertion
    processors/
      tagger.py            # Gemini auto-tagging
    cache/                 # Cached API responses (gitignored)
  tests/
    verify_seed.py         # Seed verification test suite
  vps/
    setup.sh               # VPS helper notes (optional)
  wipe_empty.py            # Destructive: empty public + storage catalog (see scripts/)
  scripts/
    wipe_public_schema.sql # SQL used by wipe_empty.py
    verify_reference_catalog.sql
```

## Re-running

The pipeline is idempotent:

- **Migrations**: Track applied files in `_migrations` table
- **Tagging**: Cached in `database/seed/cache/tags/`
- **Uploads**: Skips existing files in Supabase Storage
- **Insertions**: Uses `ON CONFLICT` upsert on `(source, source_id)`

To drop all app tables only (then re-run migrations): `python database/migrate.py --reset` (types `yes` when prompted).

To wipe **`public`** entirely (empty schema) plus app storage bucket rows/policies, then rebuild from migrations: `python database/wipe_empty.py --yes` (requires a working `DATABASE_URL`). The raw SQL is `database/scripts/wipe_public_schema.sql` (paste into Supabase SQL Editor if you prefer).
