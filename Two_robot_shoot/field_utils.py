import math
from rsk import constants

class FieldUtils:
    MAX_X = constants.field_length / 2.0
    MIN_X = -constants.field_length / 2.0
    MAX_Y = constants.field_width / 2.0
    MIN_Y = -constants.field_width / 2.0

    @staticmethod
    def dist(a, b):
        return math.hypot(a[0]-b[0], a[1]-b[1])

    @staticmethod
    def unit_vector(a, b):
        dx, dy = b[0]-a[0], b[1]-a[1]
        d = math.hypot(dx, dy)
        return (1.0, 0.0) if d < 1e-9 else (dx/d, dy/d)

    @staticmethod
    def angle(a, b):
        return math.atan2(b[1]-a[1], b[0]-a[0])

    @staticmethod
    def wrap(a):
        return (a + math.pi) % (2*math.pi) - math.pi

    @staticmethod
    def clamp(point):
        x = min(max(point[0], FieldUtils.MIN_X + 0.01), FieldUtils.MAX_X - 0.01)
        y = min(max(point[1], FieldUtils.MIN_Y + 0.01), FieldUtils.MAX_Y - 0.01)
        return (x, y)

    @staticmethod
    def behind_point(ball, goal, distance):
        u = FieldUtils.unit_vector(ball, goal)
        return (ball[0] - u[0]*distance, ball[1] - u[1]*distance)

    @staticmethod
    def is_robot_between_ball_and_goal(robot_pos, ball, goal, angle_threshold_deg=20):
        """
        Détecte si le robot est *entre* la balle et le but.
        """
        u_rg = FieldUtils.unit_vector(robot_pos, goal)   # robot -> goal (unitaire)
        v_rb = (ball[0] - robot_pos[0], ball[1] - robot_pos[1])  # robot -> ball
        dot = v_rb[0]*u_rg[0] + v_rb[1]*u_rg[1]
        # angle entre robot->ball et robot->goal (0..180)
        angle_rb = abs(math.degrees(FieldUtils.wrap(FieldUtils.angle(robot_pos, ball) - FieldUtils.angle(robot_pos, goal))))
        # on considère "between" si dot négatif et angle proche de 180
        return (dot < 0.0) and (angle_rb > (180.0 - angle_threshold_deg))