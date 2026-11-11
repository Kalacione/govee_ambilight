#!/usr/bin/env zsh
set -euo pipefail

script_dir=${0:A:h}
source "$script_dir/.env"

# le venv doit voir les bindings systeme dbus/gi installes hors pip
[[ -d "$script_dir/.venv" ]] || python3 -m venv --system-site-packages "$script_dir/.venv"
# -u : logs immediats dans le journal systemd
exec "$script_dir/.venv/bin/python" -u "$script_dir/ambilight.py" "$GOVEE_MAC" --profile fast --crop-y 13
