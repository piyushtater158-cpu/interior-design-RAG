# Atelier Frontend

Next.js 14 + React 18 + Tailwind + Zustand. The web UI for the AI-powered interior design assistant MVP (Phase 3 of 3).

## Prerequisites

- Node 20+
- Backend running at `http://localhost:8000` — see `/contracts/backend-url.md`.

## Setup

```bash
npm install
npm run gen:types   # regenerate src/lib/api.d.ts from ../contracts/openapi.yaml (run after any contract change)
cp .env.local.example .env.local
```

## Env vars

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:8000` | Backend base URL; CORS must allow the frontend origin. |

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Next.js dev server at `http://localhost:3000` |
| `npm run build` | Production build |
| `npm run start` | Serve the production build |
| `npm run lint` | Next lint |
| `npm run gen:types` | Regenerate OpenAPI → TS types |
| `npm run test:smoke` | Playwright smoke test (3 steps) |

## Routes

| Route | Screen |
|---|---|
| `/` | Landing |
| `/signin` | Mock magic-link sign-in |
| `/app` | Room type picker |
| `/app/new?type=<room>` | Upload + style picker |
| `/app/session/[sessionId]` | Generation canvas (responsive: mobile shelf ↔ iPad drawer ↔ desktop three-rail) |
| `/app/session/[sessionId]/export` | Final image + download |

## Design system

The visual language — Atelier Mobile — was extracted once from the design file into `src/components/atelier/*` (design atoms) and `src/components/mobile/*` (mobile shell). Screens compose these; they do not introduce new primitives.

### 🔒 Stitch freeze notice

**The design file (`Atelier Mobile.html`) was read once. It must not be re-imported.** Re-exporting from Stitch after this point will overwrite hand-wired state, API calls, and responsive breakpoints. Any further design changes go through direct edits to `src/components/atelier/*` and `src/components/mobile/*`.

## Testing

- Playwright smoke: `npm run test:smoke` (mocks the backend by default; set `BACKEND_LIVE=1` to hit real backend).
- Manual 11-step flow: `tests/manual-test-script.md` — run on desktop + iPad before every demo.

## State

Two Zustand stores, both persisted to `localStorage`:

- `src/store/app.ts` — JWT, user, mock credits, A/B config.
- `src/store/session.ts` — active session, revisions, references, chat.

JWT is read from `app` store first, with an `atelier:jwt` localStorage fallback for the API client (`src/lib/api.ts`).

## Deployment

Not deployed. See `/contracts/frontend-url.md` — Vercel deploy is deferred until the backend has a staging URL.
