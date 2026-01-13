import threading
import time
import rsk
from REMI import remi
from Jules_Execute import action
from math import *

# ====================================================== #
# ===============      GAME MANAGER      ================= #
# ====================================================== #

class GameManager:
    def __init__(self, client): 
        # CORRECTION : Stocke l'objet client
        self.client = client
        self.couleur = None
        self.inversion_effectuee = False

    # ----------- Sélection initiale ----------- #
    def choisir_couleur(self):
        print("Choisis la couleur : 'green' ou 'blue'")
        self.couleur = input("> ").strip().lower()
        print(f"✅ Couleur choisie : {self.couleur}")

    # ----------- Zones dépendantes du côté ----------- #
    def zone_defense(self, color):
        # CORRECTION : Utilise self.client
        referee_side = self.client.referee["teams"][color].get("side", False)
        return (-0.9, 0) if referee_side == False else (0.9, 0)

    def zone_attack(self, color):
        # CORRECTION : Utilise self.client
        referee_side = self.client.referee["teams"][color].get("side", False)
        return (0.9, 0) if referee_side == False else (-0.9, 0)

    def direction_goal(self, color):
        # CORRECTION : Utilise self.client
        referee_side = self.client.referee["teams"][color].get("side", False)
        return 1 if referee_side == False else -1 


# ====================================================== #
# ========   Fonction de contrôle par robot   ========== #
# ====================================================== #

def controle_robot(remi_obj, robot, robot_id, game, vitesse, err, marge, seuil_ball, role, seuil_player, force_player, seuil_ball_esquive, force_ball):
    
    while True:
        try:
            ball = remi_obj.client.ball

            if remi_obj.can_move(game.couleur, robot_id):
                
                zone_def = game.zone_defense(game.couleur)
                cote = game.direction_goal(game.couleur)
                
                # CORRECTION : Utilisation de robot.position[0] pour la position X
                robot_x = robot.position[0]
                
                # Logique de mouvement
                if (ball[0] - robot_x) * cote < 0: # Balle derrière le robot
                    remi_obj.defense_passive(
                        robot, ball,
                        zone_def,
                        err, vitesse,
                        marge, seuil_ball,
                        role, cote
                    )
                
                elif (ball[0] - robot_x) * cote > 0: # Balle devant le robot
                    remi_obj.defense_passive_retour(
                        robot, ball,
                        zone_def,
                        err, vitesse,
                        marge, seuil_ball,
                        role, cote, seuil_player, 
                        force_player, seuil_ball_esquive, 
                        force_ball
                    )

            time.sleep(0.05)

        except Exception as e:
            print(f"Erreur robot {robot_id}: {e}") 
            time.sleep(0.1)


# ====================================================== #
# =================  LANCEMENT MATCH  ================= #
# ====================================================== #

with rsk.Client() as client:

    # 1. CORRECTION : Création du GameManager AVEC l'objet client
    game = GameManager(client) 
    
    game.choisir_couleur()

    # 2. Création de l'objet Remi
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
    seuil_player = 0.5
    force_player = 1
    seuil_ball_esquive = 0.4
    force_ball = 1
    
    cote = game.direction_goal(game.couleur) 

    # Threads
    t1 = threading.Thread(
        target=controle_robot,
        args=(Remi, robot1, "1", game, vitesse, err, marge_front, seuil_ball, "front", seuil_player, force_player, seuil_ball_esquive, force_ball)
    )
    t2 = threading.Thread(
        target=controle_robot,
        args=(Remi, robot2, "2", game, vitesse, err, marge_back, seuil_ball, "back", seuil_player, force_player, seuil_ball_esquive, force_ball)
    )

    t1.start()
    t2.start()