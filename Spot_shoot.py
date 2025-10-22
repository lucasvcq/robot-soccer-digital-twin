import rsk
from rsk import constants
from math import sin, cos, tan, sqrt, atan2, pi
from Formule import formule

class Jules:
    def __init__(self, client):
        self.client = client
        self.f = formule(client)  
        
    def Spot_shoot(self, robot):        
        seuil = 0.2
        B = self.f.position_ball()  
        R = self.f.position_robot(robot) 
        if B[0] < R[0]:
            arrived = False            
            while not arrived: 
                D_B = formule.distance_ball(robot)  
                A = formule.angle(robot)  
                B = self.f.position_ball()  
                R = formule.position_robot(robot)                
                robot_1_arrived = robot.goto((B[0], B[1], A), wait=False)                                 
                if D_B < seuil:                    
                    robot_1_arrived = robot.goto((R[0], R[1], A), wait=False)
                    robot.kick(1)  # Tirer
                    arrived =robot_1_arrived
                else:
                    robot_1_arrived = robot.goto((B[0], B[1], A), wait=False)
        else: 
            seuil_recul = 0.5
            if B[1] <= 0:
                robot.goto((B[0], B[1], 0))
                robot.kick(1)  

             

            

with rsk.Client() as client:
    jules = Jules(client)
    jules.Spot_shoot(client.green1)  
