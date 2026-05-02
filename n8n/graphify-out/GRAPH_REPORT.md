# Graph Report - n8n  (2026-04-30)

## Corpus Check
- Corpus is ~17,951 words - fits in a single context window. You may not need a graph.

## Summary
- 237 nodes · 331 edges · 22 communities detected
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 25 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Workflow Build Tools|Workflow Build Tools]]
- [[_COMMUNITY_Workflow Deploy Tools|Workflow Deploy Tools]]
- [[_COMMUNITY_External Services and APIs|External Services and APIs]]
- [[_COMMUNITY_Core DB Tables and Scripts|Core DB Tables and Scripts]]
- [[_COMMUNITY_Generation Webhook Handlers|Generation Webhook Handlers]]
- [[_COMMUNITY_Reference Embeddings Pipeline|Reference Embeddings Pipeline]]
- [[_COMMUNITY_Seed Embedding Functions|Seed Embedding Functions]]
- [[_COMMUNITY_Reference Image Retrieval|Reference Image Retrieval]]
- [[_COMMUNITY_Generation Event Logging|Generation Event Logging]]
- [[_COMMUNITY_Orchestrator and Vision LLM|Orchestrator and Vision LLM]]
- [[_COMMUNITY_Embedding Math Utilities|Embedding Math Utilities]]
- [[_COMMUNITY_Workflow Graph Utilities|Workflow Graph Utilities]]
- [[_COMMUNITY_Auth Magic Link Flow|Auth Magic Link Flow]]
- [[_COMMUNITY_Prompt Templates|Prompt Templates]]
- [[_COMMUNITY_Caption Enhancement Workflow|Caption Enhancement Workflow]]
- [[_COMMUNITY_Admin Metrics RPC|Admin Metrics RPC]]
- [[_COMMUNITY_Session and Export Workflows|Session and Export Workflows]]
- [[_COMMUNITY_Health Check Workflow|Health Check Workflow]]
- [[_COMMUNITY_Upload Room Photo Flow|Upload Room Photo Flow]]
- [[_COMMUNITY_App Config Migration|App Config Migration]]
- [[_COMMUNITY_Storage Buckets Migration|Storage Buckets Migration]]
- [[_COMMUNITY_Seed Nemotron References|Seed Nemotron References]]

