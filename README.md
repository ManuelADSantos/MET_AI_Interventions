# AI Study Platform

## Quick Start

### Prerequisites

- **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
  - Click Download Docker Desktop -> choose installer depending on your OS and processor
  - (Windows laptops most commonly have AMD or Intel processors -> choose the AMD64 installer)

### Setup

1. **Clone or download this repository**

   - Navigate to your preferred command prompt location
   - Find the repository url from this git repo, click green "code" button -> choose "https" -> copy the url 

   ```bash
   git clone <repository-url> 
   cd RMEP_studyProject_InteractiveAI
   ```
   - Alternatively download as zip and unzip the project

2. **Set up config and data files**
   - Run the following in your terminal:
   ```bash
   # Mac / Linux
   cp study.config.example.yml study.config.yml
   ```
   - OR create a file "study.config.yml" in the root of the repository and copy "study.config.example.yml" to it manually. Then:
   - Open `study.config.yml` in any text editor
   - Add your OpenAI API key 
   - Customize other settings as needed (see Configuration section below)

3. **Start the application**
   - Open Docker Desktop app on your computer
   - Navigate to this project's root in command prompt and run:
     
   ```bash
   docker compose up --force-recreate
   ```

4. **Access the study**
   - After the app is up and running, open your browser to http://localhost:5173
   - The study interface will load automatically

5. **Stop the application**
   - Press `Ctrl+C` in the terminal where docker-compose is running
   - Or run: `docker compose down -v --rmi local`

## Customizing Your Study

All customization is done by editing files on your computer. Changes take effect immediately (hot-reload) without rebuilding Docker containers.

| What to Change | File to Edit | Notes |
|----------------|--------------|-------|
| Survey questions & instructions | `customizations/tasks/ai_tasks.md` or `no-ai_tasks.md` | Uses taskParser markdown format (see below) |
| Study info / consent page | `customizations/tasks/*_studyinfo_example.md` | First page participants see |
| Correct answers for scoring | `customizations/correct_answers.py` | Python list of correct answers |
| GPT model (gpt-4o, etc.) | `study.config.yml` → `gpt_model` | Change which OpenAI model to use |
| ChatGPT system prompt | `study.config.yml` → `system_prompt` | Defines ChatGPT behavior |
| Experimental condition | `study.config.yml` → `condition` | Switch between 'ai' and 'no-ai' |
| Which pages show chat | `study.config.yml` → `chat_enabled_from/until_page` | Control chat availability |
| Attention check settings | `study.config.yml` → `attention_check_*` | Configure attention checks |
| Completion code/URL | `study.config.yml` → `completion_code/url` | For Prolific or other platforms |
| UI components (advanced) | `interface-frontend/src/components/` | React components with hot-reload |

### Task File Format

Task files use a markdown-based format. See `customizations/tasks/ai_tasks.md` for a full working example.

```markdown
# Page Title

> Paragraph text shown to the participant.
> Use > for all displayed text.

> Pick one:

    $option; Choice A; Choice B; Choice C

> Rate on a scale:

    $slider; 0; 100; Low label; High label

> Put visible task content and context in tabs:

:::tab Exercise
> Exercise text here.
:::

:::tab Context
> Context text here.
:::

> Add text copied by the tab copy button:

:::copy
Text to copy into the AI chat.
:::

> How much do you agree?

    $likert; 1; 7; Strongly disagree; Strongly agree

> How many?

    $number

> Describe your experience:

    $text

> Any additional comments?

    $textarea

# Next Page

> Content for the next page starts here.

%% RANDOMIZE

# Randomized Page 1

> This page and the ones below will appear in random order.

# Randomized Page 2

> Until the closing %% marker.

%%
```

**Key syntax:**
- `#` starts a new page (with optional title)
- `##` creates a section heading within a page
- `> text` displays paragraph text to the participant
- `$option; A; B; C` creates radio buttons (semicolon-separated choices)
- `$slider; min; max; lowLabel; highLabel` creates a slider
- `$likert; min; max; lowLabel; highLabel` creates a Likert scale
- `$number` creates a number input
- `$text` creates a single-line text input
- `$textarea` creates a multi-line text area
- `:::tab Title` ... `:::` creates a tab on the current page
- `:::copy` ... `:::` adds copy-button text without displaying it as page content
- `%% RANDOMIZE` ... `%%` randomizes the pages inside the block
- `%% SECTION` ... `%%` marks a block as a section but keeps its page order
- A standalone `%% RANDOMIZE_SECTIONS` line anywhere in the file shuffles all marked
  sections amongst themselves (unmarked content, e.g. an intro, stays in place)
- Question inputs must be indented with 4 spaces

## Configuration Reference

### study.config.yml

```yaml
# API Settings
openai_api_key: sk-YOUR_KEY_HERE  # Required: Your OpenAI API key
gpt_model: gpt-4-turbo            # Model to use
base_url: https://api.openai.com/v1    # Optional: Custom API base URL

# Study Settings
condition: ai                      # 'ai' or 'no-ai'
randomize_tasks: true              # Shuffle tasks within sections
system_prompt: You are a helpful logical reasoning assistant          # system prompt behavior instructions

# Chat Availability
chat_enabled_from_page: 1          # First page with chat (0-indexed)
chat_enabled_until_page: 99        # Last page with chat
allow_image_attachments: false     # Enable image uploads
require_ai_prompt: true            # Require one AI prompt before continuing
copy_button_pages: 1-99            # Pages where tabs show the copy button
copy_button_template: "{copyText}" # Copy-button template text

# Attention Check
attention_check_page: 1            # Page number (-1 to disable)
attention_check_answers: Logical reasoning,The best choice  # Correct answers

# Development
dev_mode: true                     # Skip participant ID validation

# Completion
completion_code: COMPLETE          # Code shown at end
completion_url: ""                 # Redirect URL (optional)

# Data export
export_token: ""                   # Set a secret to enable GET /export?token=<secret>
```

