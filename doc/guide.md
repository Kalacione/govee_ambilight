# 💡 Guide : Piloter ses lumières Govee Bluetooth sous Linux avec Python

Ce guide vous explique comment configurer et utiliser un script Python sous Linux pour contrôler vos lumières Govee en Bluetooth Low Energy (BLE).

---

## 🛠️ Préququis obligatoires

Avant de commencer, assurez-vous d'avoir installé les outils Bluetooth système nécessaires :

```bash
sudo apt update
sudo apt install bluetooth bluez bluez-tools python3-pip
```

---

## 🔍 Étape 1 : Trouver l'adresse MAC de vos lumières

Vos lumières Govee ne doivent pas être connectées à votre smartphone (fermez l'application Govee Home).

1. Lancez un scan des appareils Bluetooth à proximité :
    
    ```bash
    sudo hcitool lescan
    ```
    
2. Repérez une ligne contenant un nom comme **`ihoment_HXXXX_XXXX`** ou **`Govee_XXXX`** (où `HXXXX` correspond au modèle de votre appareil).
3. Notez l'adresse MAC associée (ex: `AA:BB:CC:DD:EE:FF`).

---

## 📦 Étape 2 : Installer la bibliothèque Python

Nous utilisons la bibliothèque communautaire `govee_H613_BTcontroller`. Installez-la via votre terminal :

```bash
pip3 install govee_H613_BTcontroller
```

*Note : Si votre distribution Linux bloque l'installation globale de pip (erreur "externally-managed-environment"), ajoutez le drapeau `--break-system-packages` à la fin de la commande ou utilisez un environnement virtuel (`venv`).*

---

## 📝 Étape 3 : Créer le script de contrôle

1. Créez un nouveau fichier nommé `govee_control.py` :
    
    ```bash
    nano govee_control.py
    ```
    
2. Collez le code suivant à l'intérieur (**pensez à remplacer l'adresse MAC factice par la vôtre**) :

```python
import asyncio
import sys
from govee_H613_BTcontroller import GoveeController

# ⚠️ REMPLACEZ PAR L'ADRESSE MAC DE VOS LUMIÈRES
MAC_ADDRESS = "AA:BB:CC:DD:EE:FF"

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 govee_control.py [on|off|blue|red|green]")
        return

    action = sys.argv[1].lower()

    print(f"Connexion à l'appareil {MAC_ADDRESS}...")
    device = GoveeController(MAC_ADDRESS)
    device = await device.connect()
    print("Connecté avec succès !")

    if action == "on":
        await device.turn_on()
        print("Lumières allumées.")
    elif action == "off":
        await device.turn_off()
        print("Lumières éteintes.")
    elif action in ["red", "blue", "green"]:
        await device.turn_on()
        await device.set_color(action)
        await device.set_brightness(255) # Luminosité max (0 à 255)
        print(f"Couleur changée en {action}.")
    else:
        print("Commande non reconnue.")

    await device.disconnect()
    print("Déconnecté.")

if __name__ == "__main__":
    asyncio.run(main())
```

1. Sauvegardez et quittez (sur nano : `Ctrl+O`, `Entrée`, puis `Ctrl+X`).

---

## 🚀 Étape 4 : Utiliser le script

Vous pouvez maintenant piloter vos lumières en passant des arguments à votre script dans le terminal :

- **Allumer :** `python3 govee_control.py on`
- **Éteindre :** `python3 govee_control.py off`
- **Changer en Bleu :** `python3 govee_control.py blue`

---

## ⚠️ Dépannage fréquent

- **Erreur de connexion ("Device not found" ou "Timeout") :** L'antenne Bluetooth de votre téléphone est probablement encore appairée au kit. Désactivez temporairement le Bluetooth de votre téléphone.
- **Permissions refusées :** Si Python n'a pas accès à votre puce Bluetooth locale, essayez d'exécuter le script avec `sudo python3 govee_control.py on`.

# 🎬 Ambilight Govee Bluetooth pour Manjaro 25 (Wayland)

Ce guide est optimisé pour **Manjaro 25 utilisant le protocole d'affichage Wayland**. Il utilise `grim` pour une capture d'écran native, sécurisée et ultra-rapide.

---

## 📦 1. Installation des dépendances système et Python

