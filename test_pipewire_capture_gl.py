#!/usr/bin/env python3
"""Variante GPU (GL) de la capture PipeWire : conversion + redimensionnement sur le GPU NVIDIA.

Ne remplace pas test_pipewire_capture.py (pipeline CPU, conserve comme fallback).
Ce script sert uniquement a mesurer si la voie GPU reduit la charge/latence.
"""
import argparse
import time

import gi

gi.require_version("GLib", "2.0")
gi.require_version("Gst", "1.0")
from gi.repository import Gst

from test_pipewire_capture import PORTAL_NAME, SESSION, analyze, open_stream

import dbus
import dbus.mainloop.glib


def parse_args():
    parser = argparse.ArgumentParser(description="Teste une capture KDE/PipeWire acceleree GPU (GL).")
    parser.add_argument("--width", type=int, default=160)
    parser.add_argument("--height", type=int, default=None, help="defaut : proportionnel 16:9")
    parser.add_argument("--interval", type=float, default=0.25)
    args = parser.parse_args()
    if args.width < 1:
        parser.error("--width doit etre superieur ou egal a 1")
    if args.interval <= 0:
        parser.error("--interval doit etre strictement positif")
    if args.height is None:
        args.height = round(args.width * 9 / 16)
    return args


def make_gl_pipeline(fd, node_id, width, height, fps):
    pipeline = Gst.parse_launch(
        "pipewiresrc name=source "
        f"fd={fd} path={node_id} "
        "! queue max-size-buffers=1 leaky=downstream "
        # videorate avant l'upload GPU : on n'envoie au GPU que les frames retenues
        f"! videorate ! video/x-raw,framerate={fps}/1 "
        "! glupload ! glcolorconvert ! video/x-raw(memory:GLMemory),format=RGBA "
        f"! glvideomixer name=mix sink_0::width={width} sink_0::height={height} "
        f"! video/x-raw,format=RGB,width={width},height={height} "
        "! gldownload ! appsink name=sink max-buffers=1 drop=true sync=false"
    )
    pipeline.set_state(Gst.State.PLAYING)
    return pipeline, pipeline.get_by_name("sink")


def main():
    args = parse_args()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    Gst.init(None)
    bus = dbus.SessionBus()
    print("Choisissez l'ecran dans la boite de dialogue KDE.")
    session, node_id, fd = open_stream(bus)
    fps = max(1, round(1 / args.interval))
    pipeline, sink = make_gl_pipeline(fd, node_id, args.width, args.height, fps)
    print(f"Flux GPU (GL) -> {args.width}x{args.height}, {fps} fps. Ctrl+C pour arreter.")
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
