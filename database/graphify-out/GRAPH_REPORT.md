# Graph Report - database  (2026-04-30)

## Corpus Check
- Corpus is ~5,689 words - fits in a single context window. You may not need a graph.

## Summary
- 112 nodes · 140 edges · 13 communities detected
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Migration Runner|Migration Runner]]
- [[_COMMUNITY_Database Indexes|Database Indexes]]
- [[_COMMUNITY_Schema Concepts and Documentation|Schema Concepts and Documentation]]
- [[_COMMUNITY_Database Inserter|Database Inserter]]
- [[_COMMUNITY_Supabase Storage Uploader|Supabase Storage Uploader]]
- [[_COMMUNITY_CLIP Embedding Processor|CLIP Embedding Processor]]
- [[_COMMUNITY_Seed Pipeline Orchestrator|Seed Pipeline Orchestrator]]
- [[_COMMUNITY_Seed Verification Tests|Seed Verification Tests]]
- [[_COMMUNITY_Gemini Image Tagger|Gemini Image Tagger]]
- [[_COMMUNITY_DB Connection Utility|DB Connection Utility]]
- [[_COMMUNITY_VPS Embedding Script|VPS Embedding Script]]
- [[_COMMUNITY_Seed Configuration|Seed Configuration]]
- [[_COMMUNITY_Tag Test Utility|Tag Test Utility]]

