import time
import math
from field_utils import FieldUtils
from around_planner import AroundPlanner
import config

class AvoidanceState:
    def __init__(self):
        self.active = False
        self.start_time = 0.0
        self.side = 0
        # On mémorise la position de la balle au début du contournement
        self.ball_pos_at_start = None 


def aller_derriere_balle(robot, ball, goal, state: AvoidanceState):
    """
    Amène le robot derrière la balle.
    VERSION STABILISÉE : Priorité à la position, l'angle est géré après.
    """
    
    # 1. Calcul de la cible
    target_pos = FieldUtils.behind_point(ball, goal, config.ALIGN_DISTANCE)
    rpos = robot.position
    dist_to_target = FieldUtils.dist(rpos, target_pos)

    # 2. Condition de succès SIMPLIFIÉE
    # On retire la vérification de l'angle ici pour stopper les oscillations.
    # Si on est à moins de 6cm, on considère qu'on est arrivé.
    if dist_to_target <= config.AROUND_ARRIVAL_THRESH:
        state.active = False
        return True

    # 3. Reset dynamique (Si la balle bouge beaucoup)
    if state.active and state.ball_pos_at_start is not None:
        if FieldUtils.dist(state.ball_pos_at_start, ball) > 0.20:
            state.active = False
            state.ball_pos_at_start = None

    # 4. Initialisation (inchangée)
    if not state.active:
        state.active = True
        state.start_time = time.time()
        state.ball_pos_at_start = ball
        
        # Choix du côté
        wp_left = AroundPlanner.compute_around_waypoint(ball, goal, side=-1)
        wp_right = AroundPlanner.compute_around_waypoint(ball, goal, side=+1)
        if FieldUtils.dist(rpos, wp_left) <= FieldUtils.dist(rpos, wp_right):
            state.side = -1
        else:
            state.side = 1

    # Timeout
    if (time.time() - state.start_time) > config.AROUND_TIMEOUT:
        state.active = False
        return False

    # 5. Mouvement
    # On calcule le point de passage
    waypoint = AroundPlanner.compute_around_waypoint(ball, goal, side=state.side)
    angle_to_goal = FieldUtils.angle(rpos, goal)
    
    # Si on est proche du but (dernière ligne droite)
    if FieldUtils.dist(rpos, waypoint) < 0.15:
        # On fonce vers la cible finale
        robot.goto((target_pos[0], target_pos[1], angle_to_goal), wait=False)
    else:
        # On contourne en regardant le but (Strafe)
        robot.goto((waypoint[0], waypoint[1], angle_to_goal), wait=False)

    return False