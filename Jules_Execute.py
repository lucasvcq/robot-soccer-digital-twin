import rsk 
from Jules import formule
from math import sin, cos, tan, sqrt, atan2, pi
import time
import threading

class action :     

    def __init__(self, client):
        self.client = client
        self.Formule = formule(client)    

    def Tire_vers_le_but(self,robot1,robot2):
        D1 = self.Formule.distance_ball(robot1) # Distance balle-robot1
        D2 = self.Formule.distance_ball(robot2) # Distance balle-robot2

        if D1 > D2 :
            self.Formule.Spot_shoot(robot2)

        else:
            self.Formule.Spot_shoot(robot1)

    def Pass_coéquipier(self, robot1, robot2):
        D1 = self.Formule.distance_ball(robot1) # Distance balle-robot1
        D2 = self.Formule.distance_ball(robot2) # Distance balle-robot2

        if D1 > D2 :
            t1 = threading.Thread(
            target = self.Formule.Pass,
            args=(robot1, robot2) # En 1er robot_reçeveur puis en 2ème robot_passeur
            )

            t2 = threading.Thread(
            target = self.Formule.rapprochement_passeur,
            args=(robot1, 0.5) # Robot_reçeveur, distance à laquelle on veut le rapprocher de la balle
            )

            t1.start()
            t2.start()
            t1.join()
            t2.join()

        else :
            t1 = threading.Thread(
            target = self.Formule.Pass,
            args=(robot2, robot1)
            )

            t2 = threading.Thread(
            target = self.Formule.rapprochement_passeur,
            args=(robot2, 0.5)
            )

            t1.start()
            t2.start()
            t1.join()
            t2.join()

    def Pass_vers_objectif(self,robot1,robot2,objectif):
        D1 = self.Formule.distance_ball(robot1) # Distance balle-robot1
        D2 = self.Formule.distance_ball(robot2) # Distance balle-robot2

        if D1 > D2 : 
            t1 = threading.Thread(
            target = self.Formule.Pass_objectif,
            args=(robot2,objectif) # En 1er robot_reçeveur puis en 2ème robot_passeur
            )

            t2 = threading.Thread(
            target = self.Formule.deplacement_objectif,
            args=(robot1, objectif) # Robot_reçeveur, distance à laquelle on veut le rapprocher de la balle
            )

            t1.start()
            t2.start()
            t1.join()
            t2.join()

        else :
            t1 = threading.Thread(
            target = self.Formule.Pass_objectif,
            args=(robot1, objectif)
            )

            t2 = threading.Thread(
            target = self.Formule.deplacement_objectif,
            args=(robot2, objectif)
            )

            t1.start()
            t2.start()
            t1.join()
            t2.join()
        
    def aller_vers_point(self, robot, cible_x, cible_y):
        print(f"Déplacement vers {cible_x}, {cible_y}")
        
        while True:
            # 1. Où est le robot ?
            x_robot = robot.pose[0]
            y_robot = robot.pose[1]
            theta_robot = robot.pose[2] # L'angle du robot

            # 2. Calculer la distance et la direction (Vecteur Global)
            dx = cible_x - x_robot
            dy = cible_y - y_robot
            distance = sqrt(dx**2 + dy**2)

            # --- CONDITION D'ARRÊT (Ton IF) ---
            if distance < 0.2: # Si on est à moins de 10cm
                print("Arrivé à destination !")
                break

            # 3. La formule magique (Rotation de repère)
            # On transforme le vecteur global (dx, dy) en vecteur robot (vx, vy)
            # C'est de la trigonométrie : on tourne le vecteur de l'angle -theta
            vx_local = dx * cos(theta_robot) + dy * sin(theta_robot)
            vy_local = -dx * sin(theta_robot) + dy * cos(theta_robot)

            # --- 4. Vitesse Maximale Constante ---
            VITESSE_CIBLE = 1.0  # Vitesse désirée en m/s (ex: 1.0 c'est très rapide)

            # On calcule la norme (la longueur) du vecteur local
            norme_vecteur = sqrt(vx_local**2 + vy_local**2)

            if norme_vecteur > 0:
                # On "normalise" le vecteur (on le ramène à une longueur de 1)
                # Puis on multiplie par la vitesse cible pour forcer l'allure
                vitesse_x = (vx_local / norme_vecteur) * VITESSE_CIBLE
                vitesse_y = (vy_local / norme_vecteur) * VITESSE_CIBLE
            else:
                vitesse_x = 0
                vitesse_y = 0

            # 5. Envoyer la commande
            robot.control(vitesse_x, vitesse_y, 0)
            
            # Petite pause pour laisser le processeur respirer
            time.sleep(0.05)

        # Fin de la boucle : on stop tout
        robot.control(0, 0, 0)
            


with rsk.Client() as client:
    Action = action(client)
    #Action.aller_vers_point(client.green1,0,0)
    Action.Pass_coéquipier(client.green1, client.green2)
            