#!/usr/bin/env python3
import argparse
import asyncio

from bleak import BleakClient


CONTROL_CHARACTERISTIC = "00010203-0405-0607-0809-0a0b0c0d2b11"
ALL_SEGMENTS = (0xFF, 0x0F)


def frame(payload):
    data = bytearray(payload)
    data.extend(b"\x00" * (19 - len(data)))
    checksum = 0
    for value in data:
        checksum ^= value
    data.append(checksum)
    return data


def color_command(red, green, blue, mask=ALL_SEGMENTS):
    return frame([0x33, 0x05, 0x15, 0x01, red, green, blue, 0, 0, 0, 0, 0, *mask])


def brightness_command(level, mask=ALL_SEGMENTS):
    return frame([0x33, 0x05, 0x15, 0x02, level, *mask])


def parse_color(value):
    value = value.removeprefix("#")
    if len(value) != 6:
        raise argparse.ArgumentTypeError("--color doit etre au format RRGGBB ou #RRGGBB")
    try:
        return tuple(int(value[index : index + 2], 16) for index in range(0, 6, 2))
    except ValueError as error:
        raise argparse.ArgumentTypeError("--color doit contenir uniquement des chiffres hexadecimaux") from error


def parse_args():
    parser = argparse.ArgumentParser(description="Commande ponctuelle d'une lampe Govee BLE.")
    parser.add_argument("mac", help="Adresse MAC Bluetooth de la lampe")
    parser.add_argument("action", choices=("on", "off", "color"))
    parser.add_argument("--color", type=parse_color, default=(255, 128, 64), metavar="RRGGBB")
    parser.add_argument("--brightness", type=int, default=100)
    args = parser.parse_args()
    if not 0 <= args.brightness <= 100:
        parser.error("--brightness doit etre entre 0 et 100")
    return args


async def run(args):
    print(f"Connexion a {args.mac}...")
    async with BleakClient(args.mac) as client:
        if args.action == "off":
            await client.write_gatt_char(CONTROL_CHARACTERISTIC, frame([0x33, 0x01, 0x00]), response=False)
            print("Lampe eteinte.")
        else:
            await client.write_gatt_char(CONTROL_CHARACTERISTIC, frame([0x33, 0x01, 0x01]), response=False)
            if args.action == "color":
                red, green, blue = args.color
                await client.write_gatt_char(CONTROL_CHARACTERISTIC, frame([0x33, 0x04, args.brightness]), response=False)
                await client.write_gatt_char(CONTROL_CHARACTERISTIC, color_command(red, green, blue), response=False)
                print(f"Couleur #{red:02X}{green:02X}{blue:02X}, luminosite {args.brightness}/100.")
            else:
                print("Lampe allumee.")
    print("Deconnecte.")


if __name__ == "__main__":
    asyncio.run(run(parse_args()))