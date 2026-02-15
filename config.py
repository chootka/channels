import os

# Serial port — set to None for auto-detection
SERIAL_PORT = os.environ.get("MESHTASTIC_SERIAL_PORT", None)

# Claude API
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_MAX_TOKENS = 128

# Rate limiting — per-sender cooldown in seconds
RATE_LIMIT_SECONDS = int(os.environ.get("RATE_LIMIT_SECONDS", "10"))

# Message constraints
MAX_MESSAGE_BYTES = 220

# Logging
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "interactions.jsonl")
RESIDUE_MEMORY_FILE = os.path.join(LOG_DIR, "residue_memory.json")

# Channel config
CHANNELS_FILE = os.path.join(os.path.dirname(__file__), "channels.yaml")
