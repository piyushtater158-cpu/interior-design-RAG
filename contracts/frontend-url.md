# Frontend URL

## Dev (local)

```
http://localhost:3000
```

Run with:

```bash
cd frontend
npm install
npm run dev
```

Backend must be running at `http://localhost:8000` — see `contracts/backend-url.md`.

## Staging / Production

**Not deployed.** The backend has no staging URL (`contracts/backend-url.md` marks it `not deployed`), so the frontend is local-only for the MVP demo.

When the backend gets a staging URL:

1. Push this repo to GitHub.
2. Connect the `frontend/` directory as a Vercel project (framework auto-detect = Next.js).
3. Set Vercel env var `NEXT_PUBLIC_BACKEND_URL` = the backend staging URL.
4. Redeploy; paste the resulting URL here in a new **Deployed URL** section.

## Health check

Open `http://localhost:3000` → Landing page should render within a second.

Smoke test against the running dev server:

```bash
cd frontend
npm run test:smoke     # uses mocked backend
BACKEND_LIVE=1 npm run test:smoke   # hits real backend at :8000
```
