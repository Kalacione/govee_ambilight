#!/usr/bin/env python3
import argparse
import asyncio

from bleak import BleakClient

from govee_control import ALL_SEGMENTS, frame


CONTROL_CHARACTERISTIC = "00010203-0405-0607-0809-0a0b0c0d2b11"
RED = (255, 0, 0)
BLUE = (0, 0, 255)
FLIP_SECONDS = 0.4
FLIPS_PER_CANDIDATE = 6

# octets actuellement laisses a zero dans la trame couleur segmentee :
# [0]=0x33 [1]=0x05 [2]=0x15 [3]=0x01 [4..6]=RGB [7..11]=? [12..13]=masque [14..18]=?
CANDIDATE_POSITIONS = (7, 8, 9, 10, 11, 14, 15, 16, 17, 18)
CANDIDATE_VALUES = (0x01, 0xFF)


def color_command_with_extra(rgb, position, value):
    red, green, blue = rgb
    payload = [0x33, 0x05, 0x15, 0x01, red, green, blue, 0, 0, 0, 0, 0, *ALL_SEGMENTS, 0, 0, 0, 0, 0]
    payload[position] = value
    return frame(payload)


def parse_args():
    parser = argparse.ArgumentParser(description="Explore si un octet de padding influence la vitesse de fondu.")
    parser.add_argument("mac", help="Adresse MAC Bluetooth de la lampe")
    args = parser.parse_args()
    return args


async def run(args):
    print(f"Connexion a {args.mac}...")
    async with BleakClient(args.mac) as client:
        print("Connecte. Observe la vitesse de transition rouge/bleu. Ctrl+C des qu'elle change.")
        while True:
            for position in CANDIDATE_POSITIONS:
                for value in CANDIDATE_VALUES:
                    print(f"Test: octet {position} = 0x{value:02X}")
                    for step in range(FLIPS_PER_CANDIDATE):
                        color = RED if step % 2 == 0 else BLUE
                        await client.write_gatt_char(
                            CONTROL_CHARACTERISTIC, color_command_with_extra(color, position, value), response=False
                        )
                        await asyncio.sleep(FLIP_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(run(parse_args()))
    except KeyboardInterrupt:
        print("\nTest arrete.")
