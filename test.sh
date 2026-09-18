#!/usr/bin/env zsh
set -euo pipefail

mac="AA:BB:CC:DD:EE:FF"
color="red"
brightness=100 # Max=100

script_dir=${0:A:h}
exec "$script_dir/.venv/bin/python" "$script_dir/govee_control.py" "$mac" color \
  --color "$color" --brightness "$brightness"