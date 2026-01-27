import rsk
from REMI import remi
import time

with rsk.Client() as client:
    Remi = remi(client)
    robot=client.green1
    vitesse_max = 1.0
    seuil_cible = 0.2
    seuil_player = 0.5
    force_player = 1
    seuil_ball_esquive = 0.4
    force = 2
    x,y=client.ball
    destination = (x+0.3,y)
    while True:
        try:
            fini = Remi.mouvement(self, robot, destination, vitesse_max, seuil_cible, seuil_player, force)        
        except Exception as e:
            print("Erreur :", e)   # Affiche la vraie erreur → indispensable pour débug
            Remi.can_move("green", 2)
            time.sleep(1)
