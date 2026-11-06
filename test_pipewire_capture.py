#!/usr/bin/env python3
import argparse
import time
import uuid
from pathlib import Path

import dbus
import dbus.mainloop.glib
import gi

gi.require_version("GLib", "2.0")
gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst


PORTAL_NAME = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
SCREENCAST = "org.freedesktop.portal.ScreenCast"
REQUEST = "org.freedesktop.portal.Request"
SESSION = "org.freedesktop.portal.Session"

# memorise le choix d'ecran KDE pour ne plus afficher la boite de dialogue au demarrage suivant
RESTORE_TOKEN_FILE = Path(__file__).resolve().parent / ".screencast_restore_token"


def load_restore_token():
    if RESTORE_TOKEN_FILE.exists():
        return RESTORE_TOKEN_FILE.read_text().strip() or None
    return None


def save_restore_token(token):
    if token:
        RESTORE_TOKEN_FILE.write_text(token)


def parse_args():
    parser = argparse.ArgumentParser(description="Teste une capture KDE/PipeWire en memoire et basse resolution.")
    parser.add_argument("--width", type=int, default=160)
    parser.add_argument("--interval", type=float, default=0.25)
    args = parser.parse_args()
    if args.width < 1:
        parser.error("--width doit etre superieur ou egal a 1")
    if args.interval <= 0:
        parser.error("--interval doit etre strictement positif")
    return args


def option(value):
    return type(value)(value, variant_level=1)


def wait_for_response(bus, request_path):
    result = {}
    loop = GLib.MainLoop()
    request = dbus.Interface(bus.get_object(PORTAL_NAME, request_path), REQUEST)

    def on_response(code, values):
        result["code"] = int(code)
        result["values"] = values
        loop.quit()

    request.connect_to_signal("Response", on_response)
    loop.run()
    if result["code"] != 0:
        raise RuntimeError(f"Demande de partage annulee ou refusee (code {result['code']}).")
    return result["values"]


def open_stream(bus):
    portal = dbus.Interface(bus.get_object(PORTAL_NAME, PORTAL_PATH), SCREENCAST)
    token = uuid.uuid4().hex
    create = portal.CreateSession(
        {
            "handle_token": option(dbus.String(f"request{token}")),
            "session_handle_token": option(dbus.String(f"session{token}")),
        }
    )
    session = wait_for_response(bus, create)["session_handle"]
    select_options = {
        "handle_token": option(dbus.String(f"select{token}")),
        "types": option(dbus.UInt32(1)),
        "multiple": option(dbus.Boolean(False)),
        # cache le curseur : evite a KWin de le composer sur chaque frame, inutile pour une moyenne de couleur
        "cursor_mode": option(dbus.UInt32(1)),
        # persiste le choix d'ecran jusqu'a revocation explicite (pas seulement pendant l'appli)
        "persist_mode": option(dbus.UInt32(2)),
    }
    restore_token = load_restore_token()
    if restore_token:
        select_options["restore_token"] = option(dbus.String(restore_token))
    select = portal.SelectSources(session, select_options)
    wait_for_response(bus, select)
    start = portal.Start(session, "", {"handle_token": option(dbus.String(f"start{token}"))})
    start_response = wait_for_response(bus, start)
    streams = start_response["streams"]
    node_id = int(streams[0][0])
    save_restore_token(str(start_response.get("restore_token", "")))
    pipewire_fd = portal.OpenPipeWireRemote(session, {})
    return session, node_id, pipewire_fd.take()


def make_pipeline(fd, node_id, width, fps):
    pipeline = Gst.parse_launch(
        "pipewiresrc name=source "
        f"fd={fd} path={node_id} "
        "! queue max-size-buffers=1 leaky=downstream "
        # videorate coupe les frames en trop avant l'etape couteuse de conversion/redimensionnement
        f"! videorate ! video/x-raw,framerate={fps}/1 "
        "! videoconvertscale method=nearest-neighbour "
        f"! video/x-raw,format=RGB,width={width} "
        "! appsink name=sink max-buffers=1 drop=true sync=false"
    )
    pipeline.set_state(Gst.State.PLAYING)
    return pipeline, pipeline.get_by_name("sink")


def analyze(sample):
    buffer = sample.get_buffer()
    success, mapped = buffer.map(Gst.MapFlags.READ)
    if not success:
        raise RuntimeError("Lecture du flux PipeWire impossible.")
    try:
        rgb = mapped.data
        pixels = len(rgb) // 3
        red = round(sum(rgb[0::3]) / pixels)
        green = round(sum(rgb[1::3]) / pixels)
        blue = round(sum(rgb[2::3]) / pixels)
    finally:
        buffer.unmap(mapped)
    brightness = round(max(red, green, blue) * 100 / 255)
    return red, green, blue, brightness


def main():
    args = parse_args()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    Gst.init(None)
    bus = dbus.SessionBus()
    print("Choisissez l'ecran dans la boite de dialogue KDE.")
    session, node_id, fd = open_stream(bus)
    fps = max(1, round(1 / args.interval))
    pipeline, sink = make_pipeline(fd, node_id, args.width, fps)
    print(f"Flux en memoire -> {args.width}px, {fps} fps. Ctrl+C pour arreter.")
    try:
        while True:
            started = time.monotonic()
            sample = sink.emit("try-pull-sample", Gst.SECOND)
            if sample is None:
                raise RuntimeError("Aucune image recue de PipeWire.")
            red, green, blue, brightness = analyze(sample)
            elapsed = time.monotonic() - started
            print(f"#{red:02X}{green:02X}{blue:02X}  luminosite {brightness}%  analyse {elapsed:.3f}s")
            time.sleep(max(0, args.interval - elapsed))
    except KeyboardInterrupt:
        print("\nTest arrete.")
    finally:
        pipeline.set_state(Gst.State.NULL)
        dbus.Interface(bus.get_object(PORTAL_NAME, session), SESSION).Close()


if __name__ == "__main__":
    main()