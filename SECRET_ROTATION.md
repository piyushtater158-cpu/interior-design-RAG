# Secret rotation (required)

Several API keys and tokens were previously committed in this repository or stored in local `n8n/exec_*_full.json` dumps. **Removing them from the current tree does not revoke them.** Rotate every item below in the provider dashboard, then update `.env`, n8n Environment variables, and `mobile-app/config.js`.

## Rotate immediately

| Secret | Where to rotate |
|--------|-----------------|
| Supabase **service role** (`sb_secret_…`) | [Supabase](https://supabase.com/dashboard/project/uzghfpxboktnbcbbthns/settings/api) → reset service role key |
| Supabase **anon** JWT | Same page (anon key is public in clients but rotate if repo was public) |
| **OpenRouter** (`sk-or-v1-…`) | [OpenRouter](https://openrouter.ai/settings/keys) → revoke old key, create new |
| **Google AI Studio / Gemini** (`AIzaSy…`) | [Google AI Studio](https://aistudio.google.com/apikey) |
| **ADMIN_TOKEN** / `X-Admin-Token` | Generate a new random string; set in n8n env + callers |
| **JWT_SECRET** (if still used) | New random string in n8n env |
| **N8N_API_KEY** | n8n → Settings → API → regenerate |

## Git history

Old commits may still contain literal keys (`git log -S 'sk-or-v1-'`). To purge history you must use [git-filter-repo](https://github.com/newren/git-filter-repo) or BFG, then **force-push** — coordinate with anyone else using the repo.

## Repo hygiene (now enforced)

- `.env` and `mobile-app/config.js` are gitignored; use `.env.example` and `mobile-app/config.example.js`.
- `python n8n/scripts/fetch_all_workflows.py` exports live workflows with secrets redacted to `n8n/workflows/*.json`.
- Do not commit `n8n/*_full.json` execution dumps (they contain runtime secrets).
