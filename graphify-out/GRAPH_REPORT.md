# Graph Report - .  (2026-05-08)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1136 nodes · 1377 edges · 95 communities detected
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 184 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 99|Community 99]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 133|Community 133]]
- [[_COMMUNITY_Community 134|Community 134]]
- [[_COMMUNITY_Community 135|Community 135]]
- [[_COMMUNITY_Community 153|Community 153]]
- [[_COMMUNITY_Community 154|Community 154]]
- [[_COMMUNITY_Community 155|Community 155]]
- [[_COMMUNITY_Community 156|Community 156]]
- [[_COMMUNITY_Community 157|Community 157]]
- [[_COMMUNITY_Community 158|Community 158]]
- [[_COMMUNITY_Community 159|Community 159]]
- [[_COMMUNITY_Community 160|Community 160]]
- [[_COMMUNITY_Community 161|Community 161]]
- [[_COMMUNITY_Community 162|Community 162]]
- [[_COMMUNITY_Community 163|Community 163]]
- [[_COMMUNITY_Community 164|Community 164]]
- [[_COMMUNITY_Community 165|Community 165]]
- [[_COMMUNITY_Community 166|Community 166]]
- [[_COMMUNITY_Community 167|Community 167]]
- [[_COMMUNITY_Community 195|Community 195]]
- [[_COMMUNITY_Community 196|Community 196]]
- [[_COMMUNITY_Community 197|Community 197]]
- [[_COMMUNITY_Community 198|Community 198]]
- [[_COMMUNITY_Community 199|Community 199]]
- [[_COMMUNITY_Community 200|Community 200]]
- [[_COMMUNITY_Community 201|Community 201]]
- [[_COMMUNITY_Community 202|Community 202]]
- [[_COMMUNITY_Community 203|Community 203]]
- [[_COMMUNITY_Community 204|Community 204]]
- [[_COMMUNITY_Community 205|Community 205]]

## God Nodes (most connected - your core abstractions)
1. `Canvas Screen Main Component` - 22 edges
2. `Minimalist Style` - 18 edges
3. `API Client with JWT Auth` - 15 edges
4. `App Store Zustand (Auth, Credits, Prefs)` - 13 edges
5. `API Specification` - 13 edges
6. `NewSession 2-Step Upload and Brief` - 12 edges
7. `Library Session Grid View` - 11 edges
8. `AuthGate JWT Expiry Guard` - 11 edges
9. `build_workflow()` - 11 edges
10. `build_workflow()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Canvas Screen Main Component` --references--> `Manual 11-Step Test Script`  [INFERRED]
  src/components/screens/Canvas.tsx → tests/manual-test-script.md
- `Nemotron VL 1B v2 Embeddings` --semantically_similar_to--> `CLIP ViT-B/32 Retrieval (Phase 2 Plan)`  [INFERRED] [semantically similar]
  n8n/WORKFLOW_SYSTEM.md → plans/backend-implementation-plan.md
- `submit()` --calls--> `absoluteUrl()`  [INFERRED]
  src\components\canvas\ChatPanel.tsx → src\lib\api.ts
- `commit()` --calls--> `absoluteUrl()`  [INFERRED]
  src\components\screens\Canvas.tsx → src\lib\api.ts
- `onFile()` --calls--> `absoluteUrl()`  [INFERRED]
  src\components\screens\NewSession.tsx → src\lib\api.ts

