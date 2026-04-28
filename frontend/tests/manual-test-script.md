# Frontend Manual Test Script

Run with backend at `http://localhost:8000` and frontend at `http://localhost:3000`.

**Viewports to cover:** mobile 390×844 · iPad 768×1024 · desktop 1440×900.

| # | Action | Expected |
|---|---|---|
| 1 | Open site in desktop Chrome | Landing page renders: Atelier mark, serif headline, "Sign in to start" button. |
| 2 | Click "Sign in" → enter `test@demo.com` → submit | Redirects to `/app`, JWT stored in `localStorage` under `atelier:jwt`. |
| 3 | Click the "Bedroom" card | Navigates to `/app/new?type=bedroom`. |
| 4 | Upload `frontend/tests/fixtures/test-bedroom.jpg` (or any JPG), pick "Scandinavian" | Preview renders, style card shows active border, "Generate draft" enabled. |
| 5 | Click "Generate draft" | Spinner → redirects to `/app/session/<uuid>`; canvas shows generated image ≤10s. |
| 6 | Check right rail / refs sheet | 3–5 reference thumbnails visible with similarity badges. |
| 7 | Chat edit: "change the bed to rattan" → send | New image appears in revision stack; chat shows user+system messages. |
| 8 | Tap previous revision thumbnail (desktop rail / mobile sheet) | Canvas reverts to earlier revision (no API call). |
| 9 | Click "Commit" (shelf button or right-rail clay button) | Higher-fidelity image appears as new revision with `commit` kind; credits drop by 3. |
| 10 | Click "Export" → "Download PNG" | PNG downloads from backend `/data/outputs/...`. |
| 11 | Repeat 3–10 on iPad viewport (Chrome DevTools 768×1024) | Same flow works: canvas uses bottom shelf, sheets slide up. |

## Regression spot-checks

- Refresh `/app/session/<id>` mid-session → revisions re-hydrate from `/generations/session/<id>`.
- Submit a 7th edit in a single chain → `ErrorBanner` surfaces the 400 cap error.
- Sign out by clearing localStorage → visiting `/app` redirects to `/signin`.
- Landing works when signed out; visiting `/app/*` while signed out shows spinner then redirect.

## Demo-day fallback

Record a screen capture of steps 1–10 on desktop + steps 3–10 on iPad. Keep the file at `frontend/tests/fallback.mp4`.