Sous Manjaro, nous allons installer `grim` pour la gestion des captures sous Wayland, ainsi que les bibliothèques Python nécessaires via `pacman` (pour éviter les conflits d'environnement propre à Arch/Manjaro).

Ouvrez votre terminal et exécutez :

```bash
# Installation des outils système (Bluetooth et capture Wayland)
sudo pacman -Syu bluetooth bluez bluez-utils grim python-pip python-opencv python-numpy

# Installation de la bibliothèque de contrôle Govee
pip3 install govee_H613_BTcontroller --break-system-packages
```

---

## 📝 2. Le Script Python Optimisé (`govee_wayland_ambilight.py`)

Ce script remplace `mss` par un appel système ultra-léger à `grim`, qui envoie les données de l'écran directement dans le tampon mémoire d'OpenCV sans écrire de fichier sur le disque.

Créez un fichier nommé `govee_wayland_ambilight.py` :

```python
import asyncio
import cv2
import numpy as np
import subprocess
import sys
from govee_H613_BTcontroller import GoveeController

# ⚠️ REMPLACEZ PAR LES ADRESSES MAC DE VOS DEUX BLOCS
MAC_GAUCHE = "A4:C1:38:XX:XX:X1"
MAC_DROITE = "A4:C1:38:XX:XX:X2"

# Configuration de la capture
LARGEUR_BANDE_PCT = 15
INTERVALLE_MAJ = 0.3 # Temps en secondes entre deux analyses (300ms)

def capturer_ecran_wayland():
    """Utilise 'grim' pour capturer l'écran sous Wayland et le charger en mémoire via OpenCV."""
    try:
        # Lance grim et récupère l'image au format PNG directement dans le flux de sortie (stdout)
        process = subprocess.Popen(['grim', '-t', 'png', '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()

        # Convertit les données binaires en image exploitable par OpenCV
        nparr = np.frombuffer(stdout, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"❌ Erreur lors de la capture Wayland (grim) : {e}")
        return None

def obtenir_couleur_moyenne(image_zone):
    """Calcule la couleur moyenne d'une zone."""
    if image_zone is None or image_zone.size == 0:
        return (0, 0, 0)
    couleur_moyenne = cv2.mean(image_zone)[:3] # Renvoie (B, G, R)
    b, g, r = int(couleur_moyenne[0]), int(couleur_moyenne[1]), int(couleur_moyenne[2])

    if max(r, g, b) < 15:
        return (0, 0, 0)

    return (r, g, b)

async def boucle_ambilight():
    print("Connexion aux blocs Govee...")
    try:
        govee_gauche = await GoveeController(MAC_GAUCHE).connect()
        govee_droite = await GoveeController(MAC_DROITE).connect()
        print("💡 Connecté aux deux blocs ! Démarrage de l'Ambilight sous Wayland...")
    except Exception as e:
        print(f"❌ Erreur de connexion Bluetooth : {e}")
        return

    dernier_gauche = (0, 0, 0)
    dernier_droite = (0, 0, 0)

    try:
        while True:
            # Capture de l'écran via grim
            cadre = capturer_ecran_wayland()

            if cadre is None:
                await asyncio.sleep(INTERVALLE_MAJ)
                continue

            hauteur, largeur, _ = cadre.shape
            taille_bande = int(largeur * (LARGEUR_BANDE_PCT / 100))

            # Découpage des zones latérales (Gauche / Droite)
            zone_gauche = cadre[0:hauteur, 0:taille_bande]
            zone_droite = cadre[0:hauteur, (largeur - taille_bande):largeur]

            # Calcul des couleurs moyennes
            rgb_gauche = obtenir_couleur_moyenne(zone_gauche)
            rgb_droite = obtenir_couleur_moyenne(zone_droite)

            tâches = []

            # Envoi uniquement si le changement est notable pour économiser le processeur/Bluetooth
            if np.linalg.norm(np.array(rgb_gauche) - np.array(dernier_gauche)) > 15:
                tâches.append(govee_gauche.set_color(rgb_gauche))
                dernier_gauche = rgb_gauche

            if np.linalg.norm(np.array(rgb_droite) - np.array(dernier_droite)) > 15:
                tâches.append(govee_droite.set_color(rgb_droite))
                dernier_droite = rgb_droite

            # Exécution parallèle des requêtes Bluetooth
            if tâches:
                await asyncio.gather(*tâches)

            await asyncio.sleep(INTERVALLE_MAJ)

    except KeyboardInterrupt:
        print("\nArrêt de l'Ambilight...")
    finally:
        await govee_gauche.disconnect()
        await govee_droite.disconnect()
        print("Déconnecté proprement.")

if __name__ == "__main__":
    asyncio.run(boucle_ambilight())
```

---

## 🚀 3. Exécution

Assurez-vous que le service Bluetooth est bien actif sur votre Manjaro :

```bash
sudo systemctl start bluetooth
```

Lancez ensuite le script :

```bash
python3 govee_wayland_ambilight.py
```

Pour l'arrêter, pressez **`Ctrl + C`**.