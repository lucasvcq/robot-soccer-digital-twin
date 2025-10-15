import rsk
from rsk import constants
from math import sin,cos,tan,sqrt,atan2, pi

class Jules:
    def __init__(self, client):
        self.client = client

    def Spot_shoot(self, robot):
        R = robot.position  #Récupère la position du robot
        B = self.client.ball  # Récupère la position de la balle
        o = atan2((B[1]-R[1]),(B[0]-R[0]))
        s = 0.0
        S = (B[0]-s, B[1], o)  # (x, y, orientation) - orientation à 0 par défaut
        robot.goto(S) # Déplace le robot vers la balle


with rsk.Client() as client:
    jules = Jules(client)
    jules.Spot_shoot(client.green1)  # Utilise le robot vert 1
    client.green1.kick()