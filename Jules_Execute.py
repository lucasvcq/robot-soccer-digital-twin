import rsk 
from Jules import formule
from REMI import remi
from math import sin, cos, tan, sqrt, atan2, pi
import threading
import time

class action :     

    def __init__(self, client):
        self.client = client
        self.Formule = formule(client)    

    def Tire_vers_le_but(self,robot,terrain):     
            self.Formule.Spot_shoot(robot,terrain)


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

    def Pass_vers_objectif(self,robot1,robot2,objectif,terrain):
        D1 = self.Formule.distance_ball(robot1) # Distance balle-robot1
        D2 = self.Formule.distance_ball(robot2) # Distance balle-robot2

        if D1 > D2:
            receveur = robot1
            passeur = robot2
        else:
            receveur = robot2
            passeur = robot1

        t1 = threading.Thread(
        target = self.Formule.Pass_objectif,
        args=(passeur,objectif) # En 1er robot_reçeveur puis en 2ème l'objectifr
        )

        t1.start()
        t1.join()
        
        t2 = threading.Thread(
        target = self.Formule.suivre_balle,
        args=(receveur,terrain) # En 1er robot_reçeveur puis en 2ème l'objectifr
        )

        t2.start()
        t2.join()
    
        t3 = threading.Thread(
        target = self.Formule.Spot_shoot,
        args=(receveur,terrain) # En 1er robot_reçeveur puis en 2ème l'objectifr
        )

        t3.start()
        t3.join()

    def supériorité_numérique (self,Notre_robot1,Notre_robot2,Robot_adverse,terrain,zone_defense):    
        B = self.client.ball
        # Calcul des distances
        dist_r1 = self.Formule.distance_ball(Notre_robot1)
        dist_r2 = self.Formule.distance_ball(Notre_robot2)
        dist_adv = self.Formule.distance_ball(Robot_adverse)

        # Identification du robot le plus proche (évite les comparaisons de float plus tard)
        if dist_r1 < dist_r2:
            closest_friendly = Notre_robot1
            dist_min = dist_r1
        else:
            closest_friendly = Notre_robot2
            dist_min = dist_r2

        DEF_SPEED = 0.05
        DEF_TIME = 3.0
        DEF_KP = 0.3
        DEF_KD = 0.15

        # Cas : L'adversaire est plus loin que nous de la balle 
        if dist_min < dist_adv:

            if B[0] * zone_defense[0] > 0:
                # On construit une attaque (passe)
                self.Pass_vers_objectif(Notre_robot1, Notre_robot2,(-0.4,0.4),terrain)
                
            else:
                # On tire au but avec le robot le plus proche
                self.Tire_vers_le_but(closest_friendly, terrain)

        # Cas : L'adversaire est plus proche 
        else:
            
            if B[0] * zone_defense > 0:
                # Le robot le plus proche défend (ou celui qui n'est pas closest ? À vérifier selon ta strat)
                # Note: J'utilise le robot le plus proche pour défendre ici
                Remi.defense_passive(
                    closest_friendly, 
                    self.client.ball, 
                    zone_defense, 
                    DEF_SPEED, DEF_TIME, DEF_KP, DEF_KD, 
                    "front", time.time(), 0.2
                )
                
            else: 
                self.Pass_vers_objectif(Notre_robot1, Notre_robot2, (-0.4,0.4), terrain)

with rsk.Client() as client:
    Action = action(client)
    Remi = remi(client)
