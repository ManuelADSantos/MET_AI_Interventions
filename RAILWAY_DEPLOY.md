# Railway Deployment

## 1. Create project

New project on [railway.app](https://railway.app) from your GitHub repo.

## 2. Add plugins

- **Postgres** — provides `DATABASE_URL`
- **Redis** — provides `REDIS_URL`

## 3. Add two services

Both use root directory `/` (build context is the repo root).

### Backend

- Dockerfile path: `interface-backend/Dockerfile`
- Health check path: `/health`

| Variable | Value |
|---|---|
| `OPENAI_API_KEY` | Your API key |
| `GPT_MODEL` | e.g. `gpt-4-turbo` |
| `BASE_URL` | e.g. `https://api.openai.com/v1` |
| `EXPORT_TOKEN` | Secret string for data export |
| `COMPLETION_CODE` | e.g. `COMPLETE` |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` |

`PORT` and `RAILWAY_ENVIRONMENT` are set automatically by Railway.

### Frontend

- Dockerfile path: `interface-frontend/Dockerfile`

| Variable | Value |
|---|---|
| `VITE_PROXY_URL` | Backend's public URL (e.g. `https://your-backend.up.railway.app`) |
| `VITE_PCTP_CONDITION` | `ai` or `no-ai` |
| `VITE_CHAT_ENABLED_BEGIN` | `1` |
| `VITE_CHAT_ENABLED_END` | `99` |
| `VITE_DEV_MODE` | `false` |
| `VITE_ATTN_CHECK_PAGE` | Page number or `-1` to disable |
| `VITE_ATTN_CHECK_RES` | Comma-separated correct answers |

The entrypoint detects `$RAILWAY_ENVIRONMENT` and builds a production bundle automatically. No `study.config.yml` needed.

## 4. Deploy

Push to your branch. Railway builds and deploys both services.

## Exporting data

```bash
curl "https://your-backend.up.railway.app/export?token=YOUR_TOKEN" > study_data.json
```

## Gotcha

`VITE_*` vars are baked in at build time (Vite inlines them). Changing one triggers a redeploy automatically on Railway. Backend env vars take effect on restart without a rebuild.
