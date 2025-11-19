import rsk 
from rsk import constants 
import math 
from math import sin, cos, tan, sqrt, atan2, pi , degrees
from Jules import formule

class Jules: 
    def __init__(self, client): 
        self.client = client 
        
    def test(self):
        Formule = formule(client)
        arrived =False
        while not arrived: 
            xr,yr = Formule.rapprochement_passeur(client.green1,0.6)
            robot1 = client.green1.goto((xr,yr,0), avoid_obstacles=True, wait=False)
            robot2 = client.green2.goto((-0.5,-0.5,0), wait = False)
            arrived = robot1 and robot2



with rsk.Client() as client: 
    jules = Jules(client)
    jules.test()