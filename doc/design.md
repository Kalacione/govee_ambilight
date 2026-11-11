# Notes de conception

## Contexte

Linux Manjaro 25, dongle bluetooth.
Ecran tele 4k avec lumieres govee derriere (@ blocs de 18 cm)

## But 

faire correspondre la couleur et l'intensite de la lumiere avec le contenu de l'ecran.
Phase d'analyse et de test a realiser

## Moyens

Utiliser la librairie python donnee dans le [guide](guide.md)
Utiliser le terminal pour effectuer la phase d'analyse


## Contraintes

- K.I.S.S : on veut un PoC fonctionnel, un MVP, pas une usine a gaz
- Analyser la vitesse de reponse des lumieres aux commandes de changement
- verifier que cette vitesse est compatible a une utilisation ambilight
- ne pas bouffer toute la bande passante bluetooth, d'autres peripheriques s'en servent
- pas besoin que le truc tourne a 200Hz 
- Consommation de ressources minimales
- ne pas envoyer une commande BLE si la couleur et la luminosite ciblees sont identiques aux dernieres valeurs envoyees
- proposer deux profils de cadence : `normal` a 4 Hz et `fast` a 10 Hz
- permettre une configuration facile (script de config sh, compatible zsh, qui va chercher automatiquement le periph bluetooth opur trouver le govee et faire un fichier de conf pour ne pas devoir le refaire a chaque init de programme) 
- fichier de setup sh (compatible zsh) pour installer les dependances et les packages

## Battle plan

1. checker la config et la visibilite des lumieres govee
2. faire un test rapide de commande pour voir si on peut changer la couleur de la lumiere et l'intensite
3. verifier le temps de reponse (l'humain lance un petit script qui choisi une couleur rando et constate par lui meme le temps de reponse)
4. Si le test est valide, trouver une lib pour capter le contenu de l'ecran afin d'en determiner couleur et intensite lumineuse
5. optimiser pour ne pas consommer trop de ressources
6. packaging propre

## Resultats des premiers tests

- Controleur Bluetooth et H6056 detectes : `AA:BB:CC:DD:EE:FF`.
- La luminosite BLE fonctionne sur une plage de `0` a `100`.
- La commande couleur de `govee_H613_BTcontroller` ne fonctionne pas avec le H6056.
- La trame BLE segmentee `0x33 0x05 0x15` avec le masque `FF 0F` fonctionne pour les 12 segments.
- Une commande BLE avec connexion puis deconnexion prend environ 2 secondes.
- Une connexion BLE persistante supporte les changements couleur et luminosite a 10 Hz.

Conclusion : le BLE local est utilisable pour le PoC, a condition de garder la connexion ouverte pendant l'ambilight. La librairie H613 ne doit pas etre utilisee pour les couleurs du H6056.

## Capture ecran

La session est KDE/KWin sous Wayland. `grim` ne convient pas a ce compositeur. Le PoC utilise le portail de screencast KDE (`xdg-desktop-portal-kde`) et PipeWire via GStreamer (`pipewiresrc`), en gardant le flux entierement en memoire (aucun fichier disque, aucune image 4K traitee).

Resultat mesure (`test_pipewire_capture.py`, capture reduite a 160px de large) :
- temps de traitement par image : ~0.004s
- charge CPU observee : 2 a 4%

Conclusion : cette methode de capture est validee pour le PoC ambilight.

## Micro-saccades video pendant la capture

Constat : des micro-saccades video apparaissent des que le flux de capture est actif, quel que soit le profil (normal/fast).

Pistes testees :
- pipeline CPU allege (`videorate` + `videoconvertscale` en `nearest-neighbour`, cf `test_pipewire_capture.py`).
- pipeline 100% GPU NVIDIA (`glupload` -> `glcolorconvert` -> `glvideomixer` (resize) -> `gldownload`, cf `test_pipewire_capture_gl.py`), conserve en alternative mais pas active par defaut.

Resultat : les deux pipelines donnent le meme temps de traitement tres bas (<0.09s) et les memes micro-saccades. Le traitement cote script n'est donc pas la cause.

Cause identifiee : bug KWin confirme dans le composant `screencasting` ([bug KDE 479250](https://bugs.kde.org/show_bug.cgi?id=479250), statut CONFIRMED, actif en 2026), corrobore par des rapports communautaires similaires (ex. Sunshine/kwin capture backend). Le cout est cree par KWin au moment ou il exporte les frames vers PipeWire, avant meme que notre pipeline ne les recoive.

## Solution retenue : capture GPU avec DMA-BUF

Deux leviers supplementaires ont permis de resoudre les micro-saccades :
- `cursor_mode` du portail passe de `2` (curseur incruste) a `1` (cache) : evite a KWin de composer le curseur sur chaque frame.
- Le pipeline GPU tente une negociation `video/x-raw(memory:DMABuf)` avec `pipewiresrc` (partage GPU zero-copy), avec repli automatique et transparent sur l'upload GL classique si KWin la refuse.

Resultat mesure : negociation DMA-BUF acceptee, micro-saccades disparues, temps de traitement ~0.001s.

`ambilight.py` utilise desormais ce pipeline GPU par defaut (`test_pipewire_capture_gl.py`). Le pipeline CPU (`test_pipewire_capture.py`) reste disponible tel quel en reference/fallback si le GPU ou le driver NVIDIA venait a poser probleme sur une autre machine.

## Bandes noires et luminosite globale

Constat : sur un film en 2.39:1 affiche sur l ecran 16:9, les bandes noires comptent dans la moyenne et assombrissent le retro-eclairage (environ 25 % de pixels noirs).

Solution retenue : `--crop-y POURCENT` retire du calcul cette part de la hauteur, en haut et en bas. `al.sh` passe 13, la taille des bandes d un film 2.39:1. Sur du 16:9 plein ecran, on ignore seulement les bords haut et bas, sans effet visible.

Ecartee : la detection automatique des lignes noires image par image. Elle ferait varier la lumiere sur les scenes sombres (ciel de nuit pris pour une bande).

Luminosite globale : `CHANNEL_GAIN` multiplie par 1,25, soit (1.25, 1.12, 1.0), en gardant le rapport entre canaux qui rechauffe le rendu.
