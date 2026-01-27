"""
Système de navigation pour les robots
Gère le déplacement vers la balle avec évitement intelligent
"""
import time
import math
from rsk.client import ClientError  # AJOUT : Pour gérer les préemptions
from field_utils import FieldUtils
from around_planner import AroundPlanner
import config

class AvoidanceState:
    """État du système de contournement/évitement"""
    
    def __init__(self):
        self.active = False
        self.start_time = 0.0
        self.side = 0  # -1 = gauche, +1 = droite
        self.ball_pos_at_start = None  # Position de la balle au début
    
    def reset(self):
        """Réinitialise l'état"""
        self.active = False
        self.start_time = 0.0
        self.side = 0
        self.ball_pos_at_start = None


def aller_derriere_balle(robot, ball, goal, state: AvoidanceState):
    """
    Amène le robot derrière la balle en contournant si nécessaire
    
    VERSION STABILISÉE :
    - Priorité à la position (l'angle est géré séparément dans RobotAgent)
    - Détection de mouvement de balle pour reset dynamique
    - Timeout de sécurité
    
    Args:
        robot: Instance du robot RSK
        ball: Position (x, y) de la balle
        goal: Position (x, y) du but
        state: État du contournement (AvoidanceState)
        
    Returns:
        bool: True si le robot est arrivé en position, False sinon
    """
    
    # 1. Calcul de la position cible
    target_pos = FieldUtils.behind_point(ball, goal, config.ALIGN_DISTANCE)
    rpos = robot.position
    dist_to_target = FieldUtils.dist(rpos, target_pos)
    
    # 2. Condition de succès SIMPLIFIÉE
    # On retire la vérification de l'angle ici pour éviter les oscillations
    # L'orientation sera gérée dans RobotAgent._handle_orientation()
    if dist_to_target <= config.AROUND_ARRIVAL_THRESH:
        state.reset()
        return True
    
    # 3. Reset dynamique si la balle bouge significativement
    if state.active and state.ball_pos_at_start is not None:
        ball_movement = FieldUtils.dist(state.ball_pos_at_start, ball)
        if ball_movement > 0.20:  # La balle a bougé de plus de 20cm
            if config.DEBUG_NAVIGATION:
                print(f"[Navigation] Reset: balle déplacée de {ball_movement:.2f}m")
            state.reset()
    
    # 4. Initialisation du contournement si nécessaire
    if not state.active:
        state.active = True
        state.start_time = time.time()
        state.ball_pos_at_start = ball
        
        # Choix automatique du meilleur côté
        state.side = AroundPlanner.choose_side(rpos, ball, goal)
        
        if config.DEBUG_NAVIGATION:
            side_name = "gauche" if state.side == -1 else "droite"
            print(f"[Navigation] Début contournement côté {side_name}")
    
    # 5. Timeout de sécurité
    elapsed = time.time() - state.start_time
    if elapsed > config.AROUND_TIMEOUT:
        if config.DEBUG_NAVIGATION:
            print(f"[Navigation] Timeout après {elapsed:.1f}s")
        state.reset()
        return False
    
    # 6. Calcul du waypoint de contournement
    waypoint = AroundPlanner.compute_around_waypoint(ball, goal, side=state.side)
    angle_to_goal = FieldUtils.angle(rpos, goal)
    
    # 7. Stratégie de mouvement
    dist_to_waypoint = FieldUtils.dist(rpos, waypoint)
    
    if dist_to_waypoint < 0.15:
        # Phase finale : on fonce vers la cible en regardant le but
        robot.goto((target_pos[0], target_pos[1], angle_to_goal), wait=False)
    else:
        # Phase de contournement : strafe latéral en regardant le but
        robot.goto((waypoint[0], waypoint[1], angle_to_goal), wait=False)
    
    return False


def needs_around(robot_pos, ball, goal):
    """
    Détermine si un contournement est nécessaire
    (Fonction optionnelle, non utilisée actuellement mais utile pour debug)
    
    Args:
        robot_pos: Position (x, y) du robot
        ball: Position (x, y) de la balle
        goal: Position (x, y) du but
        
    Returns:
        bool: True si un contournement est recommandé
    """
    # Vecteur robot -> balle
    v_rb = (ball[0] - robot_pos[0], ball[1] - robot_pos[1])
    
    # Vecteur unitaire robot -> goal
    u_rg = FieldUtils.unit_vector(robot_pos, goal)
    
    # Produit scalaire
    dot = v_rb[0] * u_rg[0] + v_rb[1] * u_rg[1]
    
    # Distance robot <-> balle
    d_rb = FieldUtils.dist(robot_pos, ball)
    
    # Angle entre robot->ball et robot->goal
    angle = abs(FieldUtils.angle_difference(
        FieldUtils.angle(robot_pos, ball),
        FieldUtils.angle(robot_pos, goal)
    ))
    angle_deg = abs(angle * 180.0 / 3.14159)
    
    # Critères de décision
    is_ball_ahead = dot > config.FRONT_DOT
    is_aligned = angle_deg < config.FRONT_ANGLE_DEG
    is_close = d_rb < config.DIST_CLOSE
    is_on_side = angle_deg > config.SIDE_ANGLE_DEG
    
    # Logique : contourner si balle devant mais mal aligné, ou sur le côté et proche
    needs_around = (is_ball_ahead and not is_aligned) or (is_on_side and is_close)
    
    return needs_around