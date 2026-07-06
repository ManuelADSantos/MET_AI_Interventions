# Railway Deployment

## 1. Create project

New project on [railway.app](https://railway.app) from your GitHub repo.

## 2. Add plugins

- **Postgres** — provides `DATABASE_URL`

## 3. Add two services

Both use root directory `/` (build context is the repo root).

### Backend

- Dockerfile path: `interface-backend/Dockerfile`
- Health check path: `/health`

| Variable | Value |
|---|---|
| `OPENAI_API_KEY` | Your API key |
| `GPT_MODEL` | e.g. `gpt-4-turbo` |
| `REASONING_EFFORT` | Optional: `none`, `low`, `medium`, `high`, or `xhigh` |
| `BASE_URL` | e.g. `https://api.openai.com/v1` |
| `EXPORT_TOKEN` | Secret string for data export |
| `COMPLETION_CODE` | e.g. `COMPLETE` |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `DB_POOL_MAX` | `10` |
| `WEB_CONCURRENCY` | `2` |
| `WEB_THREADS` | `64` |
| `WEB_TIMEOUT` | `180` |

`PORT` and `RAILWAY_ENVIRONMENT` are set automatically by Railway.

<details><summary>Raw editor JSON</summary>

```json
{
  "OPENAI_API_KEY": "sk-YOUR_KEY_HERE",
  "GPT_MODEL": "gpt-5.4-mini",
  "REASONING_EFFORT": "none",
  "BASE_URL": "https://api.openai.com/v1",
  "EXPORT_TOKEN": "",
  "COMPLETION_CODE": "COMPLETE",
  "COMPLETION_URL": "",
  "DATABASE_URL": "${{Postgres.DATABASE_URL}}",
  "DB_POOL_MAX": "10",
  "WEB_CONCURRENCY": "2",
  "WEB_THREADS": "64",
  "WEB_TIMEOUT": "180"
}
```

</details>

### Frontend

- Dockerfile path: `interface-frontend/Dockerfile`

| Variable | Value |
|---|---|
| `VITE_PROXY_URL` | Backend's public URL (e.g. `https://your-backend.up.railway.app`) |
| `VITE_PCTP_CONDITION` | `ai` or `no-ai` |
| `VITE_CHAT_ENABLED_BEGIN` | `1` |
| `VITE_CHAT_ENABLED_END` | `99` |
| `VITE_ALLOW_IMAGES` | `false` |
| `VITE_DEV_MODE` | `false` |
| `VITE_SYSTEM_PROMPT` | Your system prompt |
| `VITE_ATTN_CHECK_PAGE` | Page number or `-1` to disable |
| `VITE_ATTN_CHECK_RES` | Comma-separated correct answers |
| `VITE_COPY_BUTTON_PAGES` | `1-99` |
| `VITE_COPY_BUTTON_TEMPLATE` | `{copyText}` |
| `VITE_RANDOMIZE_TASKS` | `true` |
| `VITE_REQUIRE_AI_PROMPT` | `true` |

<details><summary>Raw editor JSON</summary>

```json
{
  "VITE_PROXY_URL": "https://your-backend.up.railway.app",
  "VITE_PCTP_CONDITION": "ai",
  "VITE_CHAT_ENABLED_BEGIN": "1",
  "VITE_CHAT_ENABLED_END": "99",
  "VITE_ALLOW_IMAGES": "false",
  "VITE_DEV_MODE": "false",
  "VITE_SYSTEM_PROMPT": "You are a helpful logical reasoning assistant",
  "VITE_ATTN_CHECK_PAGE": "1",
  "VITE_ATTN_CHECK_RES": "Planning and Organizing,C",
  "VITE_COPY_BUTTON_PAGES": "1-99",
  "VITE_COPY_BUTTON_TEMPLATE": "{copyText}",
  "VITE_RANDOMIZE_TASKS": "true",
  "VITE_REQUIRE_AI_PROMPT": "true",
  "VITE_REQUIRE_AI_PROMPT_PAGES": "3-99"
}
```

</details>

The entrypoint detects `$RAILWAY_ENVIRONMENT` and builds a production bundle automatically. No `study.config.yml` needed.

## 4. Deploy

Push to your branch. Railway builds and deploys both services.

## Exporting data

```bash
curl "https://your-backend.up.railway.app/export?token=YOUR_TOKEN" > study_data.json
```

## Gotcha

`VITE_*` vars are baked in at build time (Vite inlines them). Changing one triggers a redeploy automatically on Railway. Backend env vars take effect on restart without a rebuild.
