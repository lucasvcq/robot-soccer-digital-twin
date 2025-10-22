import rsk
from REMI import mouvement
import time

with rsk.Client() as client:
    avoid = mouvement(client)
    vitesse_max = 1.0
    seuil_ball = 0.20
    seuil_player = 0.5
    force = 0.7
    T_sleep = 0.01
    marge_angulaire = 0.1
    while True:
        avoid.rotation_mouvement(client.green2, client.ball, marge_angulaire)
        fini = avoid.mouvement(client.green2, client.ball, vitesse_max, seuil_ball, seuil_player,force)
        if fini:
            break
        time.sleep(T_sleep)
