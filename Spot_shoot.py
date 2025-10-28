import rsk 
from rsk import constants 
import math 
from math import sin, cos, tan, sqrt, atan2, pi , degrees

class Jules: 
    def __init__(self, client): 
        self.client = client 
        
    def Spot_shoot(self, robot): 
        B = self.client.ball # Position de la balle
        R = robot.position # Position du robot 

        # Alpha, Orientation vers le but
        dx = constants.field_length / 2 + B[0]  
        dy = B[1] 
        O = atan2(dy,dx) 
        
        # Angle de départ du robot 
        xd = constants.field_length / 2 + R[0] 
        yd = R[1] 
        A = atan2(yd,xd) 
        
        # Point vers lequel le robot doit aller 
        rayon = 0.2
        xk = B[0] + rayon * math.cos((O)) 
        yk = B[1] + rayon * math.sin((O))


        Og = degrees(O)
        Ag = degrees(A)

        steps = 5
 
        for i in range (steps + 1):
                AB = A + (i / steps)*(O - A)
                x = B[0] + rayon*math.cos((AB))
                y = B[1] + rayon*math.sin((AB))
                robot.goto((x,y,O-pi))
        robot.goto((B[0],B[1],O-pi))
        robot.kick(1)

  



with rsk.Client() as client: 
    jules = Jules(client) 
    jules.Spot_shoot(client.green1)
