#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="channels"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "=== Meshtastic AI Agent Network — Pi 5 Setup ==="

# System dependencies
echo "[1/5] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-pip python3-venv

# Serial port permissions
echo "[2/5] Adding $USER to dialout group for serial access..."
sudo usermod -aG dialout "$USER"

# Python venv
echo "[3/5] Creating virtual environment..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q

# API key
echo "[4/5] Configuring environment..."
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    read -rp "Enter your ANTHROPIC_API_KEY: " api_key
    echo "ANTHROPIC_API_KEY=$api_key" > "$SCRIPT_DIR/.env"
    echo "  Saved to $SCRIPT_DIR/.env"
else
    echo "  .env already exists, skipping."
fi

# systemd service
echo "[5/5] Creating systemd service..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=Meshtastic AI Agent Network
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
EnvironmentFile=$SCRIPT_DIR/.env
ExecStart=$VENV_DIR/bin/python $SCRIPT_DIR/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service

echo ""
echo "=== Setup complete ==="
echo "Start the service:  sudo systemctl start ${SERVICE_NAME}"
echo "View logs:          journalctl -u ${SERVICE_NAME} -f"
echo "NOTE: Log out and back in for serial (dialout) group to take effect."
