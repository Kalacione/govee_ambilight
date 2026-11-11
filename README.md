# govee_ambilight

Ambilight for Govee Bluetooth lights on Linux. It matches the lights to the left and right halves of your screen.

Tested on a Govee H6056 (2 bars) with Manjaro, KDE Plasma on Wayland and an NVIDIA GPU. Other Govee models may use different commands.

## Install

```sh
git clone https://github.com/Kalacione/govee_ambilight
cd govee_ambilight
./setup.sh
```

`setup.sh` uses pacman, installs the dependencies, creates `.env`, and adds an AmbiLight shortcut that starts with your KDE session.

Turn the lights on, close the Govee app on your phone, and find their address:

```sh
bluetoothctl scan on    # look for ihoment_H6056_XXXX
```

Put it in `.env`:

```sh
GOVEE_MAC=AA:BB:CC:DD:EE:FF
```

## Use

Log in to KDE, or run `./al.sh`. The first time, KDE asks which screen to capture. Your choice is remembered.

If the lights are off, it retries every 30 seconds, so you can turn them on at any time. The screen is only captured while they are connected.

If left and right are swapped, add `--invert-lr` in `al.sh`. For a lower update rate, replace `--profile fast` (10 Hz) with `--profile normal` (4 Hz).

`--crop-y 13` leaves the top and bottom 13% of the screen out of the colour calculation, so the black bars of a 2.39:1 film do not darken the lights. Set it to `0` to use the whole screen. For brighter or dimmer lights overall, scale the three `CHANNEL_GAIN` values in `ambilight.py`.

```sh
journalctl --user -u 'app-AmbiLight@autostart' -f    # logs
systemctl --user stop 'app-AmbiLight@autostart'      # stop for this session
rm ~/.config/autostart/AmbiLight.desktop             # disable autostart
```

Design notes, in French, are in [doc/design.md](doc/design.md).

## Trademarks

This is a personal project, not affiliated with or endorsed by Govee or Philips. Govee and Ambilight are trademarks of their respective owners.

## License

[WTFPL](LICENSE)
