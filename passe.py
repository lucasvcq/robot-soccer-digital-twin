import time
import math
import rsk

class TeamAI:
    def __init__(self, client, team_color="green", update_rate=0.05):
        self.client = client
        self.team_color = team_color
        self.update_rate = update_rate
        self.running = True
        self.robots = self.client.robots[team_color]

        self.goal_pos = (1.0, 0.0) if team_color=="green" else (-1.0, 0.0)
        self.linear_speed = 0.3
        self.angular_speed = 3.0  # rad/s

        # Pour suivre l'état du robot
        self.current_target = {}  # robot_id -> target_pos

    def distance(self, pos1, pos2):
        return math.hypot(pos1[0]-pos2[0], pos1[1]-pos2[1])

    def angle_diff(self, current, target):
        diff = target - current
        while diff > math.pi:
            diff -= 2*math.pi
        while diff < -math.pi:
            diff += 2*math.pi
        return diff

    def closest_robot_to_ball(self):
        ball_pos = self.client.ball[:2]
        closest_robot = None
        min_dist = float("inf")
        for r in self.robots.values():
            d = self.distance(r.position[:2], ball_pos)
            if d < min_dist:
                min_dist = d
                closest_robot = r
        return closest_robot

    def closest_teammate(self, robot):
        min_dist = float("inf")
        closest = None
        for r in self.robots.values():
            if r == robot:
                continue
            d = self.distance(r.position[:2], robot.position[:2])
            if d < min_dist:
                min_dist = d
                closest = r
        return closest

    def control_robot_towards(self, robot, target_pos):
        # Angle vers la cible
        rx, ry = robot.position[:2]
        angle_to_target = math.atan2(target_pos[1]-ry, target_pos[0]-rx)
        angle_error = self.angle_diff(robot.orientation, angle_to_target)

        # Rotation proportionnelle
        omega = max(-self.angular_speed, min(self.angular_speed, 5*angle_error))

        # Avancer si orienté presque vers la cible
        distance = self.distance(robot.position[:2], target_pos)
        vx = self.linear_speed if abs(angle_error) < 0.2 else 0.0

        # Envoyer commandes
        robot.control(vx, 0.0, omega)

    def run(self):
        while self.running:
            # Robot le plus proche de la balle
            robot = self.closest_robot_to_ball()
            if robot is None:
                time.sleep(self.update_rate)
                continue

            # 1) Se diriger vers la balle
            self.control_robot_towards(robot, self.client.ball[:2])

            # 2) Si proche de la balle, tir vers le but
            if self.distance(robot.position[:2], self.client.ball[:2]) < 0.05:
                robot.kick()
                # 3) Passe au coéquipier le plus proche
                teammate = self.closest_teammate(robot)
                if teammate:
                    self.control_robot_towards(robot, teammate.position[:2])
                    if self.distance(robot.position[:2], teammate.position[:2]) < 0.05:
                        robot.kick()

            time.sleep(self.update_rate)

# Exemple d’utilisation
if __name__ == "__main__":
    with rsk.Client() as client:
        ai = TeamAI(client, team_color="green")
        print("AI actif : robot le plus proche de la balle tire et passe")
        ai.run()
