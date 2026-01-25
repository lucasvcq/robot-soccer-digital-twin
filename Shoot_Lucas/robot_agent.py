"""
Agent de contrôle pour un robot individuel
Gère la navigation, l'orientation et le tir
"""
from rsk.client import ClientError
from field_utils import FieldUtils
import config

# Import différé de navigation pour éviter les imports circulaires
import navigation

class RobotAgent:
    """
    Agent intelligent pour contrôler un robot
    Gère : navigation, orientation, tir
    """
    
    def __init__(self, robot, goal, name):
        """
        Args:
            robot: Instance du robot RSK (green1 ou green2)
            goal: Position (x, y) du but par défaut
            name: Nom du robot pour le debug
        """
        self.robot = robot
        self.goal = goal
        self.name = name
        
        # État de navigation - création différée
        from navigation import AvoidanceState
        self.nav_state = AvoidanceState()
        
        # Paramètres de tir
        self.kick_power = config.POWER_SHOOT  # Puissance par défaut
    
    def set_target(self, new_target):
        """
        Change la cible du robot (but ou point de passe)
        
        Args:
            new_target: Tuple (x, y) de la nouvelle cible
        """
        self.goal = new_target
    
    def set_kick_power(self, power):
        """
        Configure la puissance du tir
        
        Args:
            power: Float entre 0.0 et 1.0
        """
        self.kick_power = max(0.0, min(1.0, power))
    
    def update_state(self, ball):
        """
        Met à jour l'état du robot et exécute les actions
        
        Séquence :
        1. Navigation vers la balle
        2. Orientation vers la cible
        3. Tir si conditions réunies
        
        Args:
            ball: Position (x, y) de la balle
            
        Returns:
            bool: True si un tir a été effectué, False sinon
        """
        rpos = self.robot.position
        rtheta = self.robot.orientation
        
        # 1. Navigation : aller derrière la balle
        from navigation import aller_derriere_balle
        is_in_zone = aller_derriere_balle(
            self.robot, ball, self.goal, self.nav_state
        )
        
        # Si on n'est pas encore en position, on continue la navigation
        if not is_in_zone:
            return False
        
        # 2. Orientation : tourner vers la cible
        if self._handle_orientation(rpos, rtheta):
            return False  # Encore en train de tourner
        
        # 3. Tir : exécuter si toutes les conditions sont réunies
        return self._handle_kick(ball, rpos, rtheta)
    
    def _handle_orientation(self, rpos, rtheta):
        """
        Gère l'orientation du robot vers la cible
        AMÉLIORATION : En mode rapide, orientation non-bloquante
        
        Args:
            rpos: Position (x, y) du robot
            rtheta: Orientation actuelle en radians
            
        Returns:
            bool: True si le robot est en train de tourner, False si bien orienté
        """
        # Angle désiré vers la cible
        desired_theta = FieldUtils.angle(rpos, self.goal)
        
        # Erreur d'angle (normalisée)
        ang_err = FieldUtils.wrap(desired_theta - rtheta)
        
        # Tolérance adaptée au mode
        angle_tol = config.FAST_ANGLE_TOL if config.FAST_MODE else config.ANGLE_TOL
        
        # Si l'erreur dépasse la tolérance
        if abs(ang_err) > angle_tol:
            try:
                # AMÉLIORATION : En mode rapide, wait=False
                wait_for_orientation = not config.FAST_MODE
                self.robot.goto((rpos[0], rpos[1], desired_theta), wait=wait_for_orientation)
            except ClientError:
                pass
            
            # En mode rapide, on ne bloque pas (return False)
            # Le robot tire même si pas parfaitement orienté
            return not config.FAST_MODE
        
        return False  # Bien orienté
    
    def _handle_kick(self, ball, rpos, rtheta):
        """
        Gère l'approche finale et le tir
        RESPECTE LA ZONE INTERDITE
        
        Args:
            ball: Position (x, y) de la balle
            rpos: Position (x, y) du robot
            rtheta: Orientation du robot en radians
            
        Returns:
            bool: True si un tir a été effectué, False sinon
        """
        # NOUVEAU : Vérifier que le robot n'est pas dans la zone interdite
        if FieldUtils.is_in_penalty_area(rpos, self.goal[0]):
            # On est dans la zone interdite, sortir immédiatement
            safe_pos = FieldUtils.get_safe_position_outside_penalty(rpos, self.goal[0])
            angle_away = FieldUtils.angle(rpos, safe_pos)
            self.robot.goto((safe_pos[0], safe_pos[1], angle_away), wait=False)
            if config.DEBUG_VERBOSE:
                print(f"[{self.name}] ⚠️  Sortie de la zone interdite")
            return False
        
        # Distances et angles
        d_to_ball = FieldUtils.dist(rpos, ball)
        desired_theta = FieldUtils.angle(rpos, self.goal)
        ang_err = FieldUtils.wrap(desired_theta - rtheta)
        
        # Tolérances adaptées au mode
        capture_dist = config.FAST_CAPTURE_DISTANCE if config.FAST_MODE else config.CAPTURE_DISTANCE
        angle_tol = config.FAST_ANGLE_TOL if config.FAST_MODE else config.ANGLE_TOL
        
        # Phase 1 : Approche finale si trop loin
        if d_to_ball > capture_dist:
            # AMÉLIORATION : Approche NON-BLOQUANTE (wait=False)
            # Le robot avance vers la balle sans attendre d'être parfaitement positionné
            u_rg = FieldUtils.unit_vector(rpos, self.goal)
            
            # En mode rapide, on vise directement la balle (pas 2cm avant)
            if config.FAST_MODE:
                target_pos = (ball[0], ball[1], desired_theta)
            else:
                target_pos = (
                    ball[0] - u_rg[0] * 0.02,  # 2cm avant la balle
                    ball[1] - u_rg[1] * 0.02,
                    desired_theta
                )
            
            # Vérifier que la position d'approche n'est pas dans la zone interdite
            if FieldUtils.is_in_penalty_area(target_pos[:2], self.goal[0]):
                if config.DEBUG_VERBOSE:
                    print(f"[{self.name}] Position d'approche trop proche de la zone interdite")
                return False
            
            try:
                # CHANGEMENT CRITIQUE : wait=False au lieu de wait=True
                self.robot.goto(target_pos, wait=False)
            except ClientError:
                pass
            return False
        
        # Phase 2 : Tir si toutes les conditions sont réunies
        if d_to_ball <= capture_dist and abs(ang_err) <= angle_tol:
            try:
                if config.DEBUG_VERBOSE:
                    print(f"\n[{self.name}] 🚀 KICK (Power={self.kick_power:.1f}) !")
                
                # Exécution du tir
                self.robot.kick(power=self.kick_power)
                
                # Reset de l'état de navigation après le tir
                self.nav_state.reset()
                
                return True  # Tir effectué
                
            except ClientError as e:
                # Robot préempté pendant le tir (pénalité, pause, etc.)
                if "preempted" in str(e):
                    if config.DEBUG_VERBOSE:
                        print(f"\n[{self.name}] Robot préempté pendant le tir")
                else:
                    print(f"\n[{self.name}] ❌ Erreur kick: {e}")
                return False
        
        return False
    
    def goto_position(self, target_pos, target_theta=None):
        """
        Envoie le robot à une position donnée (utilisé pour le receveur)
        Gère les exceptions de préemption
        
        Args:
            target_pos: Tuple (x, y) de la position cible
            target_theta: Angle cible (optionnel, sinon conserve l'actuel)
        """
        if target_theta is None:
            target_theta = self.robot.orientation
        
        try:
            self.robot.goto((target_pos[0], target_pos[1], target_theta), wait=False)
        except ClientError:
            # Robot préempté, on ignore silencieusement
            pass
    
    def reset_navigation(self):
        """Réinitialise l'état de navigation"""
        self.nav_state.reset()