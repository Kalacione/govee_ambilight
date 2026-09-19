#!/usr/bin/env python3
import argparse
import asyncio
import time

import dbus
import dbus.mainloop.glib
import gi
from bleak import BleakClient
from bleak.exc import BleakError

gi.require_version("GLib", "2.0")
gi.require_version("Gst", "1.0")
from gi.repository import Gst

from govee_control import CONTROL_CHARACTERISTIC, brightness_command, color_command, frame
from test_pipewire_capture import PORTAL_NAME, SESSION, make_pipeline, open_stream


PROFILES = {"normal": 4.0, "fast": 10.0}

# segments 0-5 = un bloc physique, 6-11 = l'autre (H6056 : 2 blocs, 1 seul appareil BLE)
MASK_LEFT = (0x3F, 0x00)
MASK_RIGHT = (0xC0, 0x0F)


async def send(client, payload):
    # la lampe peut se deconnecter brievement en cours de route ; bleak perd
    # alors son cache de services et refuse l'ecriture jusqu'a reconnexion
    try:
        await client.write_gatt_char(CONTROL_CHARACTERISTIC, payload, response=False)
    except BleakError:
        await client.connect()
        await client.write_gatt_char(CONTROL_CHARACTERISTIC, payload, response=False)


def analyze_side(rgb):
    pixels = len(rgb) // 3
    red = round(sum(rgb[0::3]) / pixels)
    green = round(sum(rgb[1::3]) / pixels)
    blue = round(sum(rgb[2::3]) / pixels)
    brightness = round(max(red, green, blue) * 100 / 255)
    return (red, green, blue), brightness


def analyze_left_right(sample, width):
    buffer = sample.get_buffer()
    success, mapped = buffer.map(Gst.MapFlags.READ)
    if not success:
        raise RuntimeError("Lecture du flux PipeWire impossible.")
    try:
        rgb = mapped.data
        row_bytes = width * 3
        half_bytes = (width // 2) * 3
        height = len(rgb) // row_bytes
        left = bytearray()
        right = bytearray()
        for row in range(height):
            start = row * row_bytes
            left += rgb[start : start + half_bytes]
            right += rgb[start + half_bytes : start + row_bytes]
    finally:
        buffer.unmap(mapped)
    return analyze_side(left), analyze_side(right)


def parse_args():
    parser = argparse.ArgumentParser(description="Ambilight Govee : capture ecran KDE -> couleur/luminosite BLE.")
    parser.add_argument("mac", help="Adresse MAC Bluetooth de la lampe")
    parser.add_argument("--profile", choices=PROFILES, default="normal")
    parser.add_argument("--width", type=int, default=160)
    parser.add_argument("--invert-lr", action="store_true", help="les 2 blocs sont physiquement inverses derriere l'ecran")
    args = parser.parse_args()
    if args.width < 1 or args.width % 4 != 0:
        parser.error("--width doit etre un multiple de 4 (evite le padding de ligne GStreamer)")
    return args


async def run(args):
    interval = 1 / PROFILES[args.profile]
    mask_left, mask_right = MASK_LEFT, MASK_RIGHT
    if args.invert_lr:
        mask_left, mask_right = mask_right, mask_left

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    Gst.init(None)
    bus = dbus.SessionBus()
    print("Choisissez l'ecran dans la boite de dialogue KDE.")
    session, node_id, fd = open_stream(bus)
    pipeline, sink = make_pipeline(fd, node_id, args.width)

    print(f"Connexion a {args.mac}...")
    client = BleakClient(args.mac)
    # une session precedente mal fermee (double Ctrl+C) laisse parfois BlueZ
    # "deja connecte" sans avoir resolu les services : on repart d'un etat propre
    await client.disconnect()
    await client.connect()
    try:
        await send(client, frame([0x33, 0x01, 0x01]))
        print(f"Ambilight actif, profil {args.profile} ({PROFILES[args.profile]:g} Hz). Ctrl+C pour arreter.")

        last_left = (None, None)
        last_right = (None, None)
        try:
            while True:
                started = time.monotonic()
                sample = sink.emit("try-pull-sample", Gst.SECOND)
                if sample is not None:
                    (color_left, brightness_left), (color_right, brightness_right) = analyze_left_right(sample, args.width)
                    if (color_left, brightness_left) != last_left:
                        await send(client, brightness_command(brightness_left, mask=mask_left))
                        await send(client, color_command(*color_left, mask=mask_left))
                        last_left = (color_left, brightness_left)
                    if (color_right, brightness_right) != last_right:
                        await send(client, brightness_command(brightness_right, mask=mask_right))
                        await send(client, color_command(*color_right, mask=mask_right))
                        last_right = (color_right, brightness_right)
                elapsed = time.monotonic() - started
                await asyncio.sleep(max(0, interval - elapsed))
        except KeyboardInterrupt:
            print("\nArret de l'ambilight...")
        finally:
            pipeline.set_state(Gst.State.NULL)
            dbus.Interface(bus.get_object(PORTAL_NAME, session), SESSION).Close()
    finally:
        await client.disconnect()
    print("Deconnecte.")


if __name__ == "__main__":
    try:
        asyncio.run(run(parse_args()))
    except KeyboardInterrupt:
        pass
