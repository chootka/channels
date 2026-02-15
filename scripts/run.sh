#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

source "$SCRIPT_DIR/.venv/bin/activate"
set -a
source "$SCRIPT_DIR/.env"
set +a

python "$SCRIPT_DIR/main.py"
