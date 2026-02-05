"""
API simplifiée pour le tir automatique
Usage simple depuis n'importe quel code

Exemple d'utilisation:
    from simple_shooter import SimpleShooter
    
    with rsk.Client() as client:
        shooter = SimpleShooter(client.green1)
        
        # Viser et tirer vers un point
        shooter.shoot_at(client.ball, target=(1.0, 0.0))
        
        # Ou simplement viser les cages
        shooter.shoot_at_goal(client.ball)
"""

import rsk
from typing import Tuple, Optional
from field_utils import FieldUtils
from navigation import AvoidanceState, aller_derriere_balle
import config

class SimpleShooter:
    """
    Classe simple pour contrôler un robot et lui faire tirer
    Utilisable dans n'importe quel code
    """
    
    def __init__(self, robot, goal: Optional[Tuple[float, float]] = None):
        """
        Initialise le shooter
        
        Args:
            robot: Instance du robot RSK (ex: client.green1)
            goal: Position (x, y) du but à viser (optionnel, par défaut config.GOAL_POSITION)
        """
        self.robot = robot
        self.goal = goal if goal is not None else config.GOAL_POSITION
        self.nav_state = AvoidanceState()
        self.kick_power = config.POWER_SHOOT
    
    def shoot_at_goal(self, ball: Tuple[float, float], 
                     power: float = None,
                     wait_for_kick: bool = True) -> bool:
        """
        Se place derrière la balle et tire au but
        
        Args:
            ball: Position (x, y) de la balle
            power: Puissance du tir (0.0 à 1.0), None = config.POWER_SHOOT
            wait_for_kick: Si True, bloque jusqu'au tir. Si False, retourne immédiatement
            
        Returns:
            bool: True si le tir a été effectué, False si encore en cours
            
        Usage:
            # Mode bloquant (attend le tir)
            shooter.shoot_at_goal(ball)
            
            # Mode non-bloquant (à appeler en boucle)
            while not shooter.shoot_at_goal(ball, wait_for_kick=False):
                time.sleep(0.05)
        """
        return self.shoot_at(ball, self.goal, power, wait_for_kick)
    
    def shoot_at(self, ball: Tuple[float, float], 
                target: Tuple[float, float],
                power: float = None,
                wait_for_kick: bool = True) -> bool:
        """
        Se place derrière la balle et tire vers une cible donnée
        
        Args:
            ball: Position (x, y) de la balle
            target: Position (x, y) de la cible à viser
            power: Puissance du tir (0.0 à 1.0), None = config.POWER_SHOOT
            wait_for_kick: Si True, bloque jusqu'au tir. Si False, retourne immédiatement
            
        Returns:
            bool: True si le tir a été effectué, False si encore en cours
            
        Usage:
            # Tirer vers un point spécifique
            shooter.shoot_at(ball, target=(0.5, 0.3))
            
            # Mode boucle
            while not shooter.shoot_at(ball, target=(0.5, 0.3), wait_for_kick=False):
                time.sleep(0.05)
        """
        if power is not None:
            self.kick_power = max(0.0, min(1.0, power))
        
        if wait_for_kick:
            # Mode bloquant : on boucle jusqu'au tir
            import time
            while True:
                if self._single_update(ball, target):
                    return True
                time.sleep(config.LOOP_DT)
        else:
            # Mode non-bloquant : une seule itération
            return self._single_update(ball, target)
    
    def _single_update(self, ball: Tuple[float, float], 
                      target: Tuple[float, float]) -> bool:
        """
        Une seule itération de mise à jour (pour mode non-bloquant)
        
        Returns:
            bool: True si le tir a été effectué
        """
        rpos = self.robot.position
        rtheta = self.robot.orientation
        
        # NOUVEAU: Vérifier si le robot est dans la zone interdite
        if FieldUtils.is_in_penalty_area(rpos, target[0]):
            safe_pos = FieldUtils.get_safe_position_outside_penalty(rpos, target[0])
            angle_away = FieldUtils.angle(rpos, safe_pos)
            try:
                self.robot.goto((safe_pos[0], safe_pos[1], angle_away), wait=False)
            except rsk.ClientError:
                pass
            return False
        
        # 1. Navigation vers la balle
        is_in_zone = aller_derriere_balle(self.robot, ball, target, self.nav_state)
        
        if not is_in_zone:
            return False
        
        # 2. Orientation vers la cible
        # CORRECTION: Utiliser les tolérances adaptées au mode
        angle_tol = config.FAST_ANGLE_TOL if config.FAST_MODE else config.ANGLE_TOL
        capture_dist = config.FAST_CAPTURE_DISTANCE if config.FAST_MODE else config.CAPTURE_DISTANCE
        
        desired_theta = FieldUtils.angle(rpos, target)
        ang_err = FieldUtils.wrap(desired_theta - rtheta)
        
        if abs(ang_err) > angle_tol:
            try:
                # En mode rapide, wait=False pour ne pas bloquer
                wait_for_turn = not config.FAST_MODE
                self.robot.goto((rpos[0], rpos[1], desired_theta), wait=wait_for_turn)
            except rsk.ClientError:
                pass
            # En mode rapide, on continue sans attendre
            if not config.FAST_MODE:
                return False
        
        # 3. Tir
        d_to_ball = FieldUtils.dist(rpos, ball)
        
        # Approche finale
        if d_to_ball > capture_dist:
            u_rg = FieldUtils.unit_vector(rpos, target)
            
            # En mode rapide, on vise directement la balle
            if config.FAST_MODE:
                target_pos = (ball[0], ball[1], desired_theta)
            else:
                target_pos = (
                    ball[0] - u_rg[0] * 0.02,
                    ball[1] - u_rg[1] * 0.02,
                    desired_theta
                )
            
            # Vérifier que la position d'approche n'est pas dans la zone interdite
            if FieldUtils.is_in_penalty_area(target_pos[:2], target[0]):
                return False
            
            try:
                # En mode rapide, wait=False
                self.robot.goto(target_pos, wait=not config.FAST_MODE)
            except rsk.ClientError:
                pass
            return False
        
        # Tir final
        if d_to_ball <= capture_dist and abs(ang_err) <= angle_tol:
            try:
                self.robot.kick(power=self.kick_power)
                self.nav_state.reset()
                return True
            except rsk.ClientError as e:
                if config.DEBUG_VERBOSE:
                    print(f"Erreur kick: {e}")
                return False
        
        return False
    
    def set_goal(self, goal: Tuple[float, float]):
        """Change le but par défaut"""
        self.goal = goal
    
    def set_power(self, power: float):
        """Change la puissance de tir (0.0 à 1.0)"""
        self.kick_power = max(0.0, min(1.0, power))
    
    def reset(self):
        """Réinitialise l'état de navigation"""
        self.nav_state.reset()