## God Nodes (most connected - your core abstractions)
1. `build_workflow()` - 11 edges
2. `WorkflowMerger` - 8 edges
3. `Supabase REST API` - 8 edges
4. `reference_images table` - 8 edges
5. `main()` - 7 edges
6. `code_node()` - 6 edges
7. `inline_save_generation()` - 6 edges
8. `code_node()` - 6 edges
9. `Google Gemini Image Generation API` - 6 edges
10. `DB Table: reference_images` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Agent 2 Retriever Prompt` --references--> `DB Table: reference_images`  [INFERRED]
  n8n/prompts/agent2_retriever.txt → n8n/README.md
- `Commit Generation Prompt` --feeds_into--> `Google Gemini Image Generation API`  [INFERRED]
  n8n/prompts/commit.txt → n8n/README.md
- `Draft Generation Prompt` --feeds_into--> `Google Gemini Image Generation API`  [INFERRED]
  n8n/prompts/draft.txt → n8n/README.md
- `Edit Generation Prompt` --feeds_into--> `Google Gemini Image Generation API`  [INFERRED]
  n8n/prompts/edit.txt → n8n/README.md
- `POST /retrieve/references (webhook)` --feeds_into--> `draft: Verify JWT (inline HMAC)`  [INFERRED]
  n8n/workflows/retrieve_references.json → n8n/workflows/generate_draft.json

## Communities

### Community 0 - "Workflow Build Tools"
Cohesion: 0.12
Nodes (21): code_node(), http_node(), inline_event_log(), inline_jwt_sign(), inline_jwt_verify(), inline_save_generation(), _js(), _load_env() (+13 more)

### Community 1 - "Workflow Deploy Tools"
Cohesion: 0.16
Nodes (22): activate(), _api(), _bake_code_env(), build_workflow(), code_node(), deactivate(), deploy(), _fix_if_conditions() (+14 more)

### Community 2 - "External Services and APIs"
Cohesion: 0.13
Nodes (16): DB RPC: retrieve_candidates_text (FTS), DB RPC: retrieve_references, Google Gemini Image Generation API, n8n REST API (localhost:5678), OpenRouter Chat Completions API, Agent 1 Orchestrator Prompt, Agent 2 Retriever Prompt, Commit Generation Prompt (+8 more)

### Community 3 - "Core DB Tables and Scripts"
Cohesion: 0.15
Nodes (18): DB Table: events, DB Table: generations, DB Table: users, Supabase Storage API, Sub-workflow: wf_event_log, Sub-workflow: wf_jwt_sign, Sub-workflow: wf_jwt_verify, Sub-workflow: wf_save_generation (+10 more)

### Community 4 - "Generation Webhook Handlers"
Cohesion: 0.11
Nodes (20): commit: Verify JWT, POST /generate/commit (webhook), draft: Verify JWT (inline HMAC), POST /generate/draft (webhook), edit: Verify JWT (sub-wf), POST /generate/edit (webhook), POST /generations/:id/export (webhook), Supabase REST API (uzghfpxboktnbcbbthns.supabase.co) (+12 more)

### Community 5 - "Reference Embeddings Pipeline"
Cohesion: 0.17
Nodes (15): DB Table: reference_embeddings, DB Table: reference_images, OpenRouter Embeddings API (Nemotron VL 1B v2), Supabase REST API, n8n README, _seed_enhanced_captions: Config, _seed_enhanced_captions: Fetch all reference_images, _seed_enhanced_captions: Manual trigger (+7 more)

### Community 6 - "Seed Embedding Functions"
Cohesion: 0.26
Nodes (13): delete_existing_embedding(), embed_multimodal(), fetch_reference_images(), http_delete(), http_get(), http_post(), image_to_data_uri(), insert_embedding() (+5 more)

### Community 7 - "Reference Image Retrieval"
Cohesion: 0.18
Nodes (15): commit: Fetch reference URLs, reference_embeddings table (2048d vector), reference_images table, reference_images caption_enhanced + spatial_signature columns (mig 012), draft: Fetch reference URLs, enhance: Update reference_images (PATCH), orch: Fetch candidate pool (retrieve_candidates_text RPC), retrieve: RPC retrieve_references call (+7 more)

### Community 8 - "Generation Event Logging"
Cohesion: 0.18
Nodes (11): commit: Fetch parent generation, events table, generations table, draft: Insert generation row, draft: Log event (POST events), edit: Chain depth RPC, export: Fetch generation row, retrieve: Log event (POST events) (+3 more)

### Community 9 - "Orchestrator and Vision LLM"
Cohesion: 0.2
Nodes (10): enhance: Call vision LLM (OpenRouter), enhance: When Executed by Another Workflow, Execution 174 (retrieve_references workflow — error), OpenRouter API (openrouter.ai), orch: Agent 1 (Orchestrator) OpenRouter call, orch: Agent 2 (Retriever) OpenRouter call, retrieve: Build embeddings request, retrieve: OpenRouter embed (nemotron) (+2 more)

### Community 10 - "Embedding Math Utilities"
Cohesion: 0.42
Nodes (7): cosine(), embed_request(), http_get(), http_post(), l2_normalize(), main(), norm()

### Community 11 - "Workflow Graph Utilities"
Cohesion: 0.46
Nodes (7): describe_node(), execution_order(), generate_table(), main(), BFS from root nodes (those with no incoming connections)., short_label(), update_docs()

### Community 12 - "Auth Magic Link Flow"
Cohesion: 0.25
Nodes (8): DB RPC: admin_metrics, admin_metrics: Check admin token, admin_metrics: Token valid? (IF), admin_metrics: Respond 200, admin_metrics: Respond error, admin_metrics: RPC admin_metrics (HTTP POST /rpc/admin_metrics), admin_metrics: Shape response, admin_metrics: GET /admin/metrics (Webhook)

### Community 13 - "Prompt Templates"
Cohesion: 0.33
Nodes (6): commit: Log event (sub-wf), edit: Log event (sub-wf), export: Log event (sub-wf), orch: Log Agent 1 (sub-wf), upload: Log event (sub-wf), wf_event_log sub-workflow (referenced)

### Community 14 - "Caption Enhancement Workflow"
Cohesion: 0.8
Nodes (4): api_get(), api_put(), patch_generate_draft(), patch_retrieve_references()

### Community 15 - "Admin Metrics RPC"
Cohesion: 0.5
Nodes (4): commit: Call Gemini, draft: Call Gemini, edit: Call Gemini, Google Gemini API (generativelanguage.googleapis.com)

### Community 16 - "Session and Export Workflows"
Cohesion: 0.67
Nodes (3): commit: Fetch image_model, app_config table, draft: Fetch image_model

### Community 17 - "Health Check Workflow"
Cohesion: 0.67
Nodes (3): commit: Save generation (sub-wf), edit: Save generation (sub-wf), wf_save_generation sub-workflow (referenced)

### Community 18 - "Upload Room Photo Flow"
Cohesion: 0.67
Nodes (3): user-uploads / user-outputs storage buckets, draft: Upload PNG to storage, upload: Upload to storage (Supabase)

### Community 20 - "App Config Migration"
Cohesion: 1.0
Nodes (2): GET /health (webhook), health Workflow

### Community 21 - "Storage Buckets Migration"
Cohesion: 1.0
Nodes (1): INTERIOR DESIGN RAG (consolidated) Workflow

### Community 22 - "Seed Nemotron References"
Cohesion: 1.0
Nodes (1): Execution 16 (workflow JbnB5CPdoqgCl75F — error)

## Knowledge Gaps
- **68 isolated node(s):** `Load credentials from project .env file and Windows environment variables.`, `Escape a Python string as a JS single-quoted string literal.`, `Convert an n8n expression value (={{ … }} or =…) to a raw JS expression.`, `Recursively walk obj and replace $('OldName') / $("OldName")     with the names`, `Return 4 nodes that replace wf_save_generation.` (+63 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `App Config Migration`** (2 nodes): `GET /health (webhook)`, `health Workflow`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Storage Buckets Migration`** (1 nodes): `INTERIOR DESIGN RAG (consolidated) Workflow`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Seed Nemotron References`** (1 nodes): `Execution 16 (workflow JbnB5CPdoqgCl75F — error)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Supabase REST API` connect `Reference Embeddings Pipeline` to `Core DB Tables and Scripts`, `Auth Magic Link Flow`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `retrieve_references Workflow` connect `Reference Image Retrieval` to `Orchestrator and Vision LLM`, `Generation Webhook Handlers`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `admin_metrics: RPC admin_metrics (HTTP POST /rpc/admin_metrics)` connect `Auth Magic Link Flow` to `Reference Embeddings Pipeline`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `reference_images table` (e.g. with `retrieve_references Workflow` and `enhance: Update reference_images (PATCH)`) actually correct?**
  _`reference_images table` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Load credentials from project .env file and Windows environment variables.`, `Escape a Python string as a JS single-quoted string literal.`, `Convert an n8n expression value (={{ … }} or =…) to a raw JS expression.` to the rest of the system?**
  _68 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Workflow Build Tools` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._
- **Should `External Services and APIs` be split into smaller, more focused modules?**
  _Cohesion score 0.13 - nodes in this community are weakly interconnected._