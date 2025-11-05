import rsk 
import math 
from math import sin, cos, tan, sqrt, atan2, pi
from rsk import constants

class formule:
    def __init__(self, client):
        self.client = client

    def distance_ball(self, robot): # Distance entre le robot et la balle
        R = robot.position  
        B = self.client.ball 
        D = (R[0] - B[0], R[1] - B[1])
        return sqrt(D[0]**2 + D[1]**2)
    
    def distance_ball_objectif(self,objectif): # Distance entre la balle et l'objectif
        B = self.client.ball
        PO = objectif
        D =(PO[0] - B[0],PO[1]-B[1])
        return sqrt(D[0]**2 + D[1]**2)
    
    def distance_objectif_objectif(self,objectif1,objectif2):
        PO1 = objectif1
        PO2 = objectif2
        D =(PO1[0] - PO2[0],PO1[1]-PO2[1])
        return sqrt(D[0]**2 + D[1]**2)

    def Angle_but(self):  # Angle entre l'axe des x et la balle
        B = self.client.ball
        dx = constants.field_length / 2 + B[0]  # distance en x entre les cages et la balle
        dy = B[1] # distance en y entre le milieu des cages et la balle
        O = atan2(dy,dx)  
        return O
    
    def Angle_vecteur_balle_objectif(self,Objectif): # Angle du vecteur balle-objectif par rapport à l'horizontal
        B = self.client.ball
        dx = Objectif[0] - B[0] # distance en x entre l'objectif et la balle
        dy = Objectif[1] - B[1] # distance en y entre l'objectif et la balle
        O = atan2(dy,dx)
        return O

# Fonction qui cré des points autour de la balle formant un arc de cercle, pour l'éviter et se positionner vers l'objectif    
    def Placement_vers_objectif(self,robot,Angle_robot,Objectif):
        B = self.client.ball
        rayon = 0.2 # rayon de l'arc de cercle
        steps = 5 # Nombre de points créés pour éviter la balle
        d = Objectif - Angle_robot
        delta_angle = self.normalize_angle(d)
        for i in range (steps + 1):
                AB = Angle_robot + (i / steps)*(delta_angle) # Angle des points positionné sur le cercle 
                x = B[0] + rayon*math.cos((AB)) # Génération des coordonnées des points intermediaire pour atteindre la position finale
                y = B[1] + rayon*math.sin((AB))
                robot.goto((x,y,Objectif-pi))  # Déplacement jusqu'au point souhaité


    def normalize_angle(self,angle):
    #Ramène un angle dans l'intervalle [-pi, pi]
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    def calc_kick_strength(self,distance, d_min, d_max):     #Calcule la force de frappe (entre 0 et 1) en fonction de la distance.
        if distance <= d_min:  #d_min : distance minimale pour une passe douce
            return 0.0
        elif distance >= d_max:     #d_max : distance maximale pour une frappe forte
            return 1.0
    # Interpolation linéaire
        kick = round((distance - d_min) / (d_max - d_min),1)
        return kick

    