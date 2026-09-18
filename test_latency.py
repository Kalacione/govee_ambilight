#!/usr/bin/env python3
import argparse
import asyncio

from bleak import BleakClient

from govee_control import CONTROL_CHARACTERISTIC, color_command, frame


INTERVALS = (2.0, 1.0, 0.5, 0.25, 0.1)
STATES = (
    ((255, 96, 48), 25),
    ((32, 144, 128), 70),
)


def parse_args():
    parser = argparse.ArgumentParser(description="Teste la cadence BLE sans deconnexion entre les changements.")
    parser.add_argument("mac", nargs="?", default="AA:BB:CC:DD:EE:FF")
    parser.add_argument("--stage-seconds", type=int, default=10)
    args = parser.parse_args()
    if args.stage_seconds < 1:
        parser.error("--stage-seconds doit etre superieur ou egal a 1")
    return args


async def set_state(client, color, brightness):
    red, green, blue = color
    await client.write_gatt_char(CONTROL_CHARACTERISTIC, frame([0x33, 0x04, brightness]), response=False)
    await client.write_gatt_char(CONTROL_CHARACTERISTIC, color_command(red, green, blue), response=False)


async def run(args):
    print(f"Connexion a {args.mac}...")
    async with BleakClient(args.mac) as client:
        print("Connecte. Ctrl+C pour arreter le test.")
        await client.write_gatt_char(CONTROL_CHARACTERISTIC, frame([0x33, 0x01, 0x01]), response=False)

        for interval in INTERVALS:
            updates = max(1, int(args.stage_seconds / interval))
            print(f"Cadence: une mise a jour toutes les {interval:g}s ({1 / interval:g} Hz), {updates} changements.")
            for index in range(updates):
                color, brightness = STATES[index % len(STATES)]
                await set_state(client, color, brightness)
                await asyncio.sleep(interval)

    print("Deconnecte.")


if __name__ == "__main__":
    try:
        asyncio.run(run(parse_args()))
    except KeyboardInterrupt:
        print("\nTest arrete.")