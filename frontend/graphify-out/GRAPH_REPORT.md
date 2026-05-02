# Graph Report - frontend  (2026-04-30)

## Corpus Check
- Corpus is ~15,570 words - fits in a single context window. You may not need a graph.

## Summary
- 193 nodes · 210 edges · 17 communities detected
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 24 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_API Client and Auth|API Client and Auth]]
- [[_COMMUNITY_Canvas Session UI|Canvas Session UI]]
- [[_COMMUNITY_Brand and Layout|Brand and Layout]]
- [[_COMMUNITY_API Core Functions|API Core Functions]]
- [[_COMMUNITY_Auth Gate Hooks|Auth Gate Hooks]]
- [[_COMMUNITY_Notifications Screen|Notifications Screen]]
- [[_COMMUNITY_App Page Routes|App Page Routes]]
- [[_COMMUNITY_Next.js Config|Next.js Config]]
- [[_COMMUNITY_Session Routes|Session Routes]]
- [[_COMMUNITY_TS References Config|TS References Config]]
- [[_COMMUNITY_PostCSS Config File|PostCSS Config File]]
- [[_COMMUNITY_Library Page Route|Library Page Route]]
- [[_COMMUNITY_New Session Page|New Session Page]]
- [[_COMMUNITY_Notifications Page|Notifications Page]]
- [[_COMMUNITY_Profile Page|Profile Page]]
- [[_COMMUNITY_Top-Up Page|Top-Up Page]]
- [[_COMMUNITY_Sign-In Page|Sign-In Page]]

