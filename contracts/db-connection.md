# Database Connection Configuration

## Required Environment Variables

The backend must set these environment variables to connect to the database:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | **Yes** | Full Postgres connection string |
| `SUPABASE_URL` | **Yes** | Supabase project URL (for Storage API) |
| `SUPABASE_SERVICE_KEY` | **Yes** | Supabase service role key (for Storage API) |

## Connection String Format

```
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
```

### Supabase (current setup)

```
DATABASE_URL=postgresql://postgres:<url-encoded-password>@db.<project-ref>.supabase.co:6543/postgres
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_KEY=<service-role-key>
```

**Notes:**
- Use port **6543** (connection pooler) — port 5432 (direct) may time out on some networks
- URL-encode special characters in the password (e.g., `@` → `%40`, `[` → `%5B`)
- The `SUPABASE_SERVICE_KEY` is the **service_role** key (not the anon key) — it bypasses RLS

## Network Considerations

- Force **IPv4** DNS resolution if IPv6 connections to Supabase time out
- Connection pooling is handled by Supabase's PgBouncer on port 6543
- Free tier: connections may be paused after 7 days of inactivity

## Supabase Storage

Images are stored in a public bucket named `reference-images`:

```
SUPABASE_URL + /storage/v1/object/public/reference-images/<path>
```

The `source_url` column in `reference_images` contains the full public URL.

## Python Connection Example

```python
import os
import socket
import psycopg2
from dotenv import load_dotenv

load_dotenv(".env")

# Force IPv4 if needed
_orig = socket.getaddrinfo
socket.getaddrinfo = lambda *a, **kw: _orig(a[0], a[1], socket.AF_INET, *a[3:], **kw)

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
```
