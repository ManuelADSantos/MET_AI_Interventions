# Railway Deployment — Step by Step

## Prerequisites

- A [Railway](https://railway.app) account (free tier works for testing)
- Your repo pushed to GitHub
- An OpenAI API key

---

## Step 1: Create a Railway Project

1. Go to [railway.app/new](https://railway.app/new)
2. Click **"Deploy from GitHub repo"**
3. Select your repository
4. Railway will detect the repo — **don't deploy yet**, click the project name to enter the project dashboard

---

## Step 2: Add a Postgres Database

1. In the project dashboard, click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway provisions a Postgres instance and exposes `DATABASE_URL` as a reference variable (`${{Postgres.DATABASE_URL}}`)
3. No configuration needed — the backend picks it up automatically

---

## Step 3: Create the Backend Service

1. Click **"+ New"** → **"GitHub Repo"** → select the same repository
2. Railway creates a new service. Click on it to open its settings.

### Settings tab

- **Source** → Root Directory: leave as `/` (both Dockerfiles use repo root as build context)
- **Build** → Builder: should auto-detect the Dockerfile. If not, set to `Dockerfile` and set the Dockerfile path to `interface-backend/Dockerfile`

> If your repo has `railway.json` files (this one does), Railway reads them automatically. The backend's `interface-backend/railway.json` sets the Dockerfile path and health check for you.

### Variables tab

Click **"Raw Editor"** and paste the following JSON, then fill in your values:

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

| Variable | What it does |
|---|---|
| `OPENAI_API_KEY` | **Required.** Your OpenAI API key |
| `GPT_MODEL` | Which model to use (e.g. `gpt-5.4-mini`, `gpt-4-turbo`) |
| `REASONING_EFFORT` | `none`, `low`, `medium`, `high`, or `xhigh`. Use `none` to disable chain-of-thought |
| `BASE_URL` | API endpoint. Default `https://api.openai.com/v1`. Change for Azure or compatible APIs |
| `EXPORT_TOKEN` | Secret string to protect the `/export` endpoint. Leave empty to disable export |
| `COMPLETION_CODE` | Code shown to participants at the end (e.g. Prolific completion code) |
| `COMPLETION_URL` | Optional redirect URL shown on the completion page |
| `DATABASE_URL` | **Use exactly** `${{Postgres.DATABASE_URL}}` — Railway resolves this to the Postgres connection string |
| `DB_POOL_MAX` | Max database connections per worker. `10` is fine for most studies |
| `WEB_CONCURRENCY` | Number of Gunicorn worker processes. `2` is fine for most studies |
| `WEB_THREADS` | Threads per worker. `64` handles concurrent chat streams |
| `WEB_TIMEOUT` | Request timeout in seconds. `180` accommodates slow model responses |

`PORT` and `RAILWAY_ENVIRONMENT` are injected automatically by Railway — do not set them.

### Networking tab

1. Click **"Generate Domain"** to get a public URL (e.g. `https://your-backend-abc123.up.railway.app`)
2. **Copy this URL** — you need it for the frontend's `VITE_PROXY_URL`

---

## Step 4: Create the Frontend Service

1. Click **"+ New"** → **"GitHub Repo"** → select the same repository again
2. Open the new service's settings.

### Settings tab

Same as backend — root directory `/`, Dockerfile auto-detected from `interface-frontend/railway.json`.

### Variables tab

Click **"Raw Editor"** and paste:

```json
{
  "VITE_PROXY_URL": "https://your-backend-abc123.up.railway.app",
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

| Variable | What it does |
|---|---|
| `VITE_PROXY_URL` | **Required.** The backend's public URL from Step 3. Must include `https://` |
| `VITE_PCTP_CONDITION` | `ai` (shows chat panel) or `no-ai` (questionnaire only). Can also be overridden per-participant via URL `?condition=no_ai` |
| `VITE_CHAT_ENABLED_BEGIN` | First page (0-indexed) where the chat is available |
| `VITE_CHAT_ENABLED_END` | Last page where the chat is available |
| `VITE_ALLOW_IMAGES` | `true` or `false` — allow image attachments in chat |
| `VITE_DEV_MODE` | `false` for production. `true` skips Prolific ID validation |
| `VITE_SYSTEM_PROMPT` | The system prompt that defines AI behavior |
| `VITE_ATTN_CHECK_PAGE` | Page number for the attention check (`-1` to disable) |
| `VITE_ATTN_CHECK_RES` | Comma-separated correct answers for the attention check |
| `VITE_COPY_BUTTON_PAGES` | Page range where tabs show a copy-to-clipboard button (e.g. `1-99` or `2,4,6`) |
| `VITE_COPY_BUTTON_TEMPLATE` | Template for copied text. Placeholders: `{copyText}`, `{title}`, `{tabTitle}`, `{tabText}`, `{exerciseText}`, `{allTabsText}`, `{allCopyText}`, `{questionText}`, `{optionsText}` |
| `VITE_RANDOMIZE_TASKS` | `true` or `false` — shuffle task order |
| `VITE_REQUIRE_AI_PROMPT` | `true` to require participants to prompt the AI at least once per question |
| `VITE_REQUIRE_AI_PROMPT_PAGES` | Page range where the AI prompt requirement applies (e.g. `3-99`) |

### Networking tab

1. Click **"Generate Domain"** for a public URL
2. This is the URL you share with participants (directly or via Prolific)

---

## Step 5: Deploy

1. Click **"Deploy"** on both services (or push to your branch — Railway auto-deploys on push)
2. Watch the build logs. Both services take 1–3 minutes to build.
3. The backend shows `Listening at: http://0.0.0.0:<port>` when ready
4. The frontend shows `➜  Local: http://0.0.0.0:<port>` when ready

### Verify

- Backend health: visit `https://your-backend.up.railway.app/health` — should return `{"status": "ok"}`
- Frontend: visit your frontend URL — the study interface should load

---

## Step 6: Prolific Integration

Share the frontend URL with Prolific query parameters:

```
https://your-frontend.up.railway.app/?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}
```

To run multiple conditions, create separate Railway projects (or separate frontend services with different `VITE_PCTP_CONDITION`) and distribute the URLs accordingly. You can also override the condition per-participant via the URL:

```
https://your-frontend.up.railway.app/?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}&condition=no_ai
```

---

## Exporting Data

Set `EXPORT_TOKEN` on the backend to a secret string, then:

```bash
curl "https://your-backend.up.railway.app/export?token=YOUR_TOKEN" > study_data.json
```

Or connect to the Railway Postgres directly using the credentials from the Postgres service's **Connect** tab.

---

## Troubleshooting

### "Application failed to respond"

Check the **deploy logs** (click the service → Deployments → click the latest deployment). Common causes:

1. **Missing `DATABASE_URL`** — the backend crashes at startup if it can't connect to Postgres. Make sure `${{Postgres.DATABASE_URL}}` is set and the Postgres service is running.
2. **Missing `OPENAI_API_KEY`** — the backend exits with `sys.exit(1)` if no API key is found.
3. **Frontend build failed** — check the build logs for npm errors. The frontend must complete `npm run build` before it can serve.

### "Failed to fetch" or CORS errors in the browser

- `VITE_PROXY_URL` is wrong or missing. It must be the backend's **public Railway URL** (not `localhost`).
- The backend service doesn't have a public domain generated yet.

### Environment variable changes don't take effect (frontend)

`VITE_*` variables are baked in at build time by Vite. Changing one triggers a redeploy automatically on Railway, which rebuilds the frontend. Backend env vars take effect on restart without a rebuild.

### Database is empty after redeployment

Railway Postgres persists data across deploys by default. If you deleted and re-created the Postgres service, data is lost. The schema (`participants` table) is auto-created on backend startup.
