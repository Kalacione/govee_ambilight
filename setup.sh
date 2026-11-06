#!/usr/bin/env zsh
set -euo pipefail

script_dir=${0:A:h}

sudo pacman -S --needed bluez bluez-utils python python-pip python-gobject python-dbus gst-plugin-pipewire

# --system-site-packages : le venv doit voir dbus/gi installes par pacman, hors pip
[[ -d "$script_dir/.venv" ]] || python3 -m venv --system-site-packages "$script_dir/.venv"
"$script_dir/.venv/bin/python" -m pip install --upgrade pip
"$script_dir/.venv/bin/python" -m pip install bleak

[[ -f "$script_dir/.env" ]] || cp "$script_dir/.env.exemple" "$script_dir/.env"

# raccourci KDE, et meme fichier en autostart de session
cat > ~/.local/share/applications/AmbiLight.desktop <<DESKTOP
[Desktop Entry]
Type=Application
Name=AmbiLight
Exec=$script_dir/al.sh
Path=$script_dir
Terminal=false
DESKTOP
mkdir -p ~/.config/autostart
ln -sf ~/.local/share/applications/AmbiLight.desktop ~/.config/autostart/AmbiLight.desktop

print "Installation terminee. Renseignez GOVEE_MAC dans $script_dir/.env."

