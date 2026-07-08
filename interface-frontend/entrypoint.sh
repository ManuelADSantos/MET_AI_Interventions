#!/bin/sh

# Generate Vite .env from study.config.yml when mounted (local docker-compose).
# On Railway there is no config file: set VITE_* variables on the service instead.

CONFIG_FILE="/study.config.yml"

if [ -f "$CONFIG_FILE" ]; then
    echo "Generating .env file from study.config.yml..."

    cat > /app/.env << EOF
VITE_PROXY_URL=$(grep '^backend_url:' $CONFIG_FILE | sed 's/backend_url: *//;s/"//g;s/'\''//g;s/  *#.*//;s/ *$//')
VITE_CHAT_ENABLED_BEGIN=$(grep '^chat_enabled_from_page:' $CONFIG_FILE | sed 's/chat_enabled_from_page: *//;s/  *#.*//;s/ *$//')
VITE_CHAT_ENABLED_END=$(grep '^chat_enabled_until_page:' $CONFIG_FILE | sed 's/chat_enabled_until_page: *//;s/  *#.*//;s/ *$//')
VITE_ALLOW_IMAGES=$(grep '^allow_image_attachments:' $CONFIG_FILE | sed 's/allow_image_attachments: *//;s/  *#.*//;s/ *$//')
VITE_PCTP_CONDITION=$(grep '^condition:' $CONFIG_FILE | sed 's/condition: *//;s/"//g;s/'\''//g;s/  *#.*//;s/ *$//')
VITE_DEV_MODE=$(grep '^dev_mode:' $CONFIG_FILE | sed 's/dev_mode: *//;s/  *#.*//;s/ *$//')
VITE_SYSTEM_PROMPT=$(grep '^system_prompt:' $CONFIG_FILE | sed 's/system_prompt: *//;s/"//g;s/'\''//g;s/  *#.*//;s/ *$//')
VITE_COPY_BUTTON_PAGES=$(grep '^copy_button_pages:' $CONFIG_FILE | sed 's/copy_button_pages: *//;s/"//g;s/'\''//g;s/  *#.*//;s/ *$//')
VITE_COPY_BUTTON_TEMPLATE=$(grep '^copy_button_template:' $CONFIG_FILE | sed 's/copy_button_template: *//;s/"//g;s/'\''//g;s/  *#.*//;s/ *$//')
VITE_RANDOMIZE_TASKS=$(grep '^randomize_tasks:' $CONFIG_FILE | sed 's/randomize_tasks: *//;s/  *#.*//;s/ *$//')
VITE_REQUIRE_AI_PROMPT=$(grep '^require_ai_prompt:' $CONFIG_FILE | sed 's/require_ai_prompt: *//;s/  *#.*//;s/ *$//')
VITE_REQUIRE_AI_PROMPT_PAGES=$(grep '^require_ai_prompt_pages:' $CONFIG_FILE | sed 's/require_ai_prompt_pages: *//;s/"//g;s/'\''//g;s/  *#.*//;s/ *$//')
EOF

    echo ".env file generated successfully:"
    cat /app/.env
else
    echo "No study.config.yml found - using VITE_* environment variables as provided."
fi

PORT="${PORT:-5173}"

if [ -n "$RAILWAY_ENVIRONMENT" ]; then
    echo "Railway detected: building static bundle..."
    npm run build && exec npm run preview -- --host 0.0.0.0 --port "$PORT"
else
    echo "Starting Vite dev server..."
    exec npm run dev -- --host 0.0.0.0 --port "$PORT"
fi
