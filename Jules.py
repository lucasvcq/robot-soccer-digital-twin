import rsk 
import math 
from math import sin, cos, tan, sqrt, atan2, pi
from rsk import constants

class formule:
    def __init__(self, client):
        self.client = client

    def position_ball(self):
        B = self.client.ball
        return B
    
    def position_robot(self, robot):
        R = robot.position  
        return R

    def distance_ball(self, robot): # Distance entre le robot et la balle
        R = robot.position  
        B = self.client.ball 
        D = (R[0] - B[0], R[1] - B[1])
        return sqrt(D[0]**2 + D[1]**2)
    
    def Orientation_but(self):  # Angle par rapport à l'horizontale pour tirer au milieu des cages
        B = self.client.ball
        dx = constants.field_length / 2 + B[0]  
        dy = B[1] 
        O = atan2(dy,dx) 
        return O
    
    def Orientation_ball(self,Objectif): # Angle par rapport à l'horizontale pour s'orienter vers la balle
        B = self.client.ball
        dx = Objectif[0] - B[0] 
        dy = Objectif[1] - B[1]
        O = atan2(dy,dx)
        return O
    

    def Angle_Robot(self,robot):  # Angle du robot par rapport à l'horizontale 
        R = robot.position  
        dx = constants.field_length / 2 + R[0] 
        dy = R[1] 
        A = atan2(dy,dx)
        return A 

    def Placement_vers_but(self,robot,Angle_robot_balle,Objectif):
        B = self.client.ball
        rayon = 0.2
        steps = 5
        for i in range (steps + 1):
                AB = Angle_robot_balle + (i / steps)*(Objectif - Angle_robot_balle) # Angle des points positionné sur le cercle entre le robot et la balle
                x = B[0] + rayon*math.cos((AB)) # Génération des coordonnées des points intermediaire pour atteindre la position finale
                y = B[1] + rayon*math.sin((AB))
                robot.goto((x,y,Objectif-pi))

    def Placement_vers_objectif(self,robot,Angle_robot,Objectif):
        B = self.client.ball
        rayon = 0.15
        steps = 5
        d = Objectif - Angle_robot
        delta_angle = self.normalize_angle(d)
        for i in range (steps + 1):
                AB = Angle_robot + (i / steps)*delta_angle # Angle des points positionné sur le cercle entre le robot et la balle
                x = B[0] + rayon*math.cos((AB)) # Génération des coordonnées des points intermediaire pour atteindre la position finale
                y = B[1] + rayon*math.sin((AB))
                robot.goto((x,y,Objectif-pi))


    def normalize_angle(self,angle):
    #Ramène un angle dans l'intervalle [-pi, pi]
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    