import rsk
from REMI import Remi
import time

with rsk.Client() as client:
    avoid = Remi(client)
    vitesse_max = 1.0
    seuil_ball = 0.20
    seuil_player = 0.3
    force = 2
    T_sleep = 0.01
    marge_angulaire = 1
    while True:
        angle = client.green2.orientation
        objectif = avoid.angle(client.green2, client.ball)
        if objectif == angle + marge_angulaire or objectif == angle - marge_angulaire:
            avoid.rotation_mouvement(client.green2, client.ball)
        else:
            fini = avoid.mouvement(client.green2, client.ball, vitesse_max, seuil_ball, seuil_player,force)
            if fini:
                break
        time.sleep(T_sleep)
