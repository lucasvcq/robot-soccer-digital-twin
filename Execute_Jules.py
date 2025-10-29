import rsk 
from rsk import constants 
import math 
from math import sin, cos, tan, sqrt, atan2, pi , degrees
from Jules import formule

class Jules: 
    def __init__(self, client): 
        self.client = client 
        
    def Spot_shoot(self, robot): 
        Formule = formule(self.client)

        B = self.client.ball # Position de la balle
        R = robot.position # Position du robot 

        A = Formule.Orientation_ball(R) # Angle du robot au départ par rapport à l'horizontal
        O = Formule.Orientation_but() # Angle pour tirer dans les but par rapport à l'horizontal
        
        Formule.Placement_vers_but(robot,A,O)
        robot.goto((B[0],B[1],O-pi)) # Une fois placé on avance et on tire
        robot.kick(1)

    def Pass(self):
        Formule = formule(self.client)
        B = self.client.ball # Position de la balle
        P1 = client.green1.position # Position du robot 1
        P2 = client.green2.position # Position du robot 2

        D1 = Formule.distance_ball(client.green1)
        D2 = Formule.distance_ball(client.green2)

        if D1 > D2 :
            A = Formule.Angle_Robot(client.green2)
            O = Formule.Orientation_ball(P1) 
            Formule.Placement_vers_objectif(client.green2,A,O)
            client.green2.goto((B[0],B[1],O))
            client.green2.kick(1)



with rsk.Client() as client: 
    jules = Jules(client)
    jules.Pass() 
    #jules.Spot_shoot(client.green1)
