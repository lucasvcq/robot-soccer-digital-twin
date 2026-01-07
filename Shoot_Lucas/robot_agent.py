"""
Moteur de décision tactique
Détermine l'action à prendre (tir, passe, défense) selon la situation
"""
from enum import Enum
from typing import Tuple
import config
from field_utils import FieldUtils
from game_state import GameState

class Action(Enum):
    """Types d'actions possibles"""
    SHOOT = "shoot"      # Tir au but
    PASS = "pass"        # Passe au coéquipier
    DEFEND = "defend"    # Position défensive (non implémenté)
    IDLE = "idle"        # Attente

class RobotAgent:
    """
    Moteur de décision pour la stratégie d'équipe
    Analyse la situation et décide de l'action optimale
    """
    
    def __init__(self, goal_pos: Tuple[float, float]):
        """
        Args:
            goal_pos: Position (x, y) du but adverse
        """
        self.goal = goal_pos
        
        # Sens du jeu : +1 si on attaque vers la droite, -1 vers la gauche
        self.sens_jeu = 1 if goal_pos[0] > 0 else -1
    
    def decide(self, state: GameState, attacker_id: int) -> Action:
        """
        Décide de l'action à prendre
        
        Critères de décision :
        1. Distance au but de l'attaquant
        2. Position du coéquipier (est-il mieux placé ?)
        3. Angle de tir disponible
        
        Args:
            state: État actuel du jeu (GameState)
            attacker_id: ID du robot attaquant (1 ou 2)
            
        Returns:
            Action: Action à exécuter (SHOOT ou PASS)
        """
        # Identification des robots
        receiver_id = 2 if attacker_id == 1 else 1
        
        # Positions
        att_pos = state.get_robot_pos(attacker_id)
        rec_pos = state.get_robot_pos(receiver_id)
        
        # Distances au but
        dist_att_goal = state.get_dist_to_goal(attacker_id)
        dist_rec_goal = state.get_dist_to_goal(receiver_id)
        
        # Critère 1 : Le coéquipier est-il mieux placé ?
        teammate_ahead = dist_rec_goal < (dist_att_goal - config.TEAMMATE_AHEAD_MARGIN)
        
        # Critère 2 : L'attaquant est-il trop loin du but ?
        far_from_goal = dist_att_goal > config.DIST_SHOOT_LIMIT
        
        # Décision finale
        if far_from_goal and teammate_ahead:
            action = Action.PASS
        else:
            action = Action.SHOOT
        
        # Debug
        if config.DEBUG_STRATEGY:
            print(f"[Decision] Attaquant: R{attacker_id} | "
                  f"Dist_but: {dist_att_goal:.2f}m | "
                  f"Copain_devant: {teammate_ahead} | "
                  f"Action: {action.value}", end='\r')
        
        return action
    
    def compute_pass_target(self, receiver_pos: Tuple[float, float]) -> Tuple[float, float]:
        """
        Calcule le point de passe optimal devant le receveur
        
        Args:
            receiver_pos: Position (x, y) du receveur
            
        Returns:
            Tuple (x, y): Point cible pour la passe
        """
        # Offset en X dans le sens du jeu
        offset_x = config.PASS_DEPTH_OFFSET * self.sens_jeu
        
        # Position cible brute
        target_x = receiver_pos[0] + offset_x
        
        # Clamp avec les limites réelles du terrain
        if self.sens_jeu > 0:
            # Attaque vers la droite
            target_x = min(target_x, FieldUtils.MAX_X - config.FIELD_MARGIN)
        else:
            # Attaque vers la gauche
            target_x = max(target_x, FieldUtils.MIN_X + config.FIELD_MARGIN)
        
        return (target_x, receiver_pos[1])
    
    def compute_support_position(self, attacker_pos: Tuple[float, float], 
                                  ball: Tuple[float, float]) -> Tuple[float, float]:
        """
        Calcule une position de soutien tactique pour le receveur
        quand il n'est pas en train de recevoir une passe
        
        Args:
            attacker_pos: Position (x, y) de l'attaquant
            ball: Position (x, y) de la balle
            
        Returns:
            Tuple (x, y): Position de soutien
        """
        # Position en retrait par rapport à l'attaquant
        support_x = attacker_pos[0] - config.SUPPORT_OFFSET * self.sens_jeu
        
        # Légèrement décalé latéralement pour ne pas gêner
        support_y = attacker_pos[1] + config.SUPPORT_LATERAL_OFFSET
        
        # Clamp
        support_pos = FieldUtils.clamp((support_x, support_y), config.FIELD_MARGIN)
        
        return support_pos
    
    def is_shot_clear(self, shooter_pos: Tuple[float, float], 
                      ball: Tuple[float, float],
                      obstacle_pos: Tuple[float, float]) -> bool:
        """
        Vérifie si le tir est dégagé (pas d'obstacle sur la trajectoire)
        
        Args:
            shooter_pos: Position du tireur
            ball: Position de la balle
            obstacle_pos: Position de l'obstacle potentiel
            
        Returns:
            bool: True si le tir est dégagé
        """
        # Distance de l'obstacle à la ligne balle-but
        dist = FieldUtils.point_to_line_distance(obstacle_pos, ball, self.goal)
        
        # Considère le tir dégagé si l'obstacle est à plus de 30cm de la ligne
        return dist > 0.30