## Viewing Collected Data

Participant data is saved to Postgres (the `db` container). Each record includes:

- `participantId`: Unique participant identifier
- `condition`: Which condition they were in ('ai' or 'no-ai')
- `tasks`: All their survey responses
- `messages`: Chat conversation history (if applicable)
- `correctAnswers`, `totalQuestions`, `answerResults`: Scoring details
- `savedAt`: Timestamp of submission

### Exporting Data

Set `export_token` in `study.config.yml` (or the `EXPORT_TOKEN` env var on Railway), then:

```bash
curl "http://localhost:5001/export?token=YOUR_TOKEN" > study_data.json
```

Or query Postgres directly:

```bash
docker compose exec db psql -U study -c "SELECT data FROM participants"
```

The exported JSON can be analyzed with pandas (`pd.read_json`), R (`jsonlite`), or imported into Excel.

## Troubleshooting

### "Docker is not running"
- Open Docker Desktop and wait for it to start
- On Windows: Ensure WSL 2 is installed and enabled in Docker Desktop settings

### "Port 5173 (or 5001) is already in use"
- Another application or a previous Docker session is using this port
- Find and kill the process occupying the port:
  ```bash
  # Mac / Linux
  lsof -i :5001
  kill -9 <PID>

  # Windows (Command Prompt / PowerShell, run as Administrator)
  netstat -ano | findstr :5001
  taskkill /PID <PID> /F
  ```
- Or stop any running Docker containers first: `docker-compose down`

### "API key is not set"
- Open `study.config.yml` and set your OpenAI API key
- Make sure you've saved the file after editing

### Changes not appearing
- **Frontend source** (`interface-frontend/src/`): Hot-reloads instantly via Vite HMR — no rebuild needed.
- **Task files** (`customizations/tasks/`): Also hot-reloaded (mounted into the container).
- **`study.config.yml`**: Requires a restart (`docker-compose down && docker-compose up`).
- **`package.json` or `Dockerfile` changes**: Require a rebuild (`docker-compose up --build`).

### "Cannot connect to backend" or "Failed to save data"
- Check that both containers are running: `docker-compose ps`
- Backend should be at http://localhost:5001
- Frontend should be at http://localhost:5173
- If accessing from another device on the network, open port 5001 in Windows Firewall (run as Administrator):
  ```powershell
  netsh advfirewall firewall add rule name="AI Study Backend" dir=in action=allow protocol=TCP localport=5001
  ```

### OpenAI API errors
- Check your API key is correct in `study.config.yml`
- Check the model name is correct (e.g., 'gpt-4-turbo')

## Architecture

Three containers, orchestrated by `docker-compose.yml`:

| Container | Role |
|-----------|------|
| `frontend` | React + Vite study interface (port 5173) |
| `backend` | Flask API: chat proxy, scoring, data persistence (port 5001) |
| `db` | Postgres — all participant data |

## Deploying to Railway

See [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) for full setup instructions.

## Simulating Runs (Mock Data)

Populate Postgres with mock participant data for testing:

```bash
docker compose exec backend python /tests/simulate_runs.py              # 10 runs, mixed conditions
docker compose exec backend python /tests/simulate_runs.py --runs 20    # 20 runs
docker compose exec backend python /tests/simulate_runs.py --condition ai  # ai-only
```

View results in DataGrip (`localhost:5432`, user/pass/db: `study`).

Clean up: `docker compose exec db psql -U study -c "DELETE FROM participants WHERE participant_id LIKE '__sim_%'"`

## Tests

See [tests/README.md](tests/README.md) — endpoint tests, task parser tests, and a
concurrency stress test (`python3 tests/stress_test.py --users 100`, stdlib only).

## Project Structure

```
AI_study/
├── study.config.example.yml      # Config template (copy to study.config.yml)
├── study.config.yml              # Your configuration (created during setup, gitignored)
├── docker-compose.yml            # Docker orchestration (frontend, backend, db)
├── customizations/               # Student workspace for editing
│   ├── tasks/                    # Task + study info markdown files
│   └── correct_answers.py        # Answer key for scoring
├── tests/                        # Endpoint, parser and stress tests
├── interface-backend/            # Flask backend
│   ├── Dockerfile
│   ├── app.py
│   ├── db.py                     # Postgres persistence
│   ├── chat_helpers.py
│   ├── config_loader.py
│   └── requirements.txt
└── interface-frontend/           # React + Vite frontend
    ├── Dockerfile
    ├── entrypoint.sh
    ├── package.json
    ├── vite.config.js
    └── src/
```

## Security Notes

- **Never commit `study.config.yml` to git** - it contains your API key
- The `.gitignore` file is configured to prevent accidental commits
- Keep your OpenAI API key secret
- For production deployment, use environment variables instead of the config file

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review the configuration reference
3. Check Docker Desktop is running and up-to-date
4. Verify your OpenAI API key is valid and has credits
