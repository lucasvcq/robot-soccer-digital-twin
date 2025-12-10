# Fichier: main_attack.py

import threading
import time
import rsk
from remi_attack import remi
from math import *

# ====================================================== #
# ================== GAME MANAGER ====================== #
# ====================================================== #

class GameManager:
    """Gère la configuration du jeu (couleur, buts)."""
    def __init__(self, client):
        self.client = client
        self.couleur = None

    def choisir_couleur(self):
        print("Choisis la couleur : 'green' ou 'blue'")
        self.couleur = input("> ").strip().lower()
        print(f"Couleur choisie : {self.couleur}")

    def zone_defense(self, color):
        """Position du but à défendre."""
        side = self.client.referee["teams"][color]["x_positive"]
        return (-0.9, 0) if side == False else (0.9, 0)

    def zone_attack(self, color):
        """Position du but adverse (objectif de tir)."""
        side = self.client.referee["teams"][color]["x_positive"]
        return (0.9, 0) if side == False else (-0.9, 0)

    def direction_goal(self, color):
        """Direction de l'attaque (+1 ou -1)."""
        side = self.client.referee["teams"][color]["x_positive"]
        return 1 if side == True else -1


# ====================================================== #
# ================= ROBOT CONTROL ======================= #
# ====================================================== #

def controle_robot(remi_obj, robot, robot_id, game, role, offset, offset_lateral, vitesse, seuil_repulsion_ball, force_repulsion_ball):
    """
    Fonction de contrôle exécutée par un thread, implémentant les rôles d'attaque/soutien.
    """
    objectif_tir = game.zone_attack(game.couleur)
    cote_attaque = game.direction_goal(game.couleur)
    
    while True:
        try:
            ball = remi_obj.client.ball

            if remi_obj.can_move(game.couleur, robot_id):
                
                if role == "attaquant":
                    # L'attaquant utilise le vecteur de répulsion de balle
                    remi_obj.attaque(
                        robot, ball,
                        objectif_tir,
                        offset,
                        offset_lateral,
                        vitesse=vitesse,
                        seuil_repulsion_ball=seuil_repulsion_ball,
                        force_repulsion_ball=force_repulsion_ball
                    )
                
                elif role == "soutien":
                    if ball is None:
                        robot.control(0, 0, 0)
                        continue

                    # --- Stratégie de Soutien Dynamique ---
                    ball_x, ball_y = ball
                    but_x, but_y = objectif_tir
                    
                    # 1. Calculer la position optimale (40% du chemin Balle -> But)
                    ratio_soutien = 0.4
                    x_soutien = ball_x + (but_x - ball_x) * ratio_soutien
                    y_soutien = ball_y + (but_y - ball_y) * ratio_soutien

                    # 2. Condition de repli (si la balle est loin dans notre camp)
                    if (cote_attaque > 0 and ball_x < -0.3) or (cote_attaque < 0 and ball_x > 0.3):
                        x_soutien, y_soutien = 0, 0 

                    # 3. Exécuter le mouvement vers le point de soutien
                    vx_soutien, vy_soutien = remi_obj.vecteur_robot(robot, (x_soutien, y_soutien))
                    robot.control(vx_soutien * vitesse, vy_soutien * vitesse, 0)
                    
            time.sleep(0.05)

        except Exception as e:
            # print(f"Erreur robot {robot_id} ({role}): {e}") 
            time.sleep(0.1)


# ====================================================== #
# ================= LANCEMENT MATCH ===================== #
# ====================================================== #

if __name__ == "__main__":
    with rsk.Client() as client:
        game = GameManager(client)
        game.choisir_couleur()

        Remi = remi(client)

        # Identification des robots
        if game.couleur == "green":
            robot_attaquant = client.green1
            robot_soutien = client.green2
        else:
            robot_attaquant = client.blue1
            robot_soutien = client.blue2

        # --- Paramètres de Contrôle ---
        vitesse_max = 4.0
        offset_shoot = 0.12             # Distance D derrière la balle pour s'aligner
        offset_lateral_esquive = 0.08   # Décalage L pour l'esquive latérale (pour le goto final)
        
        # --- NOUVEAUX PARAMÈTRES DE REPULSION DE BALLE ---
        seuil_repulsion_ball = 0.3 # Distance pour que la répulsion commence (doit être > offset_shoot)
        force_repulsion_ball = 0.8  # Intensité de la force de répulsion

        # Thread Attaquant (Rôle principal avec répulsion de balle)
        t1 = threading.Thread(
            target=controle_robot,
            args=(Remi, robot_attaquant, "1", game, "attaquant", offset_shoot, offset_lateral_esquive, vitesse_max, seuil_repulsion_ball, force_repulsion_ball)
        )
        # Thread Soutien (Pas de répulsion de balle nécessaire)
        #t2 = threading.Thread(
        #    target=controle_robot,
        #    args=(Remi, robot_soutien, "2", game, "soutien", 0, 0, vitesse_max, 0, 0)
        #)

        t1.start()
        #t2.start()

        t1.join()
        #t2.join()