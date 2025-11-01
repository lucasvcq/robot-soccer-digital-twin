import rsk 
from rsk import constants 
import math 
from math import sin, cos, tan, sqrt, atan2, pi , degrees
from Jules import formule

class Jules: 
    def __init__(self, client): 
        self.client = client 
        
    def Spot_shoot(self, robot): 
        robot.goto((0,0,pi))
        print(pi)
     


with rsk.Client() as client: 
    jules = Jules(client)
    jules.Spot_shoot(client.green1)