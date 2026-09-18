# Systeme ambilight avec lumiere Govee via bluetooth

## Contexte

Linux Manjaro 25, dongle bluetooth.
Ecran tele 4k avec lumieres govee derriere (@ blocs de 18 cm)

## But 

faire correspondre la couleur et l'intensite de la lumiere avec le contenu de l'ecran.
Phase d'analyse et de test a realiser

## Moyens

Utiliser la librairie python donnee dans le [guide](./guide.md)
Utiliser le terminal pour effectuer la phase d'analyse


## Contraintes

- K.I.S.S : on veut un PoC fonctionnel, un MVP, pas une usine a gaz
- Analyser la vitesse de reponse des lumieres aux commandes de changement
- verifier que cette vitesse est compatible a une utilisation ambilight
- ne pas bouffer toute la bande passante bluetooth, d'autres peripheriques s'en servent
- pas besoin que le truc tourne a 200Hz 
- Consommation de ressources minimales
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

Conclusion : le BLE local est utilisable pour le PoC, a condition de garder la connexion ouverte pendant l'ambilight. La librairie H613 ne doit pas etre utilisee pour les couleurs du H6056.