import threading
import time
import rsk
from REMI import remi
from math import *

# ====================================================== #
# ===============     GAME MANAGER     ================= #
# ====================================================== #

class GameManager:
    def __init__(self):
        self.couleur = None
        self.inversion_effectuee = False

    # ----------- Sélection initiale ----------- #
    def choisir_couleur(self):
        print("Choisis la couleur : 'green' ou 'blue'")
        self.couleur = input("> ").strip().lower()
        print(f"✅ Couleur choisie : {self.couleur}")

    # ----------- Zones dépendantes du côté ----------- #
    def zone_defense(self, color):
        # X négatif = côté gauche | X positif = côté droit
        return (-0.9, 0) if client.referee["teams"][color] == False else (0.9, 0)

    def zone_attack(self, color):
        return (0.9, 0) if client.referee["teams"][color] == True else (-0.9, 0)

    def direction_goal(self, color):
        # utile pour orienter le robot quand il tire
        return 1 if client.referee["teams"][color] == True else -1


# ====================================================== #
# ========   Fonction de contrôle par robot   ========== #
# ====================================================== #

def controle_robot(remi_obj, robot, robot_id, game, vitesse, err, marge, seuil_ball, role):
    
    while True:
        try:
            ball = remi_obj.client.ball

            # Vérifie si le robot peut bouger (ta fonction existante)
            if remi_obj.can_move(game.couleur, robot_id):
                # zone dépendante du côté actuel
                zone_def = game.zone_defense(game.couleur)
                cote = game.direction_goal(game.couleur)

                # --- APPEL DE TA FONCTION DÉJÀ EXISTANTE --- #
                remi_obj.defense_passive(
                    robot, ball,
                    zone_def,
                    err, vitesse,
                    marge, seuil_ball,
                    role,cote
                )

            time.sleep(0.05)

        except Exception as e:
            print(f"Erreur robot {robot_id}: {e}")
            time.sleep(0.1)


# ====================================================== #
# =================   LANCEMENT MATCH   ================= #
# ====================================================== #

game = GameManager()

game.choisir_couleur()


with rsk.Client() as client:

    Remi = remi(client)

    # Sélection automatique des robots selon couleur choisie
    if game.couleur == "green":
        robot1 = client.green1
        robot2 = client.green2
    else:
        robot1 = client.blue1
        robot2 = client.blue2

    # PARAMÈTRES
    vitesse = 4
    err = 0.04
    marge_front = 0.3
    marge_back = 0.2
    seuil_ball = 0.2
    cote = game.direction_goal(game.couleur)

    # Threads
    t1 = threading.Thread(
        target=controle_robot,
        args=(Remi, robot1, "1", game, vitesse, err, marge_front, seuil_ball, "front")
    )
    t2 = threading.Thread(
        target=controle_robot,
        args=(Remi, robot2, "2", game, vitesse, err, marge_back, seuil_ball, "back")
    )

    t1.start()
    t2.start()
