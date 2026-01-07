import math
import rsk
from field_utils import FieldUtils
import config
import navigation  # <--- IMPORT IMPORTANT

class RobotAgent:
    def __init__(self, robot, goal, name):
        self.robot = robot
        self.goal = goal # Cible par défaut
        self.name = name
        self.nav_state = navigation.AvoidanceState()
        
        # NOUVEAU : Puissance de tir par défaut
        self.kick_power = 1.0 

    # NOUVEAU : Permet de changer la cible en cours de route (But ou Copain)
    def set_target(self, new_target):
        self.goal = new_target
        
    # NOUVEAU : Permet de changer la puissance (Passe douce vs Tir fort)
    def set_kick_power(self, power):
        self.kick_power = power

    def update_state(self, ball):
        # ... (Le début reste identique : navigation vers la balle ...)
        rpos = self.robot.position
        rtheta = self.robot.orientation
        
        is_in_zone = navigation.aller_derriere_balle(
            self.robot, ball, self.goal, self.nav_state
        )

        if not is_in_zone:
            return False

        if self._handle_orientation(rpos, rtheta):
            return False

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
        # ... (Calculs d'approche identiques)
        d_to_ball = FieldUtils.dist(rpos, ball)
        desired_theta = FieldUtils.angle(rpos, self.goal)
        ang_err = FieldUtils.wrap(desired_theta - rtheta)

        # Approche finale
        if d_to_ball > config.CAPTURE_DISTANCE:
            # ... (Code identique)
            u_rg = FieldUtils.unit_vector(rpos, self.goal)
            target_pos = (ball[0] - u_rg[0]*0.02, ball[1] - u_rg[1]*0.02, desired_theta)
            self.robot.goto(target_pos, wait=True)
            return False

        # MODIFICATION DU TIR : Utilisation de la puissance variable
        if d_to_ball <= config.CAPTURE_DISTANCE and abs(ang_err) <= config.ANGLE_TOL:
            try:
                print(f"[{self.name}] KICK (Power={self.kick_power}) !")
                # On utilise la puissance configurée
                self.robot.kick(power=self.kick_power) 
                
                self.nav_state = navigation.AvoidanceState()
                return True
            except rsk.ClientError as e:
                print(f"[{self.name}] Erreur kick: {e}")
        return False