import time
import rsk
from robot_agent import RobotAgent
from field_utils import FieldUtils
import config

def main():
    print("Démarrage de la stratégie d'attaque combinée (Version Corrigée)...")
    
    with rsk.Client() as client:
        # CIBLE : Assurez-vous que config.GOAL_X est bon (-1.83 ou 1.83)
        but_adverse = (config.GOAL_X, 0.0)
        
        # On définit un sens de jeu (+1 vers droite, -1 vers gauche)
        # Cela sert pour l'offset de profondeur
        sens_jeu = 1 if config.GOAL_X > 0 else -1

        agent1 = RobotAgent(client.green1, but_adverse, "Green 1")
        agent2 = RobotAgent(client.green2, but_adverse, "Green 2")
        
        try:
            while True:
                ball = client.ball
                if ball is None:
                    time.sleep(0.05); continue

                # --- 1. QUI EST L'ATTAQUANT ? ---
                d1 = FieldUtils.dist(client.green1.position, ball)
                d2 = FieldUtils.dist(client.green2.position, ball)

                if d1 < d2:
                    attaquant = agent1
                    receveur = agent2
                else:
                    attaquant = agent2
                    receveur = agent1

                # --- 2. ANALYSE DE LA SITUATION ---
                pos_att = attaquant.robot.position
                pos_rec = receveur.robot.position
                
                # A. Distances au but
                dist_att_but = FieldUtils.dist(pos_att, but_adverse)
                dist_rec_but = FieldUtils.dist(pos_rec, but_adverse)
                
                # B. Condition "Copain devant" (Universelle)
                # Le copain est devant s'il est plus proche du but que moi
                # On ajoute une petite marge (0.10m) pour éviter les hésitations
                copain_est_devant = dist_rec_but < (dist_att_but - 0.10)

                # C. Calcul du point de passe
                # On met le point X mètres devant le receveur, DANS LE SENS DU JEU
                offset_x = config.PASS_DEPTH_OFFSET * sens_jeu
                
                # On clamp (limite) pour ne pas viser hors du terrain
                target_x = pos_rec[0] + offset_x
                # Limite terrain (ex: max 1.7 ou min -1.7)
                if sens_jeu > 0: target_x = min(target_x, 1.7)
                else:            target_x = max(target_x, -1.7)
                
                point_de_passe = (target_x, pos_rec[1])

                # D. Décision finale
                should_pass = (dist_att_but > config.DIST_SHOOT_LIMIT) and copain_est_devant

                # --- 3. EXÉCUTION ---
                
                if should_pass:
                    # >>> MODE PASSE <<<
                    # print(f"Passe à {receveur.name} (DistBut: {dist_att_but:.2f})", end='\r')
                    
                    # Action Attaquant
                    attaquant.set_target(point_de_passe)
                    attaquant.set_kick_power(config.POWER_PASS)
                    
                    # Action Receveur (Va au point de passe)
                    angle_vers_balle = FieldUtils.angle(pos_rec, ball)
                    receveur.robot.goto((point_de_passe[0], point_de_passe[1], angle_vers_balle), wait=False)
                    receveur.nav_state = navigation.AvoidanceState() # Reset nav receveur
                    
                else:
                    # >>> MODE FRAPPE <<<
                    # print(f"Frappe de {attaquant.name} (Copain pas devant)", end='\r')
                    
                    # Action Attaquant
                    attaquant.set_target(but_adverse)
                    attaquant.set_kick_power(config.POWER_SHOOT)
                    
                    # Action Receveur (IMPORTANT : NE DOIT PAS RESTER IMMOBILE)
                    # Si je ne reçois pas, je me place en retrait ou je suis l'action
                    # Exemple : Je me mets 50cm derrière l'attaquant (soutien) ou je reste sur place en regardant la balle
                    # Ici : Il regarde la balle pour être prêt
                    angle_vers_balle = FieldUtils.angle(pos_rec, ball)
                    # On lui dit de rester où il est mais de regarder la balle (correction d'angle)
                    receveur.robot.goto((pos_rec[0], pos_rec[1], angle_vers_balle), wait=False)
                    # OU Optionnel : Le faire avancer un peu parallèlement (décommenter ci-dessous)
                    # receveur.robot.goto((pos_att[0] - 0.5*sens_jeu, pos_att[1] + 0.3, 0), wait=False)

                # Mise à jour physique de l'attaquant
                attaquant.update_state(ball)

                # Debug console (pour comprendre pourquoi ça échoue)
                # Affiche : Dist_But_Att | Copain_Devant? | Should_Pass?
                # print(f"D_But:{dist_att_but:.1f}m | CopainDevant:{copain_est_devant} | PASS:{should_pass}", end='\r')

                time.sleep(config.LOOP_DT)

        except KeyboardInterrupt:
            print("\nArrêt du programme.")

if __name__ == "__main__":
    import navigation 
    main()