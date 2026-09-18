#!/usr/bin/env python3
import argparse
import asyncio

from govee_H613_BTcontroller import GoveeController


COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "white": (255, 255, 255),
}


def parse_args():
    parser = argparse.ArgumentParser(description="Commande ponctuelle d'une lampe Govee BLE.")
    parser.add_argument("mac", help="Adresse MAC Bluetooth de la lampe")
    parser.add_argument("action", choices=("on", "off", "color"))
    parser.add_argument("--color", choices=COLORS, default="blue")
    parser.add_argument("--brightness", type=int, default=255)
    args = parser.parse_args()
    if not 0 <= args.brightness <= 255:
        parser.error("--brightness doit etre entre 0 et 255")
    return args


async def run(args):
    controller = GoveeController(args.mac)
    print(f"Connexion a {args.mac}...")
    controller = await controller.connect()
    try:
        if args.action == "off":
            await controller.turn_off()
            print("Lampe eteinte.")
        else:
            await controller.turn_on()
            if args.action == "color":
                await controller.set_color(COLORS[args.color])
                await controller.set_brightness(args.brightness)
                print(f"Couleur {args.color}, luminosite {args.brightness}/255.")
            else:
                print("Lampe allumee.")
    finally:
        await controller.disconnect()
        print("Deconnecte.")


if __name__ == "__main__":
    asyncio.run(run(parse_args()))