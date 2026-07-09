import functools
import os
import yaml
import sys

@functools.cache
def load_config():
    """
    Load and validate the study configuration from study.config.yml
    Returns a dictionary with all configuration values.
    Exits if the config file is missing or if the API key is not set.
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'study.config.yml')

    if not os.path.exists(config_path):
        # No config file (e.g. Railway) — fall back to environment variables
        env_keys = ('openai_api_key', 'gpt_model', 'reasoning_effort', 'base_url', 'completion_code',
                    'completion_url', 'export_token')
        config = {k: os.environ[k.upper()] for k in env_keys if os.environ.get(k.upper())}
        if config.get('openai_api_key'):
            return config
        print(f"ERROR: Configuration file not found at {config_path}")
        print("Create study.config.yml in the project root, or set OPENAI_API_KEY etc. as environment variables.")
        sys.exit(1)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to parse study.config.yml: {e}")
        sys.exit(1)

    # Validate required fields
    if not config.get('openai_api_key') or config.get('openai_api_key') == 'sk-YOUR_API_KEY_HERE':
        print("ERROR: OpenAI API key not set in study.config.yml")
        print("Please edit study.config.yml and set your API key in the 'openai_api_key' field.")
        sys.exit(1)

    return config
