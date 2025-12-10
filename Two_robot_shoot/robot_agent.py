import math
import time
from field_utils import FieldUtils
from around_planner import AroundPlanner
import config
import rsk  # Pour l'exception ClientError


class RobotAgent:
    def __init__(self, robot, goal, name):
        self.robot = robot      # L'objet rsk (ex: client.green1)
        self.goal = goal
        self.name = name

        # État interne du robot
        self.is_going_around = False
        self.around_start_time = 0.0
        self.around_side = 0  # -1=gauche, +1=droite

    # --- Méthodes utilitaires ---
    def distance_to_ball(self, ball):
        return FieldUtils.dist(self.robot.position, ball)

    def _start_around(self, ball):
        """Initialise le contournement autour de la balle."""
        if self.is_going_around:
            return

        rpos = self.robot.position
        wp_left = AroundPlanner.compute_around_waypoint(ball, self.goal, side=-1)
        wp_right = AroundPlanner.compute_around_waypoint(ball, self.goal, side=+1)

        # Choix du côté le plus court
        if FieldUtils.dist(rpos, wp_left) <= FieldUtils.dist(rpos, wp_right):
            self.around_side = -1
            first_wp = wp_left
            side_str = "gauche"
        else:
            self.around_side = 1
            first_wp = wp_right
            side_str = "droite"

        self.is_going_around = True
        self.around_start_time = time.time()

        print(f"[{self.name}] Début contournement par la {side_str}, waypoint={first_wp}")
        try:
            self.robot.goto((first_wp[0], first_wp[1], -math.pi), wait=False)
        except Exception as e:
            print(f"[{self.name}] goto(around_wp) a échoué: {e}")
            self._stop_around("Erreur goto initial")

    def _stop_around(self, reason=""):
        """Termine proprement le contournement."""
        if not self.is_going_around:
            return
        print(f"[{self.name}] Fin contournement. Raison: {reason}")
        self.is_going_around = False
        self.around_start_time = 0.0
        self.around_side = 0

    # --- Machine à états principale ---
    def update_state(self, ball):
        rpos = self.robot.position
        rtheta = self.robot.orientation

        behind = FieldUtils.behind_point(ball, self.goal, config.ALIGN_DISTANCE)
        d_to_behind = FieldUtils.dist(rpos, behind)

        # ÉTAPE 1 : SE PLACER DERRIÈRE LA BALLE
        if d_to_behind > config.AROUND_ARRIVAL_THRESH:
            return self._handle_around(ball, behind, d_to_behind)

        # ÉTAPE 2 : S'ORIENTER VERS LE BUT
        if self._handle_orientation(rpos, rtheta):
            return False

        # ÉTAPE 3 : APPROCHE ET TIR
        return self._handle_kick(ball, rpos, rtheta)

    # --- Sous-étapes de la machine à états ---
    def _handle_around(self, ball, behind, d_to_behind):
        """Gère le placement autour de la balle pour atteindre 'behind'."""
        rpos = self.robot.position

        # Si on ne contourne pas encore → démarrage
        if not self.is_going_around:
            print(f"[{self.name}] (1) Pas aligné (d_to_behind={d_to_behind:.3f}m).")
            self._start_around(ball)
            return False

        # Vérifier timeout
        elapsed = time.time() - self.around_start_time
        if elapsed > config.AROUND_TIMEOUT:
            self._stop_around(f"Timeout ({elapsed:.2f}s)")
            return False

        # Recalcul dynamique du waypoint
        current_wp = AroundPlanner.compute_around_waypoint(ball, self.goal, side=self.around_side)
        try:
            self.robot.goto((current_wp[0], current_wp[1], -math.pi), wait=False)
        except Exception as e:
            self._stop_around(f"Erreur GOTO : {e}")
            return False

        # Vérifier arrivée au waypoint
        if FieldUtils.dist(rpos, current_wp) <= config.AROUND_ARRIVAL_THRESH:
            print(f"[{self.name}] Arrivé au waypoint, passage vers 'behind'.")
            self._stop_around("Waypoint atteint")
            self.robot.goto((behind[0], behind[1], -math.pi), wait=True)
            return False

        return False

    def _handle_orientation(self, rpos, rtheta):
        """Oriente le robot vers le but si nécessaire."""
        desired_theta = FieldUtils.angle(rpos, self.goal)
        ang_err = FieldUtils.wrap(desired_theta - rtheta)

        if abs(ang_err) > config.ANGLE_TOL:
            print(f"[{self.name}] (2) S'oriente (erreur {math.degrees(ang_err):.1f}°)")
            self.robot.goto((rpos[0], rpos[1], desired_theta), wait=True)
            return True
        return False

    def _handle_kick(self, ball, rpos, rtheta):
        """Phase finale : approche et tir."""
        d_to_ball = FieldUtils.dist(rpos, ball)
        desired_theta = FieldUtils.angle(rpos, self.goal)
        ang_err = FieldUtils.wrap(desired_theta - rtheta)

        # Approche finale
        if d_to_ball > config.CAPTURE_DISTANCE:
            print(f"[{self.name}] (3a) Approche finale (d={d_to_ball:.3f}m)")
            u_rg = FieldUtils.unit_vector(rpos, self.goal)
            target_pos = (ball[0] - u_rg[0]*0.02, ball[1] - u_rg[1]*0.02, desired_theta)
            self.robot.goto(target_pos, wait=True)
            return False

        # Tir
        if d_to_ball <= config.CAPTURE_DISTANCE and abs(ang_err) <= config.ANGLE_TOL:
            try:
                print(f"[{self.name}] (3b) KICK !")
                self.robot.kick()
                return True
            except rsk.ClientError as e:
                print(f"[{self.name}] Erreur lors du kick: {e}")
        return False