## God Nodes (most connected - your core abstractions)
1. `Canvas Screen Main Component` - 22 edges
2. `API Client with JWT Auth` - 15 edges
3. `App Store Zustand (Auth, Credits, Prefs)` - 13 edges
4. `NewSession 2-Step Upload and Brief` - 12 edges
5. `Library Session Grid View` - 11 edges
6. `AuthGate JWT Expiry Guard` - 11 edges
7. `Workspace Room Type Picker` - 10 edges
8. `Anno Annotation Text Component` - 9 edges
9. `Session Store Zustand (Revisions, Chat)` - 9 edges
10. `ChatPanel Edit Interface` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Manual 11-Step Test Script` --references--> `Canvas Screen Main Component`  [INFERRED]
  tests/manual-test-script.md → src/components/screens/Canvas.tsx
- `Frontend README Documentation` --references--> `Session Store Zustand (Revisions, Chat)`  [EXTRACTED]
  README.md → src/store/session.ts
- `submit()` --calls--> `absoluteUrl()`  [INFERRED]
  src\components\canvas\ChatPanel.tsx → src\lib\api.ts
- `commit()` --calls--> `absoluteUrl()`  [INFERRED]
  src\components\screens\Canvas.tsx → src\lib\api.ts
- `onFile()` --calls--> `absoluteUrl()`  [INFERRED]
  src\components\screens\NewSession.tsx → src\lib\api.ts

## Communities

### Community 0 - "API Client and Auth"
Cohesion: 0.15
Nodes (27): absoluteUrl Backend URL Helper, API Client with JWT Auth, API generateOrchestrated Endpoint, API Mock Stubs for Sessions and Notifications, api.d.ts OpenAPI TypeScript Types, AuthGate JWT Expiry Guard, Card Surface Component, FilterChip Pill Toggle (+19 more)

### Community 1 - "Canvas Session UI"
Cohesion: 0.12
Nodes (26): Anno Annotation Text Component, Canvas Commit High-Fidelity Action, Canvas Responsive 3-Rail Layout, Canvas Screen Main Component, Canvas Session Rehydration on Refresh, ChatPanel generateEdit API Call, ChatPanel Edit Interface, CreditsPill Credits Display (+18 more)

### Community 2 - "Brand and Layout"
Cohesion: 0.16
Nodes (16): AtelierMark Brand Logo SVG, BlueprintBg Dot Grid Background, Btn Multi-variant Button, Landing Demo Authentication, Google Font Loading (Inter, Instrument Serif, JetBrains Mono), Root App Layout, Loader Spinner and Shimmer, Manual 11-Step Test Script (+8 more)

### Community 3 - "API Core Functions"
Cohesion: 0.18
Nodes (8): submit(), absoluteUrl(), ApiError, readToken(), request(), commit(), generate(), onFile()

### Community 5 - "Auth Gate Hooks"
Cohesion: 0.5
Nodes (3): useHydrated(), AuthGate(), jwtIsExpired()

### Community 6 - "Notifications Screen"
Cohesion: 0.67
Nodes (2): ctaHref(), handleCta()

### Community 7 - "App Page Routes"
Cohesion: 0.67
Nodes (1): Page()

### Community 38 - "Next.js Config"
Cohesion: 1.0
Nodes (2): Next.js Backend URL Config, Remote Image Patterns Config

### Community 39 - "Session Routes"
Cohesion: 1.0
Nodes (2): Session Canvas Page Route, Session Export Page Route

### Community 57 - "TS References Config"
Cohesion: 1.0
Nodes (1): Next.js TypeScript References

### Community 58 - "PostCSS Config File"
Cohesion: 1.0
Nodes (1): PostCSS Config

### Community 59 - "Library Page Route"
Cohesion: 1.0
Nodes (1): Library Page Route

### Community 60 - "New Session Page"
Cohesion: 1.0
Nodes (1): New Session Page Route

### Community 61 - "Notifications Page"
Cohesion: 1.0
Nodes (1): Notifications Page Route

### Community 62 - "Profile Page"
Cohesion: 1.0
Nodes (1): Profile Page Route

### Community 63 - "Top-Up Page"
Cohesion: 1.0
Nodes (1): Top-Up Credits Page Route

### Community 64 - "Sign-In Page"
Cohesion: 1.0
Nodes (1): Sign-In Page Route

## Knowledge Gaps
- **28 isolated node(s):** `Next.js TypeScript References`, `Next.js Backend URL Config`, `Remote Image Patterns Config`, `PostCSS Config`, `App Home Page (Workspace Entry)` (+23 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Notifications Screen`** (4 nodes): `ctaHref()`, `handleCta()`, `handleMarkAll()`, `Notifications.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `App Page Routes`** (3 nodes): `Page()`, `page.tsx`, `page.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Next.js Config`** (2 nodes): `Next.js Backend URL Config`, `Remote Image Patterns Config`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Session Routes`** (2 nodes): `Session Canvas Page Route`, `Session Export Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `TS References Config`** (1 nodes): `Next.js TypeScript References`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `PostCSS Config File`** (1 nodes): `PostCSS Config`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Library Page Route`** (1 nodes): `Library Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `New Session Page`** (1 nodes): `New Session Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Notifications Page`** (1 nodes): `Notifications Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Profile Page`** (1 nodes): `Profile Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Top-Up Page`** (1 nodes): `Top-Up Credits Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Sign-In Page`** (1 nodes): `Sign-In Page Route`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Canvas Screen Main Component` connect `Canvas Session UI` to `API Client and Auth`, `Brand and Layout`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `API Client with JWT Auth` connect `API Client and Auth` to `Canvas Session UI`, `Brand and Layout`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `Library Session Grid View` connect `API Client and Auth` to `Canvas Session UI`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Canvas Screen Main Component` (e.g. with `NewSession 2-Step Upload and Brief` and `Manual 11-Step Test Script`) actually correct?**
  _`Canvas Screen Main Component` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `NewSession 2-Step Upload and Brief` (e.g. with `Canvas Screen Main Component` and `Workspace Room Type Picker`) actually correct?**
  _`NewSession 2-Step Upload and Brief` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Next.js TypeScript References`, `Next.js Backend URL Config`, `Remote Image Patterns Config` to the rest of the system?**
  _28 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Canvas Session UI` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._