## Hyperedges (group relationships)
- **Seed Pipeline Data Flow: Tag â†’ Embed â†’ Upload â†’ Insert** — seed_tagger, seed_embedder, seed_uploader, seed_inserter [EXTRACTED 0.95]
- **Vector Retrieval Stack: CLIP Model + HNSW Index + reference_embeddings table** — clip_vitb32_model, hnsw_index, table_reference_embeddings [EXTRACTED 0.95]
- **Generation Backend Switching: env var + admin endpoint + adapters** — image_backend_env, admin_ab_config_endpoint, gemini_adapter, local_gpu_adapter [EXTRACTED 0.90]
- **Japandi Style Design Cluster** — 15_japandi_style, 16_japandi_living_room, 17_japandi_futuristic_mandir, 18_japandi_kids_bunk, 19_japandi_bedroom, 20_japandi_living_room, 21_japandi_living_room, 22_japandi_living_room, 24_japandi_kitchen, 25_japandi_bedroom, 27_japandi_kids_room, 28_japandi_futuristic_mandir [EXTRACTED 1.00]
- **Industrial Style Design Cluster** — 13_industrial_style, 14_industrial_style_kids_room, 2_industrial_kitchen_wood, 3_industrial_bedroom [EXTRACTED 1.00]
- **Mid-Century Modern Style Design Cluster** — 29_midcentury_futuristic_mandir, 29_midcentury_modern, 30_midcentury_living_room, 31_midcentury_study_room, 32_midcentury_kids_room [EXTRACTED 1.00]
- **Minimalist Bedroom Designs** — 36_minimalist_bedroom_bedside, 37_minimalist_futuristic_bedroom_skyline, 39_minimalist_bedroom, 43_minimalist_bedroom_alt, 44_minimalist_bedroom_city_view, 48_minimalist_futuristic_bedroom [INFERRED 0.90]
- **Minimalist Living and Study Spaces** — 40_minimalist_living_room_lamp, 42_minimalist_study_room, 45_minimalist_living_room_fireplace, 47_minimalist_study_room_alt, 52_minimalist_living_room_city_wall [INFERRED 0.85]
- **Mid-Century Modern and Industrial Style Designs** — 33_mid_century_modern_kitchen, 34_mid_century_modern_bedroom, 35_mid_century_modern_bedroom_windows, 4_industrial_study_room, 5_industrial_bedroom [INFERRED 0.80]
- **Modern Ethnic Fusion Bedrooms with Balcony** — 58_ethnic_fusion_bedroom_balcony, 62_ethnic_fusion_bedroom_balcony2, 68_ethnic_fusion_bedroom_balcony3, 69_ethnic_fusion_bedroom, 72_ethnic_fusion_bedroom_city_skyline [INFERRED 0.90]
- **Futuristic Ethnic Fusion Mandir Room Designs** — 57_futuristic_mandir_holographic, 59_futuristic_monday_room_glowing, 64_ethnic_fusion_mandir_city_skyline, 70_ethnic_fusion_mandir_holographic_symbols [INFERRED 0.88]
- **Minimalist and Industrial Interior Styles** — 53_minimalist_living_room_fireplace, 54_minimalist_bedroom, 6_industrial_study_green, 7_industrial_living_room [INFERRED 0.75]
- **Neo and New Contemporary Style Bedroom Designs** — 73_contemporary_bedroom_dark, 79_neo_contemporary_bedroom, 82_new_contemporary_bedroom, 83_neo_contemporary_bedroom, 85_new_contemporary_bedroom, 89_new_contemporary_bedroom_natural_light [INFERRED 0.85]
- **Neo-Contemporary Futuristic Mandir Room Designs** — 76_neo_contemporary_futuristic_mandir, 90_new_contemporary_futuristic_mandir [INFERRED 0.90]
- **Industrial Style Interior Rooms with Green Plants** — 8_industrial_living_room, 9_industrial_bedroom_plants [INFERRED 0.85]
- **Scandinavian Interior Design Samples Cluster** — scandinavian_bedroom_style, scandinavian_kids_room, scandinavian_futuristic_mandir, scandinavian_holographic_mandir, scandinavian_bedroom_design [INFERRED 0.95]
- **Orchestrated Generation Pipeline Components** — three_agent_pipeline, spatial_aware_retrieval, fts_candidate_pool, gemini_image_generation [EXTRACTED 1.00]
- **Draft Edit Commit Revision Workflow** — generate_orchestrated_endpoint, generate_edit_endpoint, generate_commit_endpoint, revision_chain [EXTRACTED 1.00]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (69): Anno Annotation Text Component, absoluteUrl Backend URL Helper, API Client with JWT Auth, API generateOrchestrated Endpoint, API Mock Stubs for Sessions and Notifications, api.d.ts OpenAPI TypeScript Types, AtelierMark Brand Logo SVG, AuthGate JWT Expiry Guard (+61 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (57): A/B Test System â€” Config A vs Config B, GET/PUT /admin/ab-config â€” A/B Configuration, GET /admin/metrics Endpoint, X-Admin-Token Authentication, Atelier Credit System, Atelier Design System â€” atelier/* + mobile/* components, Atelier Mobile Studio PWA, POST /auth/magic-link â€” Mock Auth Endpoint (+49 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (42): DB RPC: admin_metrics, DB RPC: retrieve_candidates_text (FTS), DB RPC: retrieve_references, DB Table: events, DB Table: generations, DB Table: reference_embeddings, DB Table: reference_images, DB Table: users (+34 more)

### Community 3 - "Community 3"
Cohesion: 0.1
Nodes (43): Mid-Century Modern Kitchen Design, Mid-Century Modern Bedroom with Natural Light, Mid-Century Modern Bedroom with Window Light, Minimalist Bedroom with Bedside Table and Pendant Lamp, Minimalist Futuristic Bedroom with City Skyline View, Minimalist Kitchen Design, Minimalist Style Bedroom, Minimalist Living Room with Hanging Lamp (+35 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (33): embed_all_images(), embed_single_image(), init_cache_dir(), load_clip_model(), main(), CLIP ViT-B/32 image embedder. Designed to run on SSH VPS with GPU or locally on, CLI entrypoint for running on VPS., Initialize cache directory. (+25 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (33): embed_all_images(), embed_single_image(), init_cache_dir(), load_clip_model(), main(), CLIP ViT-B/32 image embedder. Designed to run on SSH VPS with GPU or locally on, CLI entrypoint for running on VPS., Initialize cache directory. (+25 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (32): apply_migration(), ensure_migrations_table(), fix_database_url(), get_applied_migrations(), get_connection(), get_migration_files(), main(), Database migration runner. Executes SQL migration files in order against the Su (+24 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (32): apply_migration(), ensure_migrations_table(), fix_database_url(), get_applied_migrations(), get_connection(), get_migration_files(), main(), Database migration runner. Executes SQL migration files in order against the Su (+24 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (35): Industrial Style, Kitchen, Wooden Elements, Industrial Style Kids Room, Kids Room, Swing, Japandi Style Living Room with Tall Ceiling, Seating Area (+27 more)

### Community 9 - "Community 9"
Cohesion: 0.12
Nodes (21): code_node(), http_node(), inline_event_log(), inline_jwt_sign(), inline_jwt_verify(), inline_save_generation(), _js(), _load_env() (+13 more)

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (21): code_node(), http_node(), inline_event_log(), inline_save_generation(), inline_supabase_verify(), _js(), _load_env(), new_id() (+13 more)

### Community 11 - "Community 11"
Cohesion: 0.09
Nodes (26): commit: Fetch reference URLs, commit: Verify JWT, POST /generate/commit (webhook), reference_embeddings table (2048d vector), reference_images table, reference_images caption_enhanced + spatial_signature columns (mig 012), edit: Verify JWT (sub-wf), POST /generate/edit (webhook) (+18 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (26): Attached Balcony, Modern Ethnic Fusion Style, Modern Ethnic Fusion Study Room with Balcony, Study Room, Modern Ethnic Fusion Futuristic Mandir with Holographic Design, Futuristic Interior Style, Holographic Home Design, Mandir Room (+18 more)

### Community 13 - "Community 13"
Cohesion: 0.16
Nodes (22): activate(), _api(), _bake_code_env(), build_workflow(), code_node(), deactivate(), deploy(), _fix_if_conditions() (+14 more)

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (24): Concept: CLIP ViT-B/32 Embeddings, Concept: Gemini 2.5 Flash Auto-Tagging, Concept: Idempotent Seed Pipeline, Concept: Supabase Storage Bucket, Concept: Vector Similarity Search, README: Database Layer, Extension: uuid-ossp, Extension: pgvector (+16 more)

### Community 15 - "Community 15"
Cohesion: 0.16
Nodes (22): activate(), _api(), _bake_code_env(), build_workflow(), code_node(), deactivate(), deploy(), _fix_if_conditions() (+14 more)

### Community 16 - "Community 16"
Cohesion: 0.17
Nodes (23): CLIP ViT-B/32 Embedding Model, Database Connection Configuration, Database Schema Documentation, Seed Report â€” 104 Images, Database Layer README â€” Phase 1, DATABASE_URL Environment Variable, HNSW Vector Index (cosine, reference_embeddings), Migration Runner â€” migrate.py (+15 more)

### Community 17 - "Community 17"
Cohesion: 0.12
Nodes (18): build_consolidated.py Workflow Merge Script, FTS Candidate Pool (retrieve_candidates_text RPC), Full Audit Report (2026-04-28), Google Gemini Image Generation, Hardcoded Secrets Security Finding (C-01), JWT Gate Pattern (Auth on Every Endpoint), Database Migration Audit, n8n Consolidated Workflow (220 nodes) (+10 more)

### Community 18 - "Community 18"
Cohesion: 0.26
Nodes (13): delete_existing_embedding(), embed_multimodal(), fetch_reference_images(), http_delete(), http_get(), http_post(), image_to_data_uri(), insert_embedding() (+5 more)

### Community 19 - "Community 19"
Cohesion: 0.26
Nodes (13): delete_existing_embedding(), embed_multimodal(), fetch_reference_images(), http_delete(), http_get(), http_post(), image_to_data_uri(), insert_embedding() (+5 more)

### Community 20 - "Community 20"
Cohesion: 0.15
Nodes (14): Contemporary Bedroom with Dark Elements, Contemporary Style, Dark Aesthetics, Contemporary Kitchen with Attached Lawn, Kitchen Design, Outdoor Integration - Attached Lawn, Neo-Contemporary Bedroom Design, New Contemporary Style Bedroom Design (+6 more)

### Community 21 - "Community 21"
Cohesion: 0.18
Nodes (8): submit(), absoluteUrl(), ApiError, readToken(), request(), commit(), generate(), onFile()

### Community 22 - "Community 22"
Cohesion: 0.18
Nodes (8): submit(), absoluteUrl(), ApiError, readToken(), request(), commit(), generate(), onFile()

### Community 23 - "Community 23"
Cohesion: 0.17
Nodes (12): Interior Design Sample 1 â€” Industrial Futuristic Mandir, Interior Design Sample 10 â€” Industrial Futuristic Mandala Mandir, Interior Design Sample 100 â€” Scandinavian Bedroom, Interior Design Sample 101 â€” Scandinavian Living Room Fireplace, Interior Design Sample 102 â€” Scandinavian Living Room, Interior Design Sample 103 â€” Scandinavian Kitchen, Interior Design Sample 104 â€” Scandinavian Kitchen, Interior Design Sample 11 â€” Industrial Futuristic Mandir Holographic (+4 more)

### Community 24 - "Community 24"
Cohesion: 0.18
Nodes (12): Cozy Environment, Fireplace, Minimalist Living Room with Fireplace, Minimalist Style, Minimalist Style Bedroom, Minimalist Style, Attached Lawn, Curved Couch (+4 more)

### Community 25 - "Community 25"
Cohesion: 0.2
Nodes (10): DB Table: reference_images, Google Gemini Image Generation API, OpenRouter Embeddings API (Nemotron VL 1B v2), Supabase REST API, Agent 1 Orchestrator Prompt, Agent 2 Retriever Prompt, Commit Generation Prompt, Draft Generation Prompt (+2 more)

### Community 26 - "Community 26"
Cohesion: 0.42
Nodes (7): cosine(), embed_request(), http_get(), http_post(), l2_normalize(), main(), norm()

### Community 27 - "Community 27"
Cohesion: 0.42
Nodes (7): cosine(), embed_request(), http_get(), http_post(), l2_normalize(), main(), norm()

### Community 28 - "Community 28"
Cohesion: 0.46
Nodes (7): describe_node(), execution_order(), generate_table(), main(), BFS from root nodes (those with no incoming connections)., short_label(), update_docs()

### Community 29 - "Community 29"
Cohesion: 0.25
Nodes (8): commit: Fetch parent generation, events table, generations table, edit: Chain depth RPC, export: Fetch generation row, admin_metrics() RPC, generation_chain_depth() RPC, session: Fetch session generations

### Community 30 - "Community 30"
Cohesion: 0.46
Nodes (7): describe_node(), execution_order(), generate_table(), main(), BFS from root nodes (those with no incoming connections)., short_label(), update_docs()

### Community 31 - "Community 31"
Cohesion: 0.32
Nodes (8): Neo-Contemporary Study Room, Neo-Contemporary Style, Study Room, Neo-Contemporary Study Room Design, New Contemporary Study Room with Top Aesthetics, Scandinavian Style Study Room, Scandinavian Style, Scandinavian Style Study Room (Variant)

### Community 32 - "Community 32"
Cohesion: 0.32
Nodes (8): Center Table, Green Plants in Living Room, Industrial Style Living Room with Swing, Industrial Style, Indoor Swing Feature, Green Plants in Bedroom, Industrial Style Bedroom with Green Plants, Industrial Style Bedroom

### Community 33 - "Community 33"
Cohesion: 0.29
Nodes (8): Lit Home Floor Rug, Hanging Chandelier, Holographic Idols, Mandir Room (Prayer Room), Neo-Contemporary Futuristic Mandir Room, Futuristic Mandir Design, New Contemporary Futuristic Mandir Room with Triangular Angles, Triangular Shaped Angle Design

### Community 35 - "Community 35"
Cohesion: 0.33
Nodes (6): commit: Log event (sub-wf), edit: Log event (sub-wf), export: Log event (sub-wf), orch: Log Agent 1 (sub-wf), upload: Log event (sub-wf), wf_event_log sub-workflow (referenced)

### Community 37 - "Community 37"
Cohesion: 0.4
Nodes (6): Bedroom, Japandi Style, Japandi Style Bedroom, Japandi Style Bedroom, Green Moss Inspired Design, Japanese Bedroom with Moss Design

### Community 38 - "Community 38"
Cohesion: 0.33
Nodes (6): Living Room with Staircase, Neo Contemporary Living Room with Staircase, Staircase Feature, Hallway Design, Neo-Contemporary Hallway with Staircase, Staircase in Hallway

### Community 39 - "Community 39"
Cohesion: 0.5
Nodes (3): useHydrated(), AuthGate(), jwtIsExpired()

### Community 40 - "Community 40"
Cohesion: 0.8
Nodes (4): api_get(), api_put(), patch_generate_draft(), patch_retrieve_references()

### Community 41 - "Community 41"
Cohesion: 0.4
Nodes (3): get_connection(), Shared database connection utility. Handles IPv4 forcing and URL-encoded passwo, Create a database connection from DATABASE_URL env var.

### Community 42 - "Community 42"
Cohesion: 0.4
Nodes (3): get_connection(), Shared database connection utility. Handles IPv4 forcing and URL-encoded passwo, Create a database connection from DATABASE_URL env var.

### Community 43 - "Community 43"
Cohesion: 0.8
Nodes (4): api_get(), api_put(), patch_generate_draft(), patch_retrieve_references()

### Community 44 - "Community 44"
Cohesion: 0.4
Nodes (5): Dining Table, Modern Internet Fusion Kitchen with Dining Table, Kitchen Design, Modern Ethnic Fusion Kitchen with Seating, Kitchen Seating

### Community 45 - "Community 45"
Cohesion: 0.5
Nodes (5): Kids Room Design, Neo Contemporary Kids Room, Bunk Beds, Neo-Contemplative Kids Room with Bunk Beds, New Contemporary Style Kids Room

### Community 46 - "Community 46"
Cohesion: 0.67
Nodes (2): ctaHref(), handleCta()

### Community 47 - "Community 47"
Cohesion: 0.67
Nodes (2): ctaHref(), handleCta()

### Community 48 - "Community 48"
Cohesion: 0.5
Nodes (1): Patches live n8n workflows to:   1. Replace wf_jwt_verify -> wf_supabase_verify

### Community 49 - "Community 49"
Cohesion: 0.5
Nodes (4): Modern Ethnic Fusion Style (Kids), Kids Room, Modern Ethnic Fusion Kids Room, Modern Ethnic Fusion Kids Room Design

### Community 50 - "Community 50"
Cohesion: 0.5
Nodes (4): Green Color Theme, Industrial Style Study Room with Green Theme, Industrial Style, Industrial Style (Living Room)

### Community 51 - "Community 51"
Cohesion: 0.5
Nodes (4): A/B Model Testing Harness, CLIP ViT-B/32 Retrieval (Phase 2 Plan), FastAPI Backend Implementation Plan (Phase 2), Nemotron VL 1B v2 Embeddings

### Community 52 - "Community 52"
Cohesion: 0.67
Nodes (1): Page()

### Community 57 - "Community 57"
Cohesion: 0.67
Nodes (3): commit: Save generation (sub-wf), edit: Save generation (sub-wf), wf_save_generation sub-workflow (referenced)

### Community 58 - "Community 58"
Cohesion: 0.67
Nodes (3): enhance: Call vision LLM (OpenRouter), enhance: When Executed by Another Workflow, wf_enhance_caption Workflow

### Community 59 - "Community 59"
Cohesion: 0.67
Nodes (1): Standalone CLIP embedding script for VPS. No database dependencies — just reads

### Community 60 - "Community 60"
Cohesion: 0.67
Nodes (1): Standalone CLIP embedding script for VPS. No database dependencies — just reads

### Community 61 - "Community 61"
Cohesion: 0.67
Nodes (1): Page()

### Community 66 - "Community 66"
Cohesion: 0.67
Nodes (3): DB Table: users, Sub-workflow: wf_jwt_sign, Sub-workflow: wf_jwt_verify

### Community 93 - "Community 93"
Cohesion: 1.0
Nodes (2): Next.js Backend URL Config, Remote Image Patterns Config

### Community 94 - "Community 94"
Cohesion: 1.0
Nodes (2): Session Canvas Page Route, Session Export Page Route

### Community 96 - "Community 96"
Cohesion: 1.0
Nodes (2): GET /health (webhook), health Workflow

### Community 97 - "Community 97"
Cohesion: 1.0
Nodes (2): commit: Fetch image_model, app_config table

### Community 98 - "Community 98"
Cohesion: 1.0
Nodes (2): user-uploads / user-outputs storage buckets, upload: Upload to storage (Supabase)

### Community 99 - "Community 99"
Cohesion: 1.0
Nodes (1): Seed pipeline configuration. Central constants for paths, styles, room types, a

### Community 100 - "Community 100"
Cohesion: 1.0
Nodes (1): Quick test of Gemini tagging with thinking disabled.

### Community 101 - "Community 101"
Cohesion: 1.0
Nodes (1): Seed pipeline configuration. Central constants for paths, styles, room types, a

### Community 102 - "Community 102"
Cohesion: 1.0
Nodes (1): Quick test of Gemini tagging with thinking disabled.

### Community 133 - "Community 133"
Cohesion: 1.0
Nodes (1): DB Table: reference_embeddings

### Community 134 - "Community 134"
Cohesion: 1.0
Nodes (2): Bunk Beds, Modern Ethnic Fusion with Bunk Beds (Ruined)

### Community 135 - "Community 135"
Cohesion: 1.0
Nodes (2): n8n Task Runner Sandbox env Block, ns::Config Code Node Pattern

### Community 153 - "Community 153"
Cohesion: 1.0
Nodes (1): Next.js TypeScript References

### Community 154 - "Community 154"
Cohesion: 1.0
Nodes (1): PostCSS Config

### Community 155 - "Community 155"
Cohesion: 1.0
Nodes (1): Library Page Route

### Community 156 - "Community 156"
Cohesion: 1.0
Nodes (1): New Session Page Route

### Community 157 - "Community 157"
Cohesion: 1.0
Nodes (1): Notifications Page Route

### Community 158 - "Community 158"
Cohesion: 1.0
Nodes (1): Profile Page Route

### Community 159 - "Community 159"
Cohesion: 1.0
Nodes (1): Top-Up Credits Page Route

### Community 160 - "Community 160"
Cohesion: 1.0
Nodes (1): Sign-In Page Route

### Community 161 - "Community 161"
Cohesion: 1.0
Nodes (1): commit: Call Gemini

### Community 162 - "Community 162"
Cohesion: 1.0
Nodes (1): edit: Call Gemini

### Community 163 - "Community 163"
Cohesion: 1.0
Nodes (1): orch: Agent 1 (Orchestrator) OpenRouter call

### Community 164 - "Community 164"
Cohesion: 1.0
Nodes (1): orch: Agent 2 (Retriever) OpenRouter call

### Community 165 - "Community 165"
Cohesion: 1.0
Nodes (1): INTERIOR DESIGN RAG (consolidated) Workflow

### Community 166 - "Community 166"
Cohesion: 1.0
Nodes (1): Execution 174 (retrieve_references workflow — error)

### Community 167 - "Community 167"
Cohesion: 1.0
Nodes (1): Execution 16 (workflow JbnB5CPdoqgCl75F — error)

### Community 195 - "Community 195"
Cohesion: 1.0
Nodes (1): Sub-workflow: wf_event_log

### Community 196 - "Community 196"
Cohesion: 1.0
Nodes (1): Sub-workflow: wf_save_generation

### Community 197 - "Community 197"
Cohesion: 1.0
Nodes (1): Supabase Storage API

### Community 198 - "Community 198"
Cohesion: 1.0
Nodes (1): OpenRouter Chat Completions API

### Community 199 - "Community 199"
Cohesion: 1.0
Nodes (1): DB Table: generations

### Community 200 - "Community 200"
Cohesion: 1.0
Nodes (1): DB Table: events

### Community 201 - "Community 201"
Cohesion: 1.0
Nodes (1): DB RPC: retrieve_references

### Community 202 - "Community 202"
Cohesion: 1.0
Nodes (1): DB RPC: admin_metrics

### Community 203 - "Community 203"
Cohesion: 1.0
Nodes (1): CLAUDE.md â€” Project Workflow Instructions

### Community 204 - "Community 204"
Cohesion: 1.0
Nodes (1): Database Python Dependencies

### Community 205 - "Community 205"
Cohesion: 1.0
Nodes (1): Industrial Style Living Room Design

## Ambiguous Edges - Review These
- `Style Concept: Industrial-Futuristic Mandir` → `Style Concept: Scandinavian Interior Design`  [AMBIGUOUS]
  Interior design samples/100.txt · relation: semantically_similar_to

## Knowledge Gaps
- **300 isolated node(s):** `Next.js TypeScript References`, `Next.js Backend URL Config`, `Remote Image Patterns Config`, `PostCSS Config`, `App Home Page (Workspace Entry)` (+295 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 46`** (4 nodes): `ctaHref()`, `handleCta()`, `handleMarkAll()`, `Notifications.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (4 nodes): `Notifications.tsx`, `ctaHref()`, `handleCta()`, `handleMarkAll()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (4 nodes): `api()`, `patch_nodes()`, `update_verify_ref.py`, `Patches live n8n workflows to:   1. Replace wf_jwt_verify -> wf_supabase_verify`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (3 nodes): `Page()`, `page.tsx`, `page.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (3 nodes): `main()`, `embed_images.py`, `Standalone CLIP embedding script for VPS. No database dependencies — just reads`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (3 nodes): `embed_images.py`, `main()`, `Standalone CLIP embedding script for VPS. No database dependencies — just reads`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (3 nodes): `Page()`, `page.tsx`, `page.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 93`** (2 nodes): `Next.js Backend URL Config`, `Remote Image Patterns Config`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 94`** (2 nodes): `Session Canvas Page Route`, `Session Export Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 96`** (2 nodes): `GET /health (webhook)`, `health Workflow`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 97`** (2 nodes): `commit: Fetch image_model`, `app_config table`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 98`** (2 nodes): `user-uploads / user-outputs storage buckets`, `upload: Upload to storage (Supabase)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 99`** (2 nodes): `config.py`, `Seed pipeline configuration. Central constants for paths, styles, room types, a`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 100`** (2 nodes): `test_tag.py`, `Quick test of Gemini tagging with thinking disabled.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 101`** (2 nodes): `config.py`, `Seed pipeline configuration. Central constants for paths, styles, room types, a`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 102`** (2 nodes): `test_tag.py`, `Quick test of Gemini tagging with thinking disabled.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 133`** (2 nodes): `DB Table: reference_embeddings`, `seed_log.txt`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 134`** (2 nodes): `Bunk Beds`, `Modern Ethnic Fusion with Bunk Beds (Ruined)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 135`** (2 nodes): `n8n Task Runner Sandbox env Block`, `ns::Config Code Node Pattern`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 153`** (1 nodes): `Next.js TypeScript References`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 154`** (1 nodes): `PostCSS Config`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 155`** (1 nodes): `Library Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 156`** (1 nodes): `New Session Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 157`** (1 nodes): `Notifications Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 158`** (1 nodes): `Profile Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 159`** (1 nodes): `Top-Up Credits Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 160`** (1 nodes): `Sign-In Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 161`** (1 nodes): `commit: Call Gemini`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 162`** (1 nodes): `edit: Call Gemini`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 163`** (1 nodes): `orch: Agent 1 (Orchestrator) OpenRouter call`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 164`** (1 nodes): `orch: Agent 2 (Retriever) OpenRouter call`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 165`** (1 nodes): `INTERIOR DESIGN RAG (consolidated) Workflow`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 166`** (1 nodes): `Execution 174 (retrieve_references workflow — error)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 167`** (1 nodes): `Execution 16 (workflow JbnB5CPdoqgCl75F — error)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 195`** (1 nodes): `Sub-workflow: wf_event_log`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 196`** (1 nodes): `Sub-workflow: wf_save_generation`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 197`** (1 nodes): `Supabase Storage API`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 198`** (1 nodes): `OpenRouter Chat Completions API`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 199`** (1 nodes): `DB Table: generations`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 200`** (1 nodes): `DB Table: events`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 201`** (1 nodes): `DB RPC: retrieve_references`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 202`** (1 nodes): `DB RPC: admin_metrics`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 203`** (1 nodes): `CLAUDE.md â€” Project Workflow Instructions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 204`** (1 nodes): `Database Python Dependencies`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 205`** (1 nodes): `Industrial Style Living Room Design`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Style Concept: Industrial-Futuristic Mandir` and `Style Concept: Scandinavian Interior Design`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `main()` connect `Community 4` to `Community 6`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 5` to `Community 7`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **Why does `insert_all()` connect `Community 6` to `Community 4`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Canvas Screen Main Component` (e.g. with `NewSession 2-Step Upload and Brief` and `Manual 11-Step Test Script`) actually correct?**
  _`Canvas Screen Main Component` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Next.js TypeScript References`, `Next.js Backend URL Config`, `Remote Image Patterns Config` to the rest of the system?**
  _300 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.06 - nodes in this community are weakly interconnected._