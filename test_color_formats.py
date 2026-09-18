#!/usr/bin/env python3
import argparse
import asyncio

from bleak import BleakClient


CONTROL_CHARACTERISTIC = "00010203-0405-0607-0809-0a0b0c0d2b11"
STEP_SECONDS = 5


def frame(payload):
    data = bytearray(payload)
    data.extend(b"\x00" * (19 - len(data)))
    checksum = 0
    for value in data:
        checksum ^= value
    data.append(checksum)
    return data


def color_manual_02(red, green, blue):
    return frame([0x33, 0x05, 0x02, red, green, blue, 0x00, 0xFF, 0xAE, 0x54])


def color_manual_0d(red, green, blue):
    return frame([0x33, 0x05, 0x0D, red, green, blue])


def color_segmented_15(red, green, blue, mask):
    return frame([0x33, 0x05, 0x15, 0x01, red, green, blue, 0, 0, 0, 0, 0, *mask])


def brightness(level):
    return frame([0x33, 0x04, level])


def parse_args():
    parser = argparse.ArgumentParser(description="Teste des trames couleur BLE Govee, une toutes les 5 secondes.")
    parser.add_argument("mac", nargs="?", default="AA:BB:CC:DD:EE:FF")
    parser.add_argument("--brightness", type=int, default=100)
    args = parser.parse_args()
    if not 0 <= args.brightness <= 100:
        parser.error("--brightness doit etre entre 0 et 100")
    return args


async def run(args):
    candidates = (
        ("manual-02 (rouge)", color_manual_02(255, 0, 0)),
        ("manual-0d (vert)", color_manual_0d(0, 255, 0)),
        ("segmented-15, 12 segments (bleu)", color_segmented_15(0, 0, 255, (0xFF, 0x0F))),
        ("segmented-15, 6 premiers segments (jaune)", color_segmented_15(255, 255, 0, (0x3F, 0x00))),
        ("segmented-15, 6 derniers segments (violet)", color_segmented_15(255, 0, 255, (0xC0, 0x0F))),
    )

    print(f"Connexion a {args.mac}...")
    async with BleakClient(args.mac) as client:
        print("Connecte. Ctrl+C des que la couleur change.")
        await client.write_gatt_char(CONTROL_CHARACTERISTIC, brightness(args.brightness), response=False)
        while True:
            for name, command in candidates:
                print(f"Test: {name}")
                await client.write_gatt_char(CONTROL_CHARACTERISTIC, command, response=False)
                await asyncio.sleep(STEP_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(run(parse_args()))
    except KeyboardInterrupt:
        print("\nTest arrete.")