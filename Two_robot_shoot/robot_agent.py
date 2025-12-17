import math
import rsk
from field_utils import FieldUtils
import config
import navigation  # <--- IMPORT IMPORTANT

class RobotAgent:
    def __init__(self, robot, goal, name):
        self.robot = robot
        self.goal = goal
        self.name = name

        # On remplace toutes les vieilles variables d'état par celle-ci :
        self.nav_state = navigation.AvoidanceState()

    def update_state(self, ball):
        rpos = self.robot.position
        rtheta = self.robot.orientation

        # 1. NAVIGATION MACRO (Approche rapide)
        # Renvoie True dès qu'on est à < 6cm
        is_in_zone = navigation.aller_derriere_balle(
            self.robot, ball, self.goal, self.nav_state
        )

        if not is_in_zone:
            return False

        # 2. ORIENTATION (Correction précise)
        # Le robot s'arrête et corrige son angle
        if self._handle_orientation(rpos, rtheta):
            return False

        # 3. TIR ET APPROCHE FINALE
        # C'est ici qu'on corrige le "mal centré" : le robot va avancer doucement vers la balle
        return self._handle_kick(ball, rpos, rtheta)
    
    def _handle_orientation(self, rpos, rtheta):
        """Oriente le robot vers le but si nécessaire."""
        desired_theta = FieldUtils.angle(rpos, self.goal)
        ang_err = FieldUtils.wrap(desired_theta - rtheta)

        if abs(ang_err) > config.ANGLE_TOL:
            # On tourne sur place
            self.robot.goto((rpos[0], rpos[1], desired_theta), wait=True)
            return True # On est occupé à tourner
        return False

    def _handle_kick(self, ball, rpos, rtheta):
        """Phase finale : approche et tir."""
        d_to_ball = FieldUtils.dist(rpos, ball)
        desired_theta = FieldUtils.angle(rpos, self.goal)
        ang_err = FieldUtils.wrap(desired_theta - rtheta)

        # Approche finale (les derniers centimètres)
        if d_to_ball > config.CAPTURE_DISTANCE:
            u_rg = FieldUtils.unit_vector(rpos, self.goal)
            target_pos = (ball[0] - u_rg[0]*0.02, ball[1] - u_rg[1]*0.02, desired_theta)
            self.robot.goto(target_pos, wait=True)
            return False

        # Tir
        if d_to_ball <= config.CAPTURE_DISTANCE and abs(ang_err) <= config.ANGLE_TOL:
            try:
                print(f"[{self.name}] KICK !")
                self.robot.kick()
                # On reset l'état de navigation après un tir au cas où
                self.nav_state = navigation.AvoidanceState()
                return True
            except rsk.ClientError as e:
                print(f"[{self.name}] Erreur kick: {e}")
        return False