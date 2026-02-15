#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo "=== Meshtastic AI Agent Network — macOS Setup ==="

echo "[1/2] Creating virtual environment..."
/usr/local/bin/python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q

echo "[2/2] Configuring environment..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    read -rp "Enter your ANTHROPIC_API_KEY: " api_key
    echo "ANTHROPIC_API_KEY=$api_key" > "$PROJECT_DIR/.env"
    echo "  Saved to $PROJECT_DIR/.env"
else
    echo "  .env already exists, skipping."
fi

echo ""
echo "=== Setup complete ==="
echo "Run with:"
echo "  source $VENV_DIR/bin/activate"
echo "  source $PROJECT_DIR/.env && export ANTHROPIC_API_KEY"
echo "  python $PROJECT_DIR/main.py"
