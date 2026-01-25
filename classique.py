import threading
import time
from math import sqrt

classique:
def controle_robot(remi_obj, robot, robot_id, couleur, zone_def, cote, vitesse, err, marge, seuil_ball, role, start_time):
    ball_last_pos = None
    ball_stop_timer = 0
    
    while True:
        try:
            # Vérification si le robot a le droit de bouger (Referee)
            if not remi_obj.can_move(couleur, robot_id):
                time.sleep(0.5)
                continue

            ball = remi_obj.client.ball
            if ball is None: continue

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


def match_classique(Remi, robot1, robot2, couleur, zone_def, cote, start_time):
    r1, r2 = robot1, robot2
    

    params = {
        "vitesse": 3.0,
        "err": 0.05,
        "seuil_ball": 0.15
    }

    t1 = threading.Thread(target=controle_robot, args=(Remi, r1, "1", couleur, zone_def, cote, params["vitesse"], params["err"], 0.3, params["seuil_ball"], "front", start_time), daemon=True)
    t2 = threading.Thread(target=controle_robot, args=(Remi, r2, "2", couleur, zone_def, cote, params["vitesse"], params["err"], 0.2, params["seuil_ball"], "back", start_time), daemon=True)

    t1.start()
    t2.start()

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt.")