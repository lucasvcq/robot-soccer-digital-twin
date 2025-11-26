import math
import time
from math import pi
import rsk
from field_utils import FieldUtils
from around_planner import AroundPlanner
import config  # Assurez-vous que config.py contient vos constantes

class RobotAgent:
    def __init__(self, robot, goal, name):
        self.robot = robot  # L'objet rsk (ex: client.green1)
        self.goal = goal    # Tuple (x, y) ou Position du coéquipier/but
        self.name = name

        # État interne du robot
        self.is_going_around = False
        self.around_start_time = 0.0
        self.around_side = 0  # -1=gauche, +1=droite

    def distance_to_ball(self, ball):
        return FieldUtils.dist(self.robot.position, ball)

    def calc_kick_strength(self, distance, d_max):
        """
        Calcule la force de frappe (entre 0 et 1) en fonction de la distance.
        """
        d_min = 0.01

        # Si la cible est plus loin que d_max, puissance max (1.0)
        if distance >= d_max:
            return 1.0
        
        # Sécurité pour éviter les divisions par zéro
        if distance <= d_min:
            return 0.1 # Touchette minimale

        # Interpolation linéaire
        kick = (distance - d_min) / (d_max - d_min)
        
        # Bornage strict entre 0.0 et 1.0
        return max(0.0, min(1.0, kick))
    
    def needs_around(self, ball):
        """Décision : CE robot a-t-il besoin de contourner ?"""
        robot_pos = self.robot.position
        
        u_rg = FieldUtils.unit_vector(robot_pos, self.goal)
        v_rb = (ball[0] - robot_pos[0], ball[1] - robot_pos[1])
        d = FieldUtils.dist(robot_pos, ball)
        dot = v_rb[0]*u_rg[0] + v_rb[1]*u_rg[1]
        
        # Angle entre le vecteur Robot->Balle et Robot->But
        angle_rb_deg = abs(math.degrees(FieldUtils.wrap(
            FieldUtils.angle(robot_pos, ball) - FieldUtils.angle(robot_pos, self.goal)
        )))
        
        # Cas 1 : Robot clairement entre balle & but -> Priorité absolue (Reculer/Contourner)
        if FieldUtils.is_robot_between_ball_and_goal(robot_pos, ball, self.goal, angle_threshold_deg=config.BETWEEN_ANGLE_THRESH_DEG):
            return True

        # Cas 2 : Balle bien devant, alignée -> Pas besoin de contourner
        if (dot > config.FRONT_DOT) and (angle_rb_deg < config.FRONT_ANGLE_DEG):
            return False

        # Cas 3 : Balle sur le côté ou très mal alignée -> Contourner
        if (dot < 0) or (angle_rb_deg > config.SIDE_ANGLE_DEG):
            return True

        # Cas 4 : Balle trop proche avec mauvais angle -> Prudence
        if (d < config.DIST_CLOSE) and ((dot < 0.2) or (angle_rb_deg > 45.0)):
            return True

        return False

    def _start_around(self, ball):
        """Initialise le contournement (choix du côté)."""
        if self.is_going_around: 
            return

        rpos = self.robot.position
        wp_left = AroundPlanner.compute_around_waypoint(ball, self.goal, side=-1)
        wp_right = AroundPlanner.compute_around_waypoint(ball, self.goal, side=+1)
        
        # On choisit le côté le plus proche
        if FieldUtils.dist(rpos, wp_left) <= FieldUtils.dist(rpos, wp_right):
            self.around_side = -1 # Gauche
            side_str = "left"
            first_wp = wp_left
        else:
            self.around_side = 1 # Droite
            side_str = "right"
            first_wp = wp_right

        self.is_going_around = True
        self.around_start_time = time.time()
        print(f"[{self.name}] Début contournement par la {side_str}.")
        
        try:
            self.robot.goto((first_wp[0], first_wp[1], -pi), wait=False)
        except Exception as e:
            print(f"[{self.name}] goto(around_wp) a échoué: {e}")
            self.is_going_around = False
            self.around_side = 0

    def _stop_around(self, reason=""):
        """Termine le contournement."""
        if self.is_going_around:
            print(f"[{self.name}] Fin contournement. Raison: {reason}")
            self.is_going_around = False
            self.around_start_time = 0.0
            self.around_side = 0
            time.sleep(0.05) # Petite pause pour stabiliser

    def update_state(self, ball):
        """Machine à états de l'agent. Appelée à chaque boucle."""

        rpos = self.robot.position
        rtheta = self.robot.orientation
        
        # Point cible derrière la balle
        behind = FieldUtils.behind_point(ball, self.goal, config.ALIGN_DISTANCE)
        d_to_behind = FieldUtils.dist(rpos, behind)

        # --- ÉTAT 1: EN COURS DE CONTOURNEMENT ---
        if self.is_going_around:
            # 1a. Timeout ?
            elapsed = time.time() - self.around_start_time
            if elapsed > config.AROUND_TIMEOUT:
                self._stop_around(f"Timeout ({elapsed:.1f}s)")
                return False 

            # 1b. Le chemin s'est-il libéré ?
            if not self.needs_around(ball):
                self._stop_around("Chemin dégagé")
                return False 
            
            # 1c. Continuer vers le waypoint dynamique
            current_target_wp = AroundPlanner.compute_around_waypoint(ball, self.goal, side=self.around_side)
            try:
                self.robot.goto((current_target_wp[0], current_target_wp[1], -pi), wait=False)
            except:
                pass
            return False 

        # --- ÉTAT 2: ARRIVÉ À DESTINATION (ALIGNEMENT & TIR) ---
        if d_to_behind <= config.AROUND_ARRIVAL_THRESH:
            
            # S'assurer qu'on n'est plus en mode contournement
            self._stop_around("Arrivé derrière")

            # 2a. Orientation
            desired_theta = FieldUtils.angle(rpos, self.goal)
            ang_err = FieldUtils.wrap(desired_theta - rtheta)
            
            if abs(ang_err) > config.ANGLE_TOL:
                #print(f"[{self.name}] Orientation (err {math.degrees(ang_err):.1f}°)")
                self.robot.goto((rpos[0], rpos[1], desired_theta), wait=True)
                time.sleep(0.05) 
                return False
            
            # 2b. Approche finale
            d_to_ball = FieldUtils.dist(rpos, ball)
            if d_to_ball > config.CAPTURE_DISTANCE:
                u_rg = FieldUtils.unit_vector(rpos, self.goal)
                target_pos = (ball[0] - u_rg[0]*0.02, ball[1] - u_rg[1]*0.02, desired_theta)
                self.robot.goto(target_pos, wait=True)
                return False 
            
            # 2c. TIR (Puissance Variable)
            if d_to_ball <= config.CAPTURE_DISTANCE and abs(ang_err) <= config.ANGLE_TOL:
                try:
                    # Calcul de la distance vers l'objectif (Passe ou But)
                    dist_to_target = FieldUtils.dist(rpos, self.goal)
                    
                    # Distance max pour force max (ex: 3m). 
                    # Vous pouvez mettre cette valeur dans config.KICK_MAX_DIST
                    max_kick_dist = getattr(config, 'KICK_MAX_DIST', 3.0) 
                    
                    power = self.calc_kick_strength(dist_to_target, max_kick_dist)
                    
                    print(f"[{self.name}] KICK! (Dist={dist_to_target:.2f}m -> Power={power:.2f})")
                    self.robot.kick(power=power)
                    return True 
                except rsk.ClientError as e:
                    print(f"[{self.name}] Erreur kick: {e}")
            
            return False 

        # --- ÉTAT 3: DÉCISION DE NAVIGATION ---
        # On n'est ni en train de contourner, ni arrivé.
        if self.needs_around(ball):
            self._start_around(ball)
        else:
            # Chemin libre, on fonce au point "behind"
            try:
                self.robot.goto((behind[0], behind[1], -pi), wait=False)
            except:
                pass

        return False