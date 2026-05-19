# Graph Report - Interior design RAG  (2026-05-14)

## Corpus Check
- 27 files · ~7,286,900 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 184 nodes · 244 edges · 21 communities detected
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.8)
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
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]

## God Nodes (most connected - your core abstractions)
1. `build_workflow()` - 11 edges
2. `insert_all()` - 8 edges
3. `WorkflowMerger` - 8 edges
4. `main()` - 7 edges
5. `main()` - 6 edges
6. `upload_all_images()` - 6 edges
7. `inline_save_generation()` - 6 edges
8. `code_node()` - 6 edges
9. `get_connection()` - 5 edges
10. `pick_canonical_room_type()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `get_connection()` --calls--> `insert_all()`  [INFERRED]
  database\migrate.py → database\seed\inserter.py
- `get_connection()` --calls--> `run_tests()`  [INFERRED]
  database\migrate.py → database\tests\verify_seed.py
- `pick_canonical_style_tags_singleton()` --calls--> `insert_all()`  [INFERRED]
  database\seed\canonical_style_tags.py → database\seed\inserter.py
- `insert_all()` --calls--> `main()`  [INFERRED]
  database\seed\inserter.py → database\seed\run_seed.py
- `main()` --calls--> `upload_all_images()`  [INFERRED]
  database\seed\run_seed.py → database\seed\uploader.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (21): code_node(), http_node(), inline_event_log(), inline_save_generation(), inline_supabase_verify(), _js(), _load_env(), new_id() (+13 more)

### Community 1 - "Community 1"
Cohesion: 0.16
Nodes (22): activate(), _api(), _bake_code_env(), build_workflow(), code_node(), deactivate(), deploy(), _fix_if_conditions() (+14 more)

### Community 2 - "Community 2"
Cohesion: 0.16
Nodes (16): apply_migration(), ensure_migrations_table(), fix_database_url(), get_applied_migrations(), get_connection(), get_migration_files(), main(), Database migration runner. Executes SQL migration files in order against the Su (+8 more)

### Community 3 - "Community 3"
Cohesion: 0.17
Nodes (13): extract_json(), Gemini 2.5 Flash auto-tagger. Sends each image + its caption to Gemini for stru, Tag all images in the dataset.      Args:         image_entries: List of dict, Extract JSON from a text response, handling markdown code fences., Tag a single image using Gemini 2.5 Flash.      Args:         image_path: Pat, tag_all_images(), tag_single_image(), discover_images() (+5 more)

### Community 4 - "Community 4"
Cohesion: 0.2
Nodes (12): _from_caption_room_objects(), _from_room_string_only(), _haystack(), pick_canonical_room_type(), Collapse caption + tagger room + detected_objects to one canonical room_type str, Return one of: bedroom, kids room, dining room, kitchen, mandir, living room., get_seed_owner_id(), insert_all() (+4 more)

### Community 5 - "Community 5"
Cohesion: 0.27
Nodes (9): ensure_bucket(), get_supabase_client(), Supabase Storage uploader. Uploads reference images to a Supabase Storage bucke, Upload all images to Supabase Storage.          Args:         image_entries:, Create Supabase client., Create the storage bucket if it doesn't exist., Upload a single image to Supabase Storage.          Args:         supabase: S, upload_all_images() (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.31
Nodes (7): main(), print_report(), Seed verification test suite. Validates that the database is properly seeded wi, Print formatted test report., Run all verification tests., run_tests(), TestResult

### Community 7 - "Community 7"
Cohesion: 0.36
Nodes (7): _from_caption_and_tags(), _from_tags_only(), _haystack(), pick_canonical_style_tags_singleton(), Collapse caption + tagger output to a single DB style slug (six UI styles). Mir, Same alias collapse order as migration 013 (first matching tag wins)., Return exactly one-element text[] for reference_images.style_tags.     Default

### Community 8 - "Community 8"
Cohesion: 0.46
Nodes (7): describe_node(), execution_order(), generate_table(), main(), BFS from root nodes (those with no incoming connections)., short_label(), update_docs()

### Community 9 - "Community 9"
Cohesion: 0.43
Nodes (6): die(), http(), main(), Execute SQL via Supabase's postgres REST endpoint (service role)., # NOTE: the admin API endpoint for listing users is paginated., run_sql()

### Community 10 - "Community 10"
Cohesion: 0.53
Nodes (4): apply_patches(), get_nested(), main(), set_nested()

### Community 11 - "Community 11"
Cohesion: 0.4
Nodes (3): get_connection(), Shared database connection utility. Handles IPv4 forcing and URL-encoded passwo, Create a database connection from DATABASE_URL env var.

### Community 12 - "Community 12"
Cohesion: 0.8
Nodes (4): api_get(), api_put(), patch_generate_draft(), patch_retrieve_references()

### Community 13 - "Community 13"
Cohesion: 0.67
Nodes (3): _load_migrate(), main(), Wipe Postgres public schema and app storage rows (DESTRUCTIVE).  Requires DATA

### Community 14 - "Community 14"
Cohesion: 0.5
Nodes (1): Patches live n8n workflows to:   1. Replace wf_jwt_verify -> wf_supabase_verify

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (2): apply(), main()

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (1): Seed pipeline configuration. Central constants for paths, styles, room types, a

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (1): Quick test of Gemini tagging with thinking disabled.

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (1): Insert a demo user if not exists. Returns user_id.

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Insert a single reference image row.      Args:         conn: psycopg2 connec

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Insert all data into the database.      Args:         image_entries: List of

## Knowledge Gaps
- **57 isolated node(s):** `Shared database connection utility. Handles IPv4 forcing and URL-encoded passwo`, `Create a database connection from DATABASE_URL env var.`, `Database migration runner. Executes SQL migration files in order against the Su`, `URL-encode the password in a database URL to handle special characters.`, `Create a database connection from DATABASE_URL env var.` (+52 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 14`** (4 nodes): `api()`, `patch_nodes()`, `update_verify_ref.py`, `Patches live n8n workflows to:   1. Replace wf_jwt_verify -> wf_supabase_verify`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (3 nodes): `apply()`, `main()`, `patch_orchestrated_phase5.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (2 nodes): `config.py`, `Seed pipeline configuration. Central constants for paths, styles, room types, a`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (2 nodes): `test_tag.py`, `Quick test of Gemini tagging with thinking disabled.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `Insert a demo user if not exists. Returns user_id.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `Insert a single reference image row.      Args:         conn: psycopg2 connec`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `Insert all data into the database.      Args:         image_entries: List of`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `insert_all()` connect `Community 4` to `Community 2`, `Community 3`, `Community 7`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 3` to `Community 4`, `Community 5`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Why does `get_connection()` connect `Community 2` to `Community 4`, `Community 6`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `insert_all()` (e.g. with `get_connection()` and `pick_canonical_room_type()`) actually correct?**
  _`insert_all()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `main()` (e.g. with `tag_all_images()` and `upload_all_images()`) actually correct?**
  _`main()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Shared database connection utility. Handles IPv4 forcing and URL-encoded passwo`, `Create a database connection from DATABASE_URL env var.`, `Database migration runner. Executes SQL migration files in order against the Su` to the rest of the system?**
  _57 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._