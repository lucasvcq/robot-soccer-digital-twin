import rsk 
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

    def distance_ball(self, robot):
        R = self.position_robot(robot)  
        B = self.position_ball()  
        D = (R[0] - B[0], R[1] - B[1])
        return sqrt(D[0]**2 + D[1]**2)
    
    def angle_kick(self, robot):
        R = self.position_robot(robot)  
        B = self.position_ball() 
        dy = (B[1])              
        dx = (constants.field_length/2 + B[0])           
        return atan2(dy, dx) - pi  
