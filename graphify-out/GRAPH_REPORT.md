# Graph Report - C:/Users/asus/OneDrive/Documents/Claude/Projects/Interior design RAG  (2026-04-30)

## Corpus Check
- 90 files · ~500,000 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 542 nodes · 681 edges · 43 communities detected
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Frontend API and UI Layer|Frontend API and UI Layer]]
- [[_COMMUNITY_n8n Reference Retrieval and RPC|n8n Reference Retrieval and RPC]]
- [[_COMMUNITY_Generation Workflows and JWT Auth|Generation Workflows and JWT Auth]]
- [[_COMMUNITY_Workflow Build and Code Tools|Workflow Build and Code Tools]]
- [[_COMMUNITY_CLIP Embedding Seed Pipeline|CLIP Embedding Seed Pipeline]]
- [[_COMMUNITY_Database Migration Runner|Database Migration Runner]]
- [[_COMMUNITY_Workflow Deploy and Patch Tools|Workflow Deploy and Patch Tools]]
- [[_COMMUNITY_Seed Pipeline Concepts|Seed Pipeline Concepts]]
- [[_COMMUNITY_n8n Embedding Functions|n8n Embedding Functions]]
- [[_COMMUNITY_Orchestrator and Vision LLM|Orchestrator and Vision LLM]]
- [[_COMMUNITY_Session and Export API|Session and Export API]]
- [[_COMMUNITY_Generation Event Logging|Generation Event Logging]]
- [[_COMMUNITY_Auth Magic Link Flow|Auth Magic Link Flow]]
- [[_COMMUNITY_Database Inserter|Database Inserter]]
- [[_COMMUNITY_Supabase Storage Upload|Supabase Storage Upload]]
- [[_COMMUNITY_Prompt Templates|Prompt Templates]]
- [[_COMMUNITY_Frontend Auth and Hooks|Frontend Auth and Hooks]]
- [[_COMMUNITY_Frontend Format Utilities|Frontend Format Utilities]]
- [[_COMMUNITY_Workflow Graph Utilities|Workflow Graph Utilities]]
- [[_COMMUNITY_Admin Metrics Flow|Admin Metrics Flow]]
- [[_COMMUNITY_Health Check Workflow|Health Check Workflow]]
- [[_COMMUNITY_Upload Room Photo|Upload Room Photo]]
- [[_COMMUNITY_Spatial Caption Schema|Spatial Caption Schema]]
- [[_COMMUNITY_App Config Migration|App Config Migration]]
- [[_COMMUNITY_Frontend Brand Components|Frontend Brand Components]]
- [[_COMMUNITY_Frontend Route Pages|Frontend Route Pages]]
- [[_COMMUNITY_Tag Test Utilities|Tag Test Utilities]]
- [[_COMMUNITY_Seed Configuration|Seed Configuration]]
- [[_COMMUNITY_Misc Community 59|Misc Community 59]]
- [[_COMMUNITY_Misc Community 60|Misc Community 60]]
- [[_COMMUNITY_Misc Community 62|Misc Community 62]]
- [[_COMMUNITY_Misc Community 63|Misc Community 63]]
- [[_COMMUNITY_Misc Community 64|Misc Community 64]]
- [[_COMMUNITY_Misc Community 82|Misc Community 82]]
- [[_COMMUNITY_Misc Community 83|Misc Community 83]]
- [[_COMMUNITY_Misc Community 84|Misc Community 84]]
- [[_COMMUNITY_Misc Community 85|Misc Community 85]]
- [[_COMMUNITY_Misc Community 86|Misc Community 86]]
- [[_COMMUNITY_Misc Community 87|Misc Community 87]]
- [[_COMMUNITY_Misc Community 88|Misc Community 88]]
- [[_COMMUNITY_Misc Community 89|Misc Community 89]]
- [[_COMMUNITY_Misc Community 90|Misc Community 90]]
- [[_COMMUNITY_Misc Community 91|Misc Community 91]]

