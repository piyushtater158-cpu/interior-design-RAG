# Database Layer — Phase 1

AI-Powered Interior Design Assistant: database schema, seed pipeline, and vector search setup.

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Supabase project with pgvector enabled
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

This creates all tables (`users`, `reference_images`, `reference_embeddings`, `generations`, `events`) and indexes.

### 5. Run Seed Pipeline

```bash
# Full pipeline (tag + upload + insert, no embeddings)
python database/seed/run_seed.py

# With CLIP embeddings (requires sentence-transformers)
python database/seed/run_seed.py --with-embeddings

# Tag only (useful for testing Gemini tagging)
python database/seed/run_seed.py --tag-only

# Skip steps
python database/seed/run_seed.py --skip-tag       # Use cached tags
python database/seed/run_seed.py --skip-upload     # Use cached upload URLs
python database/seed/run_seed.py --no-insert       # Don't insert into DB
```

### 6. Generate Embeddings on VPS

If running CLIP on a remote VPS:

```bash
# On VPS:
bash database/vps/setup.sh
python3 database/vps/embed_images.py \
    --images-dir /path/to/images \
    --output-dir /path/to/output \
    --batch-size 32 --gpu

# Copy results back locally:
scp -r user@vps:/path/to/output/* database/seed/cache/embeddings/

# Re-run seed to insert embeddings:
python database/seed/run_seed.py --skip-tag --skip-upload
```

### 7. Verify Seed

```bash
python database/tests/verify_seed.py
```

Runs 9 assertions. Exits 0 if all pass.

---

## Project Structure

```
database/
  migrate.py              # Migration runner
  db.py                   # Shared DB connection utility
  requirements.txt        # Python dependencies
  migrations/
    001_extensions.sql     # pgvector + uuid-ossp
    002_create_tables.sql  # All 5 tables
    003_create_indexes.sql # All indexes (GIN, HNSW, B-tree)
  seed/
    config.py              # Paths, styles, thresholds
    run_seed.py            # Main orchestrator
    uploader.py            # Supabase Storage upload
    inserter.py            # Database insertion
    processors/
      tagger.py            # Gemini 2.5 Flash auto-tagging
      embedder.py          # CLIP ViT-B/32 embedding
    cache/                 # Cached API responses (gitignored)
  tests/
    verify_seed.py         # Seed verification test suite
  vps/
    setup.sh               # VPS dependency installer
    embed_images.py        # Standalone CLIP embedding script

contracts/
  schema.sql               # Full DDL
  schema.md                # Human-readable schema docs
  db-connection.md         # Connection info for backend
  seed-report.md           # Generated after seed run
```

## Re-running

The pipeline is idempotent:
- **Migrations**: Track applied files in `_migrations` table
- **Tagging**: Cached in `database/seed/cache/tags/`
- **Uploads**: Skips existing files in Supabase Storage
- **Insertions**: Uses `ON CONFLICT` upsert on `(source, source_id)`
- **Embeddings**: Cached in `database/seed/cache/embeddings/`

To fully reset: `python database/migrate.py --reset`
