"""
Agent défensif pour un robot
Gère le comportement défensif d'un robot individuel
"""
from typing import Tuple, Optional
from rsk.client import ClientError
from field_utils import FieldUtils
from defense_strategy import DefenseStrategy
import config

class DefenseAgent:
    """
    Agent défensif pour contrôler un robot en défense
    Similaire à RobotAgent mais spécialisé pour la défense
    """
    
    def __init__(self, robot, own_goal: Tuple[float, float], 
                 opponent_goal: Tuple[float, float], role: str, name: str):
        """
        Args:
            robot: Instance du robot RSK (green1 ou green2)
            own_goal: Position (x, y) de NOTRE but à défendre
            opponent_goal: Position (x, y) du but adverse
            role: "front" (défenseur avancé) ou "back" (défenseur reculé)
            name: Nom du robot pour le debug
        """
        self.robot = robot
        self.own_goal = own_goal
        self.opponent_goal = opponent_goal
        self.role = role
        self.name = name
        
        # État interne
        self.is_attacking_ball = False
        self.defensive_position = None
        
        # Paramètres de contrôle
        self.position_tolerance = 0.04  # 4cm de tolérance
        self.attack_threshold = 0.20  # Distance pour considérer "proche de la balle"
        self.clearance_power = 0.90  # Puissance de dégagement
        
    def update_state(self, ball: Tuple[float, float]) -> bool:
        """
        Met à jour l'état du défenseur et exécute les actions
        
        Logique :
        1. Si la balle est dangereusement proche → attaquer et dégager
        2. Sinon → se positionner défensivement
        
        Args:
            ball: Position (x, y) de la balle
            
        Returns:
            bool: True si un dégagement a été effectué, False sinon
        """
        rpos = self.robot.position
        
        # NOUVEAU : Vérifier que le robot n'est pas dans la zone interdite
        if FieldUtils.is_in_penalty_area(rpos, self.own_goal[0]):
            self._exit_penalty_area(rpos)
            return False
        
        # Décision : attaquer la balle ou défendre ?
        should_attack = DefenseStrategy.should_attack_ball(
            rpos, ball, self.own_goal, self.role,
            attack_threshold=self.attack_threshold
        )
        
        if should_attack:
            # Mode attaque : aller chercher la balle et dégager
            return self._attack_and_clear(ball)
        else:
            # Mode défense : se positionner
            return self._defensive_positioning(ball)
    
    def _defensive_positioning(self, ball: Tuple[float, float]) -> bool:
        """
        Positionne le robot défensivement entre la balle et le but
        
        Args:
            ball: Position de la balle
            
        Returns:
            bool: False (pas de dégagement)
        """
        rpos = self.robot.position
        rtheta = self.robot.orientation
        
        # Calculer la position défensive
        self.defensive_position = DefenseStrategy.compute_defensive_position(
            ball, self.own_goal, self.role
        )
        
        # Distance à la position défensive
        dist_to_pos = FieldUtils.dist(rpos, self.defensive_position)
        
        # Angle pour regarder la balle
        angle_to_ball = FieldUtils.angle(rpos, ball)
        
        # Si loin de la position, s'y déplacer
        if dist_to_pos > self.position_tolerance:
            try:
                self.robot.goto(
                    (self.defensive_position[0], self.defensive_position[1], angle_to_ball),
                    wait=False
                )
            except ClientError:
                pass
        else:
            # En position : juste orienter vers la balle
            ang_err = FieldUtils.wrap(angle_to_ball - rtheta)
            if abs(ang_err) > config.ANGLE_TOL:
                try:
                    self.robot.goto(
                        (rpos[0], rpos[1], angle_to_ball),
                        wait=False
                    )
                except ClientError:
                    pass
        
        return False
    
    def _attack_and_clear(self, ball: Tuple[float, float]) -> bool:
        """
        Attaque la balle et effectue un dégagement
        
        Séquence :
        1. Aller derrière la balle
        2. S'orienter vers la cible de dégagement
        3. Dégager
        
        Args:
            ball: Position de la balle
            
        Returns:
            bool: True si dégagement effectué, False sinon
        """
        rpos = self.robot.position
        rtheta = self.robot.orientation
        
        # Point d'interception derrière la balle
        intercept_point = DefenseStrategy.compute_intercept_point(
            ball, self.own_goal, offset=0.15
        )
        
        # Cible de dégagement
        clearance_target = DefenseStrategy.compute_clearance_target(
            ball, self.own_goal, self.opponent_goal
        )
        
        # Distance au point d'interception
        dist_to_intercept = FieldUtils.dist(rpos, intercept_point)
        
        # Distance à la balle
        dist_to_ball = FieldUtils.dist(rpos, ball)
        
        # Angle vers la cible de dégagement
        angle_to_target = FieldUtils.angle(ball, clearance_target)
        
        # Phase 1 : Se positionner derrière la balle
        if dist_to_intercept > self.position_tolerance:
            try:
                self.robot.goto(
                    (intercept_point[0], intercept_point[1], angle_to_target),
                    wait=False
                )
            except ClientError:
                pass
            return False
        
        # Phase 2 : S'orienter vers la cible
        ang_err = FieldUtils.wrap(angle_to_target - rtheta)
        if abs(ang_err) > config.ANGLE_TOL:
            try:
                self.robot.goto(
                    (rpos[0], rpos[1], angle_to_target),
                    wait=False
                )
            except ClientError:
                pass
            return False
        
        # Phase 3 : Dégager si proche de la balle et bien orienté
        if dist_to_ball <= config.FAST_CAPTURE_DISTANCE:
            try:
                if config.DEBUG_VERBOSE:
                    print(f"\n[{self.name}] 🥾 DÉGAGEMENT DÉFENSIF !")
                
                self.robot.kick(power=self.clearance_power)
                return True
                
            except ClientError as e:
                if config.DEBUG_VERBOSE:
                    print(f"\n[{self.name}] ❌ Erreur dégagement: {e}")
                return False
        
        # Approche finale vers la balle
        if dist_to_ball > config.FAST_CAPTURE_DISTANCE:
            try:
                self.robot.goto(
                    (ball[0], ball[1], angle_to_target),
                    wait=False
                )
            except ClientError:
                pass
        
        return False
    
    def _exit_penalty_area(self, current_pos: Tuple[float, float]):
        """
        Sort d'urgence de la zone interdite
        
        Args:
            current_pos: Position actuelle du robot
        """
        safe_pos = FieldUtils.get_safe_position_outside_penalty(
            current_pos, self.own_goal[0]
        )
        angle = FieldUtils.angle(current_pos, safe_pos)
        
        if config.DEBUG_VERBOSE:
            print(f"\n⚠️  [{self.name}] SORTIE D'URGENCE de la zone interdite!")
            print(f"   Position actuelle: ({current_pos[0]:.3f}, {current_pos[1]:.3f})")
            print(f"   Position sûre: ({safe_pos[0]:.3f}, {safe_pos[1]:.3f})")
        
        try:
            self.robot.goto((safe_pos[0], safe_pos[1], angle), wait=False)
        except ClientError:
            pass
    
    def set_role(self, new_role: str):
        """
        Change le rôle du défenseur
        
        Args:
            new_role: "front" ou "back"
        """
        if new_role in ["front", "back"]:
            self.role = new_role
            if config.DEBUG_VERBOSE:
                print(f"[{self.name}] Changement de rôle → {new_role}")
    
    def set_attack_threshold(self, threshold: float):
        """
        Configure la distance d'attaque
        
        Args:
            threshold: Distance en mètres
        """
        self.attack_threshold = max(0.1, min(0.5, threshold))
    
    def get_current_position(self) -> Optional[Tuple[float, float]]:
        """
        Retourne la position défensive calculée
        
        Returns:
            Tuple (x, y) ou None
        """
        return self.defensive_position
    
    def reset(self):
        """Réinitialise l'état interne"""
        self.is_attacking_ball = False
        self.defensive_position = None
