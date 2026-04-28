# Demo Script — 5 minutes

**Audience:** investors / design-studio principals.
**Setup:** backend running at `:8000`, frontend at `:3000`, a sample bedroom JPG at hand, iPad mirrored to a second screen for the second half.

## One-liner

> "Atelier is a designer's co-pilot. Upload a room, describe the mood, iterate in plain language, commit when it's right, and export. Built for studios — not for end-consumers."

## Walkthrough

| Time | Action | Narration |
|---|---|---|
| 0:00–0:30 | Desktop. Open `http://localhost:3000`. Click **Sign in to start** → enter `demo@example.com` → submit. | "Magic-link sign-in. In the MVP it's mocked — in v1 it'll be real email." |
| 0:30–1:00 | On `/app`, click the **Bedroom** card. On `/app/new`, tap upload, pick a committed JPG, then pick **Scandinavian**. Click **Generate draft**. | "Four room types, six styles — the index is different for each. This upload uses CLIP retrieval to ground the first draft against our 104-image library." |
| 1:00–2:00 | Wait for draft to appear. Point to the right rail: reference thumbnails with similarity scores. | "These are the references the model saw. Every generation is traceable back to its library grounding — that's how we keep brand voice consistent across a studio's projects." |
| 2:00–3:30 | Chat edit: "change the bed to rattan". Wait. Then: "warmer evening light". Wait. Tap the second-latest revision thumbnail. | "This is the core loop. Designers speak, the canvas updates, and every step is non-destructive — every revision stays in the stack. We're back two edits in a single tap." |
| 3:30–4:30 | Click **Commit**. Wait for the commit render. | "Commit re-renders at higher fidelity. A/B-configurable: today we're on Gemini 2.5 Flash for iteration and Pro for commit. The backend swaps models without a frontend change." |
| 4:30–5:00 | Click **Export** → **Download PNG**. | "PNG out, full resolution, drops straight into the studio's presentation deck. That's the workflow: upload, converse, commit, ship." |

## iPad addendum (optional 60s)

- Mirror to iPad. Repeat steps 0:30–3:30.
- Show the bottom shelf: "Edit, Refs, Commit, Export — every action is one tap from the canvas, nothing scrolls off-screen."
- Emphasize the same codebase serves both viewports.

## Fallback

If the live backend is slow or down, play `frontend/tests/fallback.mp4` (pre-recorded capture of the full desktop + iPad flow).

## Closing line

> "Ten seconds to a draft, one sentence to an edit, three credits to a commit. That's the studio workflow we wanted and couldn't buy — so we built it."
