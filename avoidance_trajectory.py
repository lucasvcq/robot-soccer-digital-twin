import rsk 
from REMI import remi
import time 
with rsk.Client() as client:
     Remi = remi(client) 
     vitesse_max = 1.0 
     seuil_ball = 0.2
     seuil_player = 0.5 
     force = 1.3 
     while True: 
        try:
            fini = Remi.mouvement(client.green2, client.ball, vitesse_max, seuil_ball, seuil_player,force) 
            #client.green2.goto((client.ball[0],client.ball[1],0),wait=False)
        except:
            Remi.can_move("green", 2)
            time.sleep(1)