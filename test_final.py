import threading
import time
import rsk
from test_remi import remi
from math import sqrt

# ====================================================== #
# ================== GAME MANAGER ====================== #
# ====================================================== #

class GameManager:
    def __init__(self, client):
        self.client = client
        self.couleur = None

    def choisir_couleur(self):
        while self.couleur not in ["green", "blue"]:
            print("Choisis la couleur : 'green' ou 'blue'")
            self.couleur = input("> ").strip().lower()
        print(f"Couleur choisie : {self.couleur}")

    def zone_defense(self, color):
        side = self.client.referee["teams"][color]["x_positive"]
        return (0.9, 0) if side else (-0.9, 0)

    def direction_goal(self, color):
        side = self.client.referee["teams"][color]["x_positive"]
        # cote = 1 si nos buts sont à droite (x>0), -1 si à gauche (x<0)
        return 1 if side else -1

# ====================================================== #
# ================= ROBOT CONTROL ======================= #
# ====================================================== #

def controle_robot(remi_obj, robot, robot_id, game, vitesse, err, marge, seuil_ball, role, start_time):
    ball_last_pos = None
    ball_stop_timer = 0
    
    while True:
        try:
            # Vérification si le robot a le droit de bouger (Referee)
            if not remi_obj.can_move(game.couleur, robot_id):
                time.sleep(0.5)
                continue

            ball = remi_obj.client.ball
            if ball is None: continue

            zone_def = game.zone_defense(game.couleur)
            cote = game.direction_goal(game.couleur)
            elapsed = time.time() - start_time
            
            # --- 1. DETECTION IMMOBILITÉ BALLE (3 SECONDES) ---
            is_ball_stuck = False
            if ball_last_pos is not None:
                dist_mouv = sqrt((ball[0]-ball_last_pos[0])**2 + (ball[1]-ball_last_pos[1])**2)
                if dist_mouv < 0.01: # Si elle bouge de moins d'1cm
                    ball_stop_timer += 0.1
                else:
                    ball_stop_timer = 0
                if ball_stop_timer >= 3.0:
                    is_ball_stuck = True
            ball_last_pos = ball

            # --- 2. LOGIQUE STRATÉGIQUE ---
            
            # Condition : La balle est dans notre camp ?
            # (Si cote=1, notre camp est x > 0. Si cote=-1, notre camp est x < 0)
            ball_dans_notre_camp = (ball[0] * cote > 0)
            x,y = robot.position
            if y>0:
                yposition=1
            else:
                yposition=-1

            # A. MODE DEFENSE (Balle dans notre camp)
            if ball_dans_notre_camp and not is_ball_stuck:
                remi_obj.defense_passive(robot, ball, zone_def, err, vitesse, marge, seuil_ball, role, cote, 0.2)
            
            # B. MODE ATTAQUE (Balle immobile OU Hors de notre camp)
            else:
                if elapsed < 30:
                    # Les 30 premières secondes
                    if role == "front":
                        # Tir premier poteau (y = 0.3 ou -0.3 selon le côté)
                        but_adv = (-0.9 * cote, 0.25 * yposition) 
                        ##########################remi_obj.attaque(robot, ball, but_adv, offset=0.1)
                    else:
                        # Le deuxième reste aux buts
                        remi_obj.defense_passive(robot, ball, zone_def, err, vitesse, marge, seuil_ball, "back", cote, 0.2)

                elif elapsed > 30 and elapsed < 240:
                    # Après 30 secondes : Attaque normale
                    if role == "front":
                        # Tir premier poteau (y = 0.3 ou -0.3 selon le côté)
                        but_adv = (-0.9 * cote, 0.25 * yposition) 
                        #########################remi_obj.attaque(robot, ball, but_adv, offset=0.1)
                    else:
                        # Le deuxième reste aux buts
                        remi_obj.defense_passive(robot, ball, zone_def, err, vitesse, marge, seuil_ball, "back", cote, 0.2)

        except Exception as e:
            print(f"Erreur robot {robot_id}: {e}")
        
        time.sleep(0.05) # Petite pause pour ne pas saturer le CPU

# ====================================================== #
# ================= LANCEMENT MATCH ===================== #
# ====================================================== #

if __name__ == "__main__":
    with rsk.Client() as client:
        game = GameManager(client)
        game.choisir_couleur()
        Remi = remi(client)

        if game.couleur == "green":
            r1, r2 = client.green1, client.green2
        else:
            r1, r2 = client.blue1, client.blue2

        params = {
            "vitesse": 3.0,
            "err": 0.05,
            "seuil_ball": 0.15,
            "start_time": time.time()
        }

        t1 = threading.Thread(target=controle_robot, args=(Remi, r1, "1", game, params["vitesse"], params["err"], 0.3, params["seuil_ball"], "front", params["start_time"]), daemon=True)
        t2 = threading.Thread(target=controle_robot, args=(Remi, r2, "2", game, params["vitesse"], params["err"], 0.2, params["seuil_ball"], "back", params["start_time"]), daemon=True)

        t1.start()
        t2.start()

        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            print("\nArrêt.")