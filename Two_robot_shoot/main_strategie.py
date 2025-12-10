import time
import rsk
from robot_agent import RobotAgent
import config

# --- CONFIGURATION DU TEST ---
ROBOT_ID = 1            # Le robot qui joue (Green 1)
TEAM = 'green'          # Couleur de l'équipe

# Choisissez le mode pour tester la puissance de frappe :
# "GOAL" = Vise le but adverse (Tir fort)
# "PASS" = Vise un coéquipier virtuel proche (Passe douce)
TEST_MODE = "GOAL" 

def main():
    print("Démarrage du client RSK...")
    
    with rsk.Client() as client:
        # 1. Récupération du robot
        if TEAM == 'green':
            robot = client.green1 # ou client.green[ROBOT_ID]
            # Le but adverse est généralement en x positif ou négatif selon le côté.
            # Pour la démo, disons que le but adverse est à droite (x=1.8, y=0)
            enemy_goal = (-1.8, 0.0) 
        else:
            robot = client.blue1
            enemy_goal = (1.8, 0.0)

        # 2. Définition de la cible selon le mode
        if TEST_MODE == "GOAL":
            target = enemy_goal
            target_name = "But Adverse"
        else:
            # On simule un coéquipier situé à une position fixe, pas trop loin du centre
            # Par exemple à (0.5, 0.5). Si le robot est à (-0.5, -0.5), ça fait ~1.4m de distance.
            target = (0.0, 0.0) 
            target_name = "Coéquipier (Centre)"

        # 3. Création de l'agent
        # On lui donne l'objet robot brut et la cible (x,y)
        agent = RobotAgent(robot, target, name=f"Striker-{ROBOT_ID}")

        print(f"--- DÉBUT DU TEST : Mode {TEST_MODE} ---")
        print(f"Cible : {target_name} en {target}")
        print("Observez la console pour voir la puissance de tir (Power).")
        print("------------------------------------------")

        # 4. Boucle principale
        try:
            while True:
                # Récupérer la position de la balle (x, y)
                # client.ball peut être None si la balle n'est pas détectée
                ball_data = client.ball
                
                if ball_data is None:
                    print("Balle non détectée !", end='\r')
                    time.sleep(0.1)
                    continue
                
                # La position de la balle est souvent un tuple (x, y) ou un objet avec .position
                # Adaptez selon votre version de rsk, ici on suppose un tuple (x, y)
                ball_pos = ball_data 

                # --- APPEL DE L'IA ---
                # update_state renvoie True si un tir a été effectué
                did_kick = agent.update_state(ball_pos)

                if did_kick:
                    print(f" >>> ACTION TERMINÉE ! ({TEST_MODE}) <<<")
                    # On attend un peu pour laisser le temps de voir le tir
                    # Ou pour laisser l'arbitre replacer la balle
                    time.sleep(2.0)
                    
                    # Optionnel : Si vous voulez que le robot recule un peu après le tir
                    # robot.goto((robot.position[0]-0.2, robot.position[1], 0))

                time.sleep(0.01) # Petite pause pour ne pas surcharger le CPU

        except KeyboardInterrupt:
            print("\nArrêt du programme.")

if __name__ == "__main__":
    main()