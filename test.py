import rsk
from rsk import constants
from math import sin, cos, tan, sqrt, atan2, pi

class Jules:
    def __init__(self, client):
        self.client = client
        
    def Spot_shoot(self, robot):        
        seuil = 0.15  # Distance à laquelle le robot s'arrête avant la balle
        B = self.client.ball
        R = robot.position
        if B[0] < R[0]:  # Si la balle est devant le robot (côté gauche du terrain)
            arrived = False
            while not arrived:
                B = self.client.ball
                R = robot.position  # Met à jour la position du robot
                D = (B[0] - R[0], B[1] - R[1])
                s = sqrt(D[0]**2 + D[1]**2)  # Distance actuelle à la balle
                dy = B[1]  # Différence sur l'axe Y (vers les cages)
                dx = constants.field_length / 2 + B[0]  # Différence sur l'axe X
                O = atan2(dy, dx) - pi  # Angle pour tirer vers les cages
                    
                if s < seuil:  # Si le robot est suffisamment proche de la balle
                    robot_1_arrived = robot.goto((R[0], R[1], O), wait=False)
                    robot.kick(1)  # Tirer
                    arrived =robot_1_arrived
                     
                else:
                    robot_1_arrived = robot.goto((B[0], B[1], O), wait=False)
                      


with rsk.Client() as client:
    jules = Jules(client)
    jules.Spot_shoot(client.green1) 
                        