## God Nodes (most connected - your core abstractions)
1. `Canvas Screen Main Component` - 22 edges
2. `API Client with JWT Auth` - 15 edges
3. `App Store Zustand (Auth, Credits, Prefs)` - 13 edges
4. `NewSession 2-Step Upload and Brief` - 12 edges
5. `Library Session Grid View` - 11 edges
6. `AuthGate JWT Expiry Guard` - 11 edges
7. `build_workflow()` - 11 edges
8. `Workspace Room Type Picker` - 10 edges
9. `Anno Annotation Text Component` - 9 edges
10. `Session Store Zustand (Revisions, Chat)` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Canvas Screen Main Component` --references--> `Manual 11-Step Test Script`  [INFERRED]
  src/components/screens/Canvas.tsx → tests/manual-test-script.md
- `submit()` --calls--> `absoluteUrl()`  [INFERRED]
  src\components\canvas\ChatPanel.tsx → src\lib\api.ts
- `commit()` --calls--> `absoluteUrl()`  [INFERRED]
  src\components\screens\Canvas.tsx → src\lib\api.ts
- `onFile()` --calls--> `absoluteUrl()`  [INFERRED]
  src\components\screens\NewSession.tsx → src\lib\api.ts
- `generate()` --calls--> `absoluteUrl()`  [INFERRED]
  src\components\screens\NewSession.tsx → src\lib\api.ts

## Communities

### Community 0 - "Frontend API and UI Layer"
Cohesion: 0.07
Nodes (64): Anno Annotation Text Component, absoluteUrl Backend URL Helper, API Client with JWT Auth, API generateOrchestrated Endpoint, API Mock Stubs for Sessions and Notifications, api.d.ts OpenAPI TypeScript Types, AtelierMark Brand Logo SVG, AuthGate JWT Expiry Guard (+56 more)

### Community 1 - "n8n Reference Retrieval and RPC"
Cohesion: 0.06
Nodes (39): DB RPC: admin_metrics, DB RPC: retrieve_candidates_text (FTS), DB RPC: retrieve_references, DB Table: reference_embeddings, DB Table: reference_images, Google Gemini Image Generation API, n8n REST API (localhost:5678), OpenRouter Chat Completions API (+31 more)

### Community 2 - "Generation Workflows and JWT Auth"
Cohesion: 0.05
Nodes (45): commit: Fetch reference URLs, commit: Verify JWT, POST /generate/commit (webhook), reference_embeddings table (2048d vector), reference_images table, reference_images caption_enhanced + spatial_signature columns (mig 012), draft: Fetch reference URLs, draft: Verify JWT (inline HMAC) (+37 more)

### Community 3 - "Workflow Build and Code Tools"
Cohesion: 0.12
Nodes (21): code_node(), http_node(), inline_event_log(), inline_jwt_sign(), inline_jwt_verify(), inline_save_generation(), _js(), _load_env() (+13 more)

### Community 4 - "CLIP Embedding Seed Pipeline"
Cohesion: 0.09
Nodes (24): embed_all_images(), embed_single_image(), init_cache_dir(), load_clip_model(), main(), CLIP ViT-B/32 image embedder. Designed to run on SSH VPS with GPU or locally on, CLI entrypoint for running on VPS., Initialize cache directory. (+16 more)

### Community 5 - "Database Migration Runner"
Cohesion: 0.1
Nodes (23): apply_migration(), ensure_migrations_table(), fix_database_url(), get_applied_migrations(), get_connection(), get_migration_files(), main(), Database migration runner. Executes SQL migration files in order against the Su (+15 more)

### Community 6 - "Workflow Deploy and Patch Tools"
Cohesion: 0.16
Nodes (22): activate(), _api(), _bake_code_env(), build_workflow(), code_node(), deactivate(), deploy(), _fix_if_conditions() (+14 more)

### Community 7 - "Seed Pipeline Concepts"
Cohesion: 0.14
Nodes (24): Concept: CLIP ViT-B/32 Embeddings, Concept: Gemini 2.5 Flash Auto-Tagging, Concept: Idempotent Seed Pipeline, Concept: Supabase Storage Bucket, Concept: Vector Similarity Search, README: Database Layer, Extension: uuid-ossp, Extension: pgvector (+16 more)

### Community 8 - "n8n Embedding Functions"
Cohesion: 0.15
Nodes (18): DB Table: events, DB Table: generations, DB Table: users, Supabase Storage API, Sub-workflow: wf_event_log, Sub-workflow: wf_jwt_sign, Sub-workflow: wf_jwt_verify, Sub-workflow: wf_save_generation (+10 more)

### Community 9 - "Orchestrator and Vision LLM"
Cohesion: 0.26
Nodes (13): delete_existing_embedding(), embed_multimodal(), fetch_reference_images(), http_delete(), http_get(), http_post(), image_to_data_uri(), insert_embedding() (+5 more)

### Community 10 - "Session and Export API"
Cohesion: 0.18
Nodes (8): submit(), absoluteUrl(), ApiError, readToken(), request(), commit(), generate(), onFile()

### Community 11 - "Generation Event Logging"
Cohesion: 0.18
Nodes (11): commit: Fetch parent generation, events table, generations table, draft: Insert generation row, draft: Log event (POST events), edit: Chain depth RPC, export: Fetch generation row, retrieve: Log event (POST events) (+3 more)

### Community 12 - "Auth Magic Link Flow"
Cohesion: 0.27
Nodes (9): insert_all(), insert_demo_user(), insert_reference_embedding(), insert_reference_image(), Database inserter. Takes tagged, embedded, uploaded image data and inserts into, Insert all data into the database.          Args:         image_entries: List, Insert a demo user if not exists. Returns user_id., Insert a single reference image row.          Args:         conn: psycopg2 co (+1 more)

### Community 13 - "Database Inserter"
Cohesion: 0.27
Nodes (9): ensure_bucket(), get_supabase_client(), Supabase Storage uploader. Uploads reference images to a Supabase Storage bucke, Upload all images to Supabase Storage.          Args:         image_entries:, Create Supabase client., Create the storage bucket if it doesn't exist., Upload a single image to Supabase Storage.          Args:         supabase: S, upload_all_images() (+1 more)

### Community 14 - "Supabase Storage Upload"
Cohesion: 0.42
Nodes (7): cosine(), embed_request(), http_get(), http_post(), l2_normalize(), main(), norm()

### Community 15 - "Prompt Templates"
Cohesion: 0.46
Nodes (7): describe_node(), execution_order(), generate_table(), main(), BFS from root nodes (those with no incoming connections)., short_label(), update_docs()

### Community 17 - "Frontend Auth and Hooks"
Cohesion: 0.33
Nodes (6): commit: Log event (sub-wf), edit: Log event (sub-wf), export: Log event (sub-wf), orch: Log Agent 1 (sub-wf), upload: Log event (sub-wf), wf_event_log sub-workflow (referenced)

### Community 18 - "Frontend Format Utilities"
Cohesion: 0.5
Nodes (3): useHydrated(), AuthGate(), jwtIsExpired()

### Community 19 - "Workflow Graph Utilities"
Cohesion: 0.4
Nodes (5): Google Font Loading (Inter, Instrument Serif, JetBrains Mono), Root App Layout, App Home Page (Workspace Entry), Root Page (Landing Entry), Playwright E2E Test Config

### Community 20 - "Admin Metrics Flow"
Cohesion: 0.8
Nodes (4): api_get(), api_put(), patch_generate_draft(), patch_retrieve_references()

### Community 21 - "Health Check Workflow"
Cohesion: 0.4
Nodes (3): get_connection(), Shared database connection utility. Handles IPv4 forcing and URL-encoded passwo, Create a database connection from DATABASE_URL env var.

### Community 22 - "Upload Room Photo"
Cohesion: 0.67
Nodes (2): ctaHref(), handleCta()

### Community 23 - "Spatial Caption Schema"
Cohesion: 0.5
Nodes (4): commit: Call Gemini, draft: Call Gemini, edit: Call Gemini, Google Gemini API (generativelanguage.googleapis.com)

### Community 24 - "App Config Migration"
Cohesion: 0.67
Nodes (1): Page()

### Community 29 - "Frontend Brand Components"
Cohesion: 0.67
Nodes (3): commit: Fetch image_model, app_config table, draft: Fetch image_model

### Community 30 - "Frontend Route Pages"
Cohesion: 0.67
Nodes (3): commit: Save generation (sub-wf), edit: Save generation (sub-wf), wf_save_generation sub-workflow (referenced)

### Community 31 - "Tag Test Utilities"
Cohesion: 0.67
Nodes (3): user-uploads / user-outputs storage buckets, draft: Upload PNG to storage, upload: Upload to storage (Supabase)

### Community 32 - "Seed Configuration"
Cohesion: 0.67
Nodes (1): Standalone CLIP embedding script for VPS. No database dependencies — just reads

### Community 59 - "Misc Community 59"
Cohesion: 1.0
Nodes (2): Next.js Backend URL Config, Remote Image Patterns Config

### Community 60 - "Misc Community 60"
Cohesion: 1.0
Nodes (2): Session Canvas Page Route, Session Export Page Route

### Community 62 - "Misc Community 62"
Cohesion: 1.0
Nodes (2): GET /health (webhook), health Workflow

### Community 63 - "Misc Community 63"
Cohesion: 1.0
Nodes (1): Seed pipeline configuration. Central constants for paths, styles, room types, a

### Community 64 - "Misc Community 64"
Cohesion: 1.0
Nodes (1): Quick test of Gemini tagging with thinking disabled.

### Community 82 - "Misc Community 82"
Cohesion: 1.0
Nodes (1): Next.js TypeScript References

### Community 83 - "Misc Community 83"
Cohesion: 1.0
Nodes (1): PostCSS Config

### Community 84 - "Misc Community 84"
Cohesion: 1.0
Nodes (1): Library Page Route

### Community 85 - "Misc Community 85"
Cohesion: 1.0
Nodes (1): New Session Page Route

### Community 86 - "Misc Community 86"
Cohesion: 1.0
Nodes (1): Notifications Page Route

### Community 87 - "Misc Community 87"
Cohesion: 1.0
Nodes (1): Profile Page Route

### Community 88 - "Misc Community 88"
Cohesion: 1.0
Nodes (1): Top-Up Credits Page Route

### Community 89 - "Misc Community 89"
Cohesion: 1.0
Nodes (1): Sign-In Page Route

### Community 90 - "Misc Community 90"
Cohesion: 1.0
Nodes (1): INTERIOR DESIGN RAG (consolidated) Workflow

### Community 91 - "Misc Community 91"
Cohesion: 1.0
Nodes (1): Execution 16 (workflow JbnB5CPdoqgCl75F — error)

## Knowledge Gaps
- **137 isolated node(s):** `Next.js TypeScript References`, `Next.js Backend URL Config`, `Remote Image Patterns Config`, `PostCSS Config`, `App Home Page (Workspace Entry)` (+132 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Upload Room Photo`** (4 nodes): `ctaHref()`, `handleCta()`, `handleMarkAll()`, `Notifications.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App Config Migration`** (3 nodes): `Page()`, `page.tsx`, `page.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Seed Configuration`** (3 nodes): `main()`, `embed_images.py`, `Standalone CLIP embedding script for VPS. No database dependencies — just reads`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 59`** (2 nodes): `Next.js Backend URL Config`, `Remote Image Patterns Config`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 60`** (2 nodes): `Session Canvas Page Route`, `Session Export Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 62`** (2 nodes): `GET /health (webhook)`, `health Workflow`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 63`** (2 nodes): `config.py`, `Seed pipeline configuration. Central constants for paths, styles, room types, a`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 64`** (2 nodes): `test_tag.py`, `Quick test of Gemini tagging with thinking disabled.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 82`** (1 nodes): `Next.js TypeScript References`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 83`** (1 nodes): `PostCSS Config`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 84`** (1 nodes): `Library Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 85`** (1 nodes): `New Session Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 86`** (1 nodes): `Notifications Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 87`** (1 nodes): `Profile Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 88`** (1 nodes): `Top-Up Credits Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 89`** (1 nodes): `Sign-In Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 90`** (1 nodes): `INTERIOR DESIGN RAG (consolidated) Workflow`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc Community 91`** (1 nodes): `Execution 16 (workflow JbnB5CPdoqgCl75F — error)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `CLIP Embedding Seed Pipeline` to `Auth Magic Link Flow`, `Database Inserter`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `insert_all()` connect `Auth Magic Link Flow` to `CLIP Embedding Seed Pipeline`, `Database Migration Runner`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Why does `get_connection()` connect `Database Migration Runner` to `Auth Magic Link Flow`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Canvas Screen Main Component` (e.g. with `NewSession 2-Step Upload and Brief` and `Manual 11-Step Test Script`) actually correct?**
  _`Canvas Screen Main Component` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `NewSession 2-Step Upload and Brief` (e.g. with `Canvas Screen Main Component` and `Workspace Room Type Picker`) actually correct?**
  _`NewSession 2-Step Upload and Brief` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Next.js TypeScript References`, `Next.js Backend URL Config`, `Remote Image Patterns Config` to the rest of the system?**
  _137 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Frontend API and UI Layer` be split into smaller, more focused modules?**
  _Cohesion score 0.07 - nodes in this community are weakly interconnected._