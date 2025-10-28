import rsk
from REMI import Mouvement
import time

with rsk.Client() as client:
    avoid = Mouvement(client)
    vitesse_max = 1.0
    seuil_ball = 0.2
    seuil_player = 0.4
    force = 1.5
    while True:
        fini = avoid.mouvement(client.green2, client.ball, vitesse_max, seuil_ball, seuil_player,force)
        if fini:
            break
