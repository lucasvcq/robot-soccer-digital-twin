import rsk
from REMI import remi
import time

with rsk.Client() as client:
    Remi = remi(client)
    robot = client.green1
    zone_attaque = (0.9, 0)
    erreur_placement = 0.04
    vitesse = 1
    marge = 0.2
    seuil_ball = 0.2
    role = "direct"
    seuil = 0.2
    cote = -1
    while True:
        try:
            ballx, bally= client.ball
            ball = (ballx, bally)
            print(ball)
            fini = Remi.defense_passive(robot, ball, zone_attaque, erreur_placement, vitesse, marge, seuil_ball, role, cote, seuil)
        except Exception as e:
            print("Erreur :", e)   # Affiche la vraie erreur → indispensable pour débug
            Remi.can_move("green", 2)
            time.sleep(1)
