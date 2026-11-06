#!/usr/bin/env python3
import argparse
import asyncio

from bleak import BleakClient


CONTROL_CHARACTERISTIC = "00010203-0405-0607-0809-0a0b0c0d2b11"
STEP_SECONDS = 5

# segments 0-5 = un bloc physique, 6-11 = l'autre (H6056 : 2 blocs, 1 seul appareil BLE)
MASK_LEFT = (0x3F, 0x00)
MASK_RIGHT = (0xC0, 0x0F)
MASK_BOTH = (0xFF, 0x0F)


def frame(payload):
    data = bytearray(payload)
    data.extend(b"\x00" * (19 - len(data)))
    checksum = 0
    for value in data:
        checksum ^= value
    data.append(checksum)
    return data


def color_command(red, green, blue, mask):
    return frame([0x33, 0x05, 0x15, 0x01, red, green, blue, 0, 0, 0, 0, 0, *mask])


def brightness(level):
    return frame([0x33, 0x04, level])


def parse_args():
    parser = argparse.ArgumentParser(description="Teste le pilotage individuel des 2 blocs Govee (gauche/droite).")
    parser.add_argument("mac", help="Adresse MAC Bluetooth de la lampe")
    parser.add_argument("--brightness", type=int, default=100)
    parser.add_argument("--swap", action="store_true", help="inverse gauche et droite")
    args = parser.parse_args()
    if not 0 <= args.brightness <= 100:
        parser.error("--brightness doit etre entre 0 et 100")
    return args


async def run(args):
    mask_left, mask_right = MASK_LEFT, MASK_RIGHT
    if args.swap:
        mask_left, mask_right = mask_right, mask_left

    candidates = (
        ("GAUCHE seul (rouge)", color_command(255, 0, 0, mask_left)),
        ("DROITE seul (bleu)", color_command(0, 0, 255, mask_right)),
        ("LES DEUX (vert)", color_command(0, 255, 0, MASK_BOTH)),
    )

    print(f"Connexion a {args.mac}...")
    async with BleakClient(args.mac) as client:
        print("Connecte. Ctrl+C des que le comportement est identifie.")
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
