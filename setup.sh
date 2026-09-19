#!/usr/bin/env zsh
set -euo pipefail

script_dir=${0:A:h}

sudo pacman -S --needed bluez bluez-utils python python-pip python-gobject python-dbus gst-plugin-pipewire

# --system-site-packages : le venv doit voir dbus/gi installes par pacman, hors pip
[[ -d "$script_dir/.venv" ]] || python3 -m venv --system-site-packages "$script_dir/.venv"
"$script_dir/.venv/bin/python" -m pip install --upgrade pip
"$script_dir/.venv/bin/python" -m pip install bleak

print "Installation terminee. Utilisez $script_dir/.venv/bin/python pour les scripts du projet."

