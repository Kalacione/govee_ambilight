#!/usr/bin/env zsh
set -euo pipefail

script_dir=${0:A:h}

sudo pacman -S --needed bluez bluez-utils python python-pip

python3 -m venv "$script_dir/.venv"
"$script_dir/.venv/bin/python" -m pip install --upgrade pip
"$script_dir/.venv/bin/python" -m pip install govee_H613_BTcontroller

print "Installation terminee. Utilisez $script_dir/.venv/bin/python pour les scripts du projet."

