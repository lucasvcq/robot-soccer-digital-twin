import rsk
from REMI import remi
import time

with rsk.Client() as client:
    Remi = remi(client)

    vitesse_max = 1.0
    seuil_cible = 0.1
    seuil_player = 0.5
    force_player = 1
    seuil_ball_esquive = 0.4
    force_ball = 1
    x,y=client.ball
    destination = (x+0.1,y)
    while True:
        try:
            x,y=client.ball
            destination = (x+0.1,y)
            fini = Remi.mouvement_esquive_balle(client.green2, destination, client.ball, vitesse_max, seuil_cible, seuil_player, force_player, seuil_ball_esquive, force_ball)
        except Exception as e:
            print("Erreur :", e)   # Affiche la vraie erreur → indispensable pour débug
            Remi.can_move("green", 2)
            time.sleep(1)
