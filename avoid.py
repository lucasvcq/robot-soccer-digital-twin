from math import sqrt, cos, sin

class avoid:
    def __init__(self, client):
        self.client = client

    def distance_ball(self, robot):
        C = robot.position
        B = self.client.ball
        D = (C[0] - B[0], C[1] - B[1])
        return sqrt(D[0]**2 + D[1]**2)

    def vecteur_ball(self, robot):
        C = robot.position
        B = self.client.ball
        return (B[0] - C[0], B[1] - C[1])  # vecteur vers la balle

    def vecteur_robot(self, robot):
        """Vecteur vers la balle dans le repère du robot"""
        vx_terrain, vy_terrain = self.vecteur_ball(robot)
        theta = robot.orientation
        vx = cos(theta) * vx_terrain + sin(theta) * vy_terrain
        vy = -sin(theta) * vx_terrain + cos(theta) * vy_terrain
        norme = (vx**2 + vy**2)**0.5
        if norme != 0:
            vx_robot = (vx / norme)
            vy_robot = (vy / norme)
        else:
            vx_robot, vy_robot = 0, 0
        return (vx_robot, vy_robot)