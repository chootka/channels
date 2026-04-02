import os
from dotenv import dotenv_values

_env = dotenv_values()

# Serial port — set to None for auto-detection
SERIAL_PORT = _env.get("MESHTASTIC_SERIAL_PORT", None)

# Claude API
ANTHROPIC_API_KEY = _env.get("ANTHROPIC_API_KEY", "")
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_MAX_TOKENS = 128

# LLM backend — set RUN_LOCAL_LLM=true to use Ollama instead of Claude API
RUN_LOCAL_LLM = _env.get("RUN_LOCAL_LLM", "false").lower() == "true"

# Rate limiting — per-sender cooldown in seconds
RATE_LIMIT_SECONDS = int(_env.get("RATE_LIMIT_SECONDS", "10"))

# Message constraints
MAX_MESSAGE_BYTES = 220

# Logging
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "interactions.jsonl")
RESIDUE_MEMORY_FILE = os.path.join(LOG_DIR, "residue_memory.json")
CONTROL_STATE_FILE = os.path.join(LOG_DIR, "control_state.json")

# Channel config
CHANNELS_FILE = os.path.join(os.path.dirname(__file__), _env.get("CHANNELS_FILE", "channels.yaml"))
