import rsk
from avoid import Remi
import time

with rsk.Client() as client:
    avoid = Remi(client)
    vitesse_max = 1.0
    seuil_ball = 0.2
    seuil_player = 0.3
    force = 3
    while True:

        fini = avoid.mouvement(client.green2, client.ball, vitesse_max, seuil_ball, seuil_player,force)
        if fini:
            break
        time.sleep(0.01)
