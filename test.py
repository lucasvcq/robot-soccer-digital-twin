import rsk
from rsk import constants
import math
from math import sin, cos, tan, sqrt, atan2, pi, degrees

class Jules:
    def __init__(self, client):
        self.client = client

    def Spot_shoot(self, robot):
        B = self.client.ball  # Position de la balle
        R = robot.position    # Position du robot

        # O, Orientation vers le but
        dx = constants.field_length / 2 + B[0]
        dy = B[1]
        O = atan2(dy, dx)

        # A, Angle de départ du robot
        xd = constants.field_length / 2 + R[0]
        yd = R[1]
        A = atan2(yd, xd)

        # Paramètres de contrôle
        rayon = 0.2
        steps = 5
        linear_speed = 0.25  # Vitesse linéaire [m/s]
        angular_speed = 0.5  # Vitesse angulaire [rad/s]

        for i in range(steps + 1):
            AB = A + (i / steps) * (O - A)  # Angle intermédiaire
            x_target = B[0] + rayon * math.cos(AB)
            y_target = B[1] + rayon * math.sin(AB)

            # Calcul de la direction vers le point cible
            dx = x_target - R[0]
            dy = y_target - R[1]
            target_angle = atan2(dy, dx)

            # Calcul de l'erreur d'angle
            angle_error = target_angle - robot.orientation
            angle_error = (angle_error + pi) % (2 * pi) - pi  # Normalisation entre -pi et pi

            # Contrôle du robot
            if abs(angle_error) > 0.1:  # Si l'erreur d'angle est grande, on tourne sur place
                robot.control(0., 0., angular_speed * (1 if angle_error > 0 else -1))
            else:  # Sinon, on avance vers la cible
                robot.control(linear_speed * cos(angle_error), linear_speed * sin(angle_error), 0.)

            # Mise à jour de la position du robot (simulation)
            R = robot.position

        # Dernière étape : aller sur la balle et tirer
        dx = B[0] - R[0]
        dy = B[1] - R[1]
        target_angle = atan2(dy, dx)
        angle_error = target_angle - robot.orientation
        angle_error = (angle_error + pi) % (2 * pi) - pi

        # On s'aligne sur la balle
        while abs(angle_error) > 0.1:
            robot.control(0., 0., angular_speed * (1 if angle_error > 0 else -1))
            angle_error = target_angle - robot.orientation
            angle_error = (angle_error + pi) % (2 * pi) - pi

        # On avance vers la balle
        distance = sqrt(dx**2 + dy**2)
        while distance > 0.05:  # Seuil de distance
            robot.control(linear_speed, 0., 0.)
            R = robot.position
            dx = B[0] - R[0]
            dy = B[1] - R[1]
            distance = sqrt(dx**2 + dy**2)

        # On s'oriente vers le but et on tire
        final_angle = O - pi
        angle_error = final_angle - robot.orientation
        angle_error = (angle_error + pi) % (2 * pi) - pi
        while abs(angle_error) > 0.1:
            robot.control(0., 0., angular_speed * (1 if angle_error > 0 else -1))
            angle_error = final_angle - robot.orientation
            angle_error = (angle_error + pi) % (2 * pi) - pi

        robot.kick(1)

with rsk.Client() as client:
    jules = Jules(client)
    jules.Spot_shoot(client.green1)
