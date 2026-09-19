#!/usr/bin/env zsh
set -euo pipefail

script_dir=${0:A:h}

# le venv doit voir les bindings systeme dbus/gi installes hors pip
[[ -d "$script_dir/.venv" ]] || python3 -m venv --system-site-packages "$script_dir/.venv"
#"$script_dir/.venv/bin/python" "$script_dir/ambilight.py" AA:BB:CC:DD:EE:FF --invert-lr --profile fast
"$script_dir/.venv/bin/python" "$script_dir/ambilight.py" AA:BB:CC:DD:EE:FF --invert-lr
