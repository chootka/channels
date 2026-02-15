#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "=== Meshtastic AI Agent Network — macOS Setup ==="

echo "[1/2] Creating virtual environment..."
/usr/local/bin/python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q

echo "[2/2] Configuring environment..."
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    read -rp "Enter your ANTHROPIC_API_KEY: " api_key
    echo "ANTHROPIC_API_KEY=$api_key" > "$SCRIPT_DIR/.env"
    echo "  Saved to $SCRIPT_DIR/.env"
else
    echo "  .env already exists, skipping."
fi

echo ""
echo "=== Setup complete ==="
echo "Run with:"
echo "  source $VENV_DIR/bin/activate"
echo "  source $SCRIPT_DIR/.env && export ANTHROPIC_API_KEY"
echo "  python $SCRIPT_DIR/main.py"
