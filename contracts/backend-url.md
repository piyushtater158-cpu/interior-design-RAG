# Backend URL

## Dev (local)

```
http://localhost:8000
```

Run with:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## Staging / Production

**Not deployed.** MVP runs locally only — no Railway / Render / Fly. The A/B harness and frontend both target `http://localhost:8000`.

## BPA GPU endpoint

Separate from the backend URL. When the BPA-provisioned GPU instance is online, the backend calls it internally through the `local_gpu` adapter. Record the URL here once assigned:

```
LOCAL_GPU_URL = <not yet provisioned>
```

Update this file when the GPU is wired in.

## Health check

```bash
curl http://localhost:8000/health
# → { "status": "ok", "backend": "interior-design-assistant" }
```

## Useful entrypoints

| Path | Purpose |
|---|---|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc UI |
| `/openapi.json` | Machine-readable spec |
| `/data/uploads/<user>/<id>.png` | User-uploaded room photo |
| `/data/outputs/<user>/<id>.png` | Generated image |
