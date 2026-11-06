#!/usr/bin/env zsh
set -euo pipefail

color="#00A060"
brightness=50 # Max=100

script_dir=${0:A:h}
source "$script_dir/.env"
exec "$script_dir/.venv/bin/python" "$script_dir/govee_control.py" "$GOVEE_MAC" color \
  --color "$color" --brightness "$brightness"