## God Nodes (most connected - your core abstractions)
1. `main()` - 8 edges
2. `main()` - 7 edges
3. `insert_all()` - 7 edges
4. `Migration 003: Create Indexes` - 7 edges
5. `Table: reference_images` - 7 edges
6. `upload_all_images()` - 6 edges
7. `Table: reference_embeddings` - 6 edges
8. `Table: generations` - 6 edges
9. `get_connection()` - 5 edges
10. `embed_all_images()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `insert_all()` --calls--> `get_connection()`  [INFERRED]
  seed\inserter.py → migrate.py
- `run_tests()` --calls--> `get_connection()`  [INFERRED]
  tests\verify_seed.py → migrate.py
- `main()` --calls--> `insert_all()`  [INFERRED]
  seed\run_seed.py → seed\inserter.py
- `main()` --calls--> `tag_all_images()`  [INFERRED]
  seed\run_seed.py → seed\processors\tagger.py
- `main()` --calls--> `upload_all_images()`  [INFERRED]
  seed\run_seed.py → seed\uploader.py

## Communities

### Community 0 - "Migration Runner"
Cohesion: 0.16
Nodes (16): apply_migration(), ensure_migrations_table(), fix_database_url(), get_applied_migrations(), get_connection(), get_migration_files(), main(), Database migration runner. Executes SQL migration files in order against the Su (+8 more)

### Community 1 - "Database Indexes"
Cohesion: 0.29
Nodes (12): Index: idx_events_user_time, Index: idx_gen_parent, Index: idx_gen_user_session, Index: idx_ref_quality, Index: idx_ref_room_type, Index: idx_ref_style_tags (GIN), Migration 002: Create Tables, Migration 003: Create Indexes (+4 more)

### Community 2 - "Schema Concepts and Documentation"
Cohesion: 0.21
Nodes (12): Concept: CLIP ViT-B/32 Embeddings, Concept: Gemini 2.5 Flash Auto-Tagging, Concept: Idempotent Seed Pipeline, Concept: Supabase Storage Bucket, Concept: Vector Similarity Search, README: Database Layer, Extension: uuid-ossp, Extension: pgvector (+4 more)

### Community 3 - "Database Inserter"
Cohesion: 0.27
Nodes (9): insert_all(), insert_demo_user(), insert_reference_embedding(), insert_reference_image(), Database inserter. Takes tagged, embedded, uploaded image data and inserts into, Insert all data into the database.          Args:         image_entries: List, Insert a demo user if not exists. Returns user_id., Insert a single reference image row.          Args:         conn: psycopg2 co (+1 more)

### Community 4 - "Supabase Storage Uploader"
Cohesion: 0.27
Nodes (9): ensure_bucket(), get_supabase_client(), Supabase Storage uploader. Uploads reference images to a Supabase Storage bucke, Upload all images to Supabase Storage.          Args:         image_entries:, Create Supabase client., Create the storage bucket if it doesn't exist., Upload a single image to Supabase Storage.          Args:         supabase: S, upload_all_images() (+1 more)

### Community 5 - "CLIP Embedding Processor"
Cohesion: 0.24
Nodes (9): embed_all_images(), embed_single_image(), load_clip_model(), main(), CLIP ViT-B/32 image embedder. Designed to run on SSH VPS with GPU or locally on, CLI entrypoint for running on VPS., Load CLIP ViT-B/32 model. Requires sentence-transformers to be installed., Generate CLIP embedding for a single image.          Returns:         numpy a (+1 more)

### Community 6 - "Seed Pipeline Orchestrator"
Cohesion: 0.28
Nodes (8): init_cache_dir(), Initialize cache directory., discover_images(), generate_seed_report(), main(), Main seed pipeline orchestrator. Reads local images + captions, tags via Gemini, Scan the local dataset and build a list of image entries.          Returns:, Generate the seed report markdown file.          Args:         entries: image

### Community 7 - "Seed Verification Tests"
Cohesion: 0.31
Nodes (7): main(), print_report(), Seed verification test suite. Validates that the database is properly seeded wi, Print formatted test report., Run all verification tests., run_tests(), TestResult

### Community 8 - "Gemini Image Tagger"
Cohesion: 0.32
Nodes (7): extract_json(), Gemini 2.5 Flash auto-tagger. Sends each image + its caption to Gemini for stru, Tag all images in the dataset.      Args:         image_entries: List of dict, Extract JSON from a text response, handling markdown code fences., Tag a single image using Gemini 2.5 Flash.      Args:         image_path: Pat, tag_all_images(), tag_single_image()

### Community 9 - "DB Connection Utility"
Cohesion: 0.4
Nodes (3): get_connection(), Shared database connection utility. Handles IPv4 forcing and URL-encoded passwo, Create a database connection from DATABASE_URL env var.

### Community 10 - "VPS Embedding Script"
Cohesion: 0.67
Nodes (1): Standalone CLIP embedding script for VPS. No database dependencies — just reads

### Community 11 - "Seed Configuration"
Cohesion: 1.0
Nodes (1): Seed pipeline configuration. Central constants for paths, styles, room types, a

### Community 12 - "Tag Test Utility"
Cohesion: 1.0
Nodes (1): Quick test of Gemini tagging with thinking disabled.

## Knowledge Gaps
- **41 isolated node(s):** `Shared database connection utility. Handles IPv4 forcing and URL-encoded passwo`, `Create a database connection from DATABASE_URL env var.`, `Database migration runner. Executes SQL migration files in order against the Su`, `URL-encode the password in a database URL to handle special characters.`, `Create a database connection from DATABASE_URL env var.` (+36 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `VPS Embedding Script`** (3 nodes): `main()`, `embed_images.py`, `Standalone CLIP embedding script for VPS. No database dependencies — just reads`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Seed Configuration`** (2 nodes): `config.py`, `Seed pipeline configuration. Central constants for paths, styles, room types, a`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Tag Test Utility`** (2 nodes): `test_tag.py`, `Quick test of Gemini tagging with thinking disabled.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Seed Pipeline Orchestrator` to `Gemini Image Tagger`, `Database Inserter`, `Supabase Storage Uploader`, `CLIP Embedding Processor`?**
  _High betweenness centrality (0.291) - this node is a cross-community bridge._
- **Why does `insert_all()` connect `Database Inserter` to `Migration Runner`, `Seed Pipeline Orchestrator`?**
  _High betweenness centrality (0.253) - this node is a cross-community bridge._
- **Why does `get_connection()` connect `Migration Runner` to `Database Inserter`, `Seed Verification Tests`?**
  _High betweenness centrality (0.219) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `main()` (e.g. with `tag_all_images()` and `upload_all_images()`) actually correct?**
  _`main()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `insert_all()` (e.g. with `get_connection()` and `main()`) actually correct?**
  _`insert_all()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Shared database connection utility. Handles IPv4 forcing and URL-encoded passwo`, `Create a database connection from DATABASE_URL env var.`, `Database migration runner. Executes SQL migration files in order against the Su` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._