# ============================================================================
# FONCTIONS STANDALONE (encore plus simple)
# ============================================================================

def shoot_at_goal(robot, ball: Tuple[float, float], 
                 goal: Tuple[float, float] = None,
                 power: float = None) -> bool:
    """
    Fonction autonome : fait tirer un robot au but
    Crée un shooter temporaire et tire (bloquant)
    
    Args:
        robot: Instance du robot RSK
        ball: Position (x, y) de la balle
        goal: Position (x, y) du but (optionnel)
        power: Puissance (0.0-1.0, optionnel)
        
    Returns:
        bool: True si le tir a réussi
        
    Usage ultra-simple:
        from simple_shooter import shoot_at_goal
        shoot_at_goal(client.green1, client.ball)
    """
    shooter = SimpleShooter(robot, goal)
    if power is not None:
        shooter.set_power(power)
    return shooter.shoot_at_goal(ball, wait_for_kick=True)


def shoot_at_target(robot, ball: Tuple[float, float], 
                   target: Tuple[float, float],
                   power: float = None) -> bool:
    """
    Fonction autonome : fait tirer un robot vers une cible
    
    Args:
        robot: Instance du robot RSK
        ball: Position (x, y) de la balle
        target: Position (x, y) de la cible
        power: Puissance (0.0-1.0, optionnel)
        
    Returns:
        bool: True si le tir a réussi
        
    Usage:
        from simple_shooter import shoot_at_target
        shoot_at_target(client.green1, client.ball, target=(0.5, 0.3))
    """
    shooter = SimpleShooter(robot, goal=target)
    if power is not None:
        shooter.set_power(power)
    return shooter.shoot_at(ball, target, wait_for_kick=True)