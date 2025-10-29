import math
import time
from field_utils import FieldUtils
from around_planner import AroundPlanner
import config  # Importe les constantes
import rsk # Pour l'exception ClientError
from math import pi

class RobotAgent:
    def __init__(self, robot, goal, name):
        self.robot = robot  # L'objet rsk (ex: client.green1)
        self.goal = goal
        self.name = name

        # État interne du robot
        self.is_going_around = False
        self.around_start_time = 0.0
        # NOUVEAU: Mémorise le côté du contournement (-1=gauche, +1=droite)
        self.around_side = 0 

    def distance_to_ball(self, ball):
        return FieldUtils.dist(self.robot.position, ball)
    
    def needs_around(self, ball):
        """Décision améliorée : CE robot a-t-il besoin de contourner ?"""
        robot_pos = self.robot.position
        
        u_rg = FieldUtils.unit_vector(robot_pos, self.goal)
        v_rb = (ball[0] - robot_pos[0], ball[1] - robot_pos[1])
        d = FieldUtils.dist(robot_pos, ball)
        dot = v_rb[0]*u_rg[0] + v_rb[1]*u_rg[1]
        angle_rb_deg = abs(math.degrees(FieldUtils.wrap(FieldUtils.angle(robot_pos, ball) - FieldUtils.angle(robot_pos, self.goal))))
        
        # Diagnostics
        print(f"---- DIAG [{self.name}] ----")
        print(f"angle_rb_deg={angle_rb_deg:.2f} dot={dot:.4f} d_to_ball={d:.3f}")

        # --- CORRECTION : INVERSION DE L'ORDRE ---
        
        # Cas 4 (MAINTENANT CAS 1) : robot clairement entre balle & but
        # C'EST LA PRIORITÉ ABSOLUE.
        if FieldUtils.is_robot_between_ball_and_goal(robot_pos, ball, self.goal, angle_threshold_deg=config.BETWEEN_ANGLE_THRESH_DEG):
            return True

        # Cas 1 (MAINTENANT CAS 2) : balle bien devant, alignée -> pas besoin
        # Ce cas n'est vérifié QUE SI on n'est pas entre la balle et le but.
        if (dot > config.FRONT_DOT) and (angle_rb_deg < config.FRONT_ANGLE_DEG):
            return False

        # Cas 2 (MAINTENANT CAS 3) : balle sur le côté ou très mal alignée -> contourner
        if (dot < 0) or (angle_rb_deg > config.SIDE_ANGLE_DEG):
            return True

        # Cas 3 (MAINTENANT CAS 4) : balle proche -> prudence
        if (d < config.DIST_CLOSE) and ((dot < 0.2) or (angle_rb_deg > 45.0)):
            return True

        # sinon, pas besoin de contourner
        return False

    def _start_around(self, ball):
        """Initialise le contournement."""
        if self.is_going_around: # Déjà en cours
            return

        rpos = self.robot.position
        wp_left = AroundPlanner.compute_around_waypoint(ball, self.goal, side=-1)
        wp_right = AroundPlanner.compute_around_waypoint(ball, self.goal, side=+1)
        
        # On choisit le côté et on le mémorise
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
        print(f"[{self.name}] Début contournement par la {side_str}, premier waypoint={first_wp}")
        
        try:
            # On envoie la *première* commande goto
            self.robot.goto((first_wp[0], first_wp[1], -pi), wait=False)
        except Exception as e:
            print(f"[{self.name}] goto(around_wp) a échoué: {e}")
            self.is_going_around = False # Annuler l'état
            self.around_side = 0

    def _stop_around(self, reason=""):
        """Termine le contournement."""
        print(f"[{self.name}] Fin contournement. Raison: {reason}")
        self.is_going_around = False
        self.around_start_time = 0.0
        self.around_side = 0 # On réinitialise le côté
        time.sleep(0.05) # Petite pause pour stabiliser

    def update_state(self, ball):
        """Machine à états de l'agent. Appelée à chaque boucle."""
        
        rpos = self.robot.position
        rtheta = self.robot.orientation
        
        # Objectif final: être au point "behind"
        behind = FieldUtils.behind_point(ball, self.goal, config.ALIGN_DISTANCE)
        d_to_behind = FieldUtils.dist(rpos, behind)

        # --- ÉTAPE 1: SE PLACER DERRIÈRE LA BALLE ---
        if d_to_behind > config.AROUND_ARRIVAL_THRESH: 
            
            # On n'est pas à notre place. On doit y aller SANS toucher la balle.
            # C'est le travail du "AroundPlanner".
            
            # 1a. Si on ne contourne pas, on choisit un côté.
            if not self.is_going_around:
                wp_left = AroundPlanner.compute_around_waypoint(ball, self.goal, side=-1)
                wp_right = AroundPlanner.compute_around_waypoint(ball, self.goal, side=+1)
                
                # Choisir le waypoint le plus proche du robot pour démarrer
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
                print(f"[{self.name}] (1) Pas aligné (d_to_behind={d_to_behind:.3f}m). Début contournement par la {side_str}.")
                
                # Ordre initial (non-bloquant)
                try:
                    self.robot.goto((first_wp[0], first_wp[1], -pi), wait=False)
                except Exception as e:
                    print(f"[{self.name}] goto(around_wp) a échoué: {e}")
                    self._stop_around("Erreur GOTO")
                
                return False # On attend la prochaine boucle

            # 1b. On est déjà en train de contourner. On met à jour la cible.
            
            # Vérifier le timeout
            elapsed = time.time() - self.around_start_time
            if elapsed > config.AROUND_TIMEOUT:
                self._stop_around(f"Timeout (elapsed={elapsed:.2f}s)")
                return False 
            
            # Recalculer le waypoint dynamique
            current_target_wp = AroundPlanner.compute_around_waypoint(ball, self.goal, side=self.around_side)

            # Envoyer la commande (non-bloquante)
            try:
                self.robot.goto((current_target_wp[0], current_target_wp[1], -pi), wait=False)
            except Exception as e:
                self._stop_around(f"Erreur GOTO Servo")

            # 1c. Est-ce qu'on est arrivé au waypoint?
            # On vérifie si on est arrivé au waypoint *ET* si le chemin vers "behind" est dégagé
            d_to_wp = FieldUtils.dist(rpos, current_target_wp)
            if d_to_wp <= config.AROUND_ARRIVAL_THRESH:
                print(f"[{self.name}] Arrivé au waypoint de contournement. Transition vers 'behind' final.")
                # On arrête le mode "around" pour passer en 'goto(behind)' direct
                self._stop_around("Waypoint atteint")
                # Maintenant on peut y aller, le chemin est dégagé
                self.robot.goto((behind[0], behind[1], -pi), wait=True)
                time.sleep(0.1) # Stabilisation
                return False

            return False # On continue de contourner
        
        # --- ÉTAPE 2: S'ORIENTER (On est au point 'behind') ---
        
        # Si on était en train de contourner, on s'arrête.
        if self.is_going_around:
            self._stop_around(f"Arrivé au point 'behind' (d={d_to_behind:.3f}m)")
            self.robot.goto((rpos[0], rpos[1], rtheta), wait=True) # Stop
            time.sleep(0.1)
            return False

        # On est stabilisé au point "behind"
        desired_theta = FieldUtils.angle(rpos, self.goal)
        ang_err = FieldUtils.wrap(desired_theta - rtheta)
        
        if abs(ang_err) > config.ANGLE_TOL:
            print(f"[{self.name}] (2) S'oriente (err {math.degrees(ang_err):.1f} deg)")
            self.robot.goto((rpos[0], rpos[1], desired_theta), wait=True)
            time.sleep(0.05) 
            return False
            
        # --- ÉTAPE 3: APPROCHE FINALE ET TIR ---
        
        d_to_ball = FieldUtils.dist(rpos, ball)
        
        if d_to_ball > config.CAPTURE_DISTANCE:
            print(f"[{self.name}] (3a) Approche finale (d={d_to_ball:.3f}m)")
            u_rg = FieldUtils.unit_vector(rpos, self.goal)
            target_pos = (ball[0] - u_rg[0]*0.02, ball[1] - u_rg[1]*0.02, desired_theta)
            self.robot.goto(target_pos, wait=True)
            time.sleep(0.02)
            
            # Re-vérifier les conditions après le wait=True
            rpos = self.robot.position
            rtheta = self.robot.orientation
            d_to_ball = FieldUtils.dist(rpos, ball)
            ang_err = FieldUtils.wrap(desired_theta - rtheta)
            
        if d_to_ball <= config.CAPTURE_DISTANCE and abs(ang_err) <= config.ANGLE_TOL:
            try:
                print(f"[{self.name}] (3b) KICK !")
                self.robot.kick()
                u_rg = FieldUtils.unit_vector(rpos, self.goal)
                #self.robot.goto((rpos[0] - u_rg[0]*0.10, rpos[1] - u_rg[1]*0.10, rtheta), wait=True)
                return True 
            except rsk.ClientError as e:
                print(f"[{self.name}] Erreur lors du kick: {e}")
                
        return False