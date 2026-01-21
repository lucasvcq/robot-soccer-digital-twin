import rsk 
import math
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

   
    def Pass_vers_objectif(self,robot1,robot2,objectif,terrain):
        D1 = self.Formule.distance_ball(robot1) # Distance balle-robot1
        D2 = self.Formule.distance_ball(robot2) # Distance balle-robot2

        if D1 > D2:
            receveur = robot1
            passeur = robot2
        else:
            receveur = robot2
            passeur = robot1

        self.Formule.Pass_objectif(passeur,objectif)
        self.Formule.suivre_balle(receveur,terrain)
        self.Formule.Spot_shoot(receveur,terrain)


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
            # On est dans notre camp
            if B[0] * zone_defense[0] > 0:
                # On construit une attaque (passe)
                self.Pass_vers_objectif(Notre_robot1, Notre_robot2,(-0.4,0.4),terrain)
            
            # On est dans leur camp
            else:
                # On tire au but avec le robot le plus proche
                self.Tire_vers_le_but(closest_friendly, terrain)

        # Cas : L'adversaire est plus proche 
        else:
            # On est dans notre camp
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
            
            # On est dans leur camp
            else: 
                self.Pass_vers_objectif(Notre_robot1, Notre_robot2, (-0.4,0.4), terrain)

    def Aucun_adversaire(self, N_robot1, N_robot2,terrain):
        d1 = self.Formule.distance_ball(N_robot1)
        d2 = self.Formule.distance_ball(N_robot2)
        if d1 < d2 :
            self.Tire_vers_le_but(N_robot1,terrain)
        else : 
            self.Tire_vers_le_but(N_robot2,terrain)


with rsk.Client() as client:
    Action = action(client)
    Remi = remi(client)