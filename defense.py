import rsk
from REMI import Mouvement
from REMI import Penalty
import time

with rsk.Client() as client:
    avoid = Mouvement(client)
    penalty = Penalty(client, debug=True) 
    vitesse_max = 1.0
    seuil_ball = 0.2
    seuil_player = 0.5
    force = 1.3

    while True:
        ok = penalty.wait_until_can_move("green", 2, delay=0.5, timeout=10)
        if not ok:
            time.sleep(1)
            continue

        fini = avoid.mouvement(client.green2, client.ball, vitesse_max, seuil_ball, seuil_player, force)
        if fini:
            break
        time.sleep(0.01)
