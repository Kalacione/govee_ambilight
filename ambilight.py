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

from govee_control import CONTROL_CHARACTERISTIC, color_command, frame
from test_pipewire_capture import PORTAL_NAME, SESSION, analyze, make_pipeline, open_stream


PROFILES = {"normal": 4.0, "fast": 10.0}


async def send(client, payload):
    # la lampe peut se deconnecter brievement en cours de route ; bleak perd
    # alors son cache de services et refuse l'ecriture jusqu'a reconnexion
    try:
        await client.write_gatt_char(CONTROL_CHARACTERISTIC, payload, response=False)
    except BleakError:
        await client.connect()
        await client.write_gatt_char(CONTROL_CHARACTERISTIC, payload, response=False)


def parse_args():
    parser = argparse.ArgumentParser(description="Ambilight Govee : capture ecran KDE -> couleur/luminosite BLE.")
    parser.add_argument("mac", help="Adresse MAC Bluetooth de la lampe")
    parser.add_argument("--profile", choices=PROFILES, default="normal")
    parser.add_argument("--width", type=int, default=160)
    args = parser.parse_args()
    if args.width < 1:
        parser.error("--width doit etre superieur ou egal a 1")
    return args


async def run(args):
    interval = 1 / PROFILES[args.profile]

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

        last_color = None
        last_brightness = None
        try:
            while True:
                started = time.monotonic()
                sample = sink.emit("try-pull-sample", Gst.SECOND)
                if sample is not None:
                    red, green, blue, brightness = analyze(sample)
                    color = (red, green, blue)
                    if color != last_color or brightness != last_brightness:
                        await send(client, frame([0x33, 0x04, brightness]))
                        await send(client, color_command(*color))
                        last_color, last_brightness = color, brightness
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
