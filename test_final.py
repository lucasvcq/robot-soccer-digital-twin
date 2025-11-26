import threading
import time
import rsk
from test_remi import remi
from math import *

# ====================================================== #
# ================== GAME MANAGER ====================== #
# ====================================================== #

class GameManager:
    def __init__(self, client):
        self.client = client
        self.couleur = None

    def choisir_couleur(self):
        print("Choisis la couleur : 'green' ou 'blue'")
        self.couleur = input("> ").strip().lower()
        print(f"Couleur choisie : {self.couleur}")

    def zone_defense(self, color):
        side = self.client.referee["teams"][color]["x_positive"]  # "left" ou "right"
        print(side)
        return (-0.9, 0) if side == False else (0.9, 0)

    def zone_attack(self, color):
        side = self.client.referee["teams"][color]["x_positive"]
        return (0.9, 0) if side == False else (-0.9, 0)

    def direction_goal(self, color):
        side = self.client.referee["teams"][color]["x_positive"]
        return 1 if side == True else -1


# ====================================================== #
# ================= ROBOT CONTROL ======================= #
# ====================================================== #

def controle_robot(remi_obj, robot, robot_id, game, vitesse, err, marge, seuil_ball, role, seuil):

    while True:
        try:
            ball = remi_obj.client.ball

            if remi_obj.can_move(game.couleur, robot_id):

                zone_def = game.zone_defense(game.couleur)
                cote = game.direction_goal(game.couleur)

                remi_obj.defense_passive(
                    robot, ball,
                    zone_def,
                    err, vitesse,
                    marge, seuil_ball,
                    role, cote, seuil
                )

            time.sleep(0.05)

        except Exception as e:
            print(f"Erreur robot {robot_id}: {e}")
            time.sleep(0.1)


# ====================================================== #
# ================= LANCEMENT MATCH ===================== #
# ====================================================== #

with rsk.Client() as client:

    game = GameManager(client)
    game.choisir_couleur()

    Remi = remi(client)

    if game.couleur == "green":
        robot1 = client.green1
        robot2 = client.green2
    else:
        robot1 = client.blue1
        robot2 = client.blue2

    vitesse = 4
    err = 0.04
    marge_front = 0.3
    marge_back  = 0.2
    seuil_ball = 0.2
    seuil = 0.2

    t1 = threading.Thread(
        target=controle_robot,
        args=(Remi, robot1, "1", game, vitesse, err, marge_front, seuil_ball, "front", seuil)
    )
    t2 = threading.Thread(
        target=controle_robot,
        args=(Remi, robot2, "2", game, vitesse, err, marge_back, seuil_ball, "back", seuil)
    )

    t1.start()
    t2.start()

    t1.join()
    t2.join()
