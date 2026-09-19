#!/usr/bin/env python3
import argparse
import statistics
import subprocess
import tempfile
import time
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Teste la capture ecran KDE en basse resolution.")
    parser.add_argument("--width", type=int, default=160)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    if args.width < 1:
        parser.error("--width doit etre superieur ou egal a 1")
    if args.interval <= 0:
        parser.error("--interval doit etre strictement positif")
    return args


def capture_rgb(width):
    with tempfile.TemporaryDirectory() as directory:
        image = Path(directory) / "screen.png"
        subprocess.run(["spectacle", "-d", "0", "-b", "-n", "-o", str(image)], check=True)
        result = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(image), "-vf", f"scale={width}:-2", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
            check=True,
            capture_output=True,
        )
    return result.stdout


def analyze(rgb):
    channels = [rgb[index::3] for index in range(3)]
    red, green, blue = (round(statistics.fmean(channel)) for channel in channels)
    brightness = round((max(red, green, blue) / 255) * 100)
    return red, green, blue, brightness


def main():
    args = parse_args()
    print(f"Capture KDE -> {args.width}px de large. Ctrl+C pour arreter.")
    try:
        while True:
            started = time.monotonic()
            red, green, blue, brightness = analyze(capture_rgb(args.width))
            elapsed = time.monotonic() - started
            print(f"#{red:02X}{green:02X}{blue:02X}  luminosite {brightness}%  capture+analyse {elapsed:.3f}s")
            time.sleep(max(0, args.interval - elapsed))
    except KeyboardInterrupt:
        print("\nTest arrete.")


if __name__ == "__main__":
    main()