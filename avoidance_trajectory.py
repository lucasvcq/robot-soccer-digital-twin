import rsk 
from REMI import Mouvement 
from REMI import Penalty 
import time 
with rsk.Client() as client:
     avoid = Mouvement(client) 
     penalty = Penalty(client) 
     vitesse_max = 1.0 
     seuil_ball = 0.2 
     seuil_player = 0.5 
     force = 1.3 
     while True: 
        try:
            fini = avoid.mouvement(client.green2, client.ball, vitesse_max, seuil_ball, seuil_player,force) 
            if fini: break
        except:
            penalty.can_move("green", 2)
            time.sleep(1)