"""
Agent de contrôle pour un robot individuel - VERSION CORRIGÉE
Gère la navigation, l'orientation et le tir
AVEC VÉRIFICATION STRICTE DE LA ZONE ADVERSE
"""
from rsk.client import ClientError
from field_utils import FieldUtils
import config

# Import différé de navigation pour éviter les imports circulaires
import navigation

class RobotAgent:
    """
    Agent intelligent pour contrôler un robot
    VERSION CORRIGÉE : Vérifie TOUJOURS la zone adverse avant toute action
    """
    
    def __init__(self, robot, goal, name):
        """
        Args:
            robot: Instance du robot RSK (green1 ou green2)
            goal: Position (x, y) du but adverse (à attaquer)
            name: Nom du robot pour le debug
        """
        self.robot = robot
        self.goal = goal  # But ADVERSE
        self.name = name
        
        # État de navigation
        from navigation import AvoidanceState
        self.nav_state = AvoidanceState()
        
        # Paramètres de tir
        self.kick_power = config.POWER_SHOOT
    
    def set_target(self, new_target):
        """Change la cible du robot (but ou point de passe)"""
        self.goal = new_target
    
    def set_kick_power(self, power):
        """Configure la puissance du tir"""
        self.kick_power = max(0.0, min(1.0, power))
    
    def _is_position_safe(self, position):
        """
        Vérifie si une position est HORS de la zone adverse
        
        Args:
            position: Tuple (x, y) ou (x, y, theta)
            
        Returns:
            bool: True si la position est sûre (hors zone adverse)
        """
        pos_2d = position[:2] if len(position) > 2 else position
        return not FieldUtils.is_in_penalty_area(pos_2d, self.goal[0])
    
    def _get_safe_ball_approach_position(self, ball):
        """
        Calcule une position d'approche de la balle qui est HORS zone adverse
        
        Si la balle est dans la zone adverse :
        - On s'arrête à la limite de la zone
        - On ne tire PAS (règle 6)
        
        Args:
            ball: Position (x, y) de la balle
            
        Returns:
            Tuple (x, y, can_shoot):
                - (x, y): Position sûre d'approche
                - can_shoot: True si on peut tirer, False si balle inaccessible
        """
        # Vérifier si la balle est dans la zone adverse
        if FieldUtils.is_in_penalty_area(ball, self.goal[0]):
            # BALLE DANS ZONE ADVERSE → ON NE PEUT PAS Y ALLER
            if config.DEBUG_VERBOSE:
                print(f"[{self.name}] ⚠️  Balle dans zone adverse - INACCESSIBLE")
            
            # Position sûre = à la limite de la zone adverse
            safe_pos = FieldUtils.get_safe_position_outside_penalty(ball, self.goal[0])
            return (safe_pos, False)  # can_shoot = False
        
        # Balle hors zone → OK
        return (ball, True)  # can_shoot = True
    
    def update_state(self, ball):
        """
        Met à jour l'état du robot et exécute les actions
        VERSION CORRIGÉE : Vérifie la zone adverse à chaque étape
        
        Séquence :
        1. Vérifier qu'on n'est pas dans la zone adverse
        2. Vérifier si la balle est accessible (pas dans zone adverse)
        3. Navigation vers la balle
        4. Orientation vers la cible
        5. Tir si conditions réunies
        
        Args:
            ball: Position (x, y) de la balle
            
        Returns:
            bool: True si un tir a été effectué, False sinon
        """
        rpos = self.robot.position
        rtheta = self.robot.orientation
        
        # ÉTAPE 0 : Vérifier qu'on n'est PAS dans la zone adverse
        if not self._is_position_safe(rpos):
            # ON EST DANS LA ZONE ADVERSE ! Sortir IMMÉDIATEMENT
            safe_pos = FieldUtils.get_safe_position_outside_penalty(rpos, self.goal[0])
            angle_away = FieldUtils.angle(rpos, safe_pos)
            
            if config.DEBUG_VERBOSE:
                print(f"[{self.name}] 🚨 SORTIE D'URGENCE zone adverse !")
            
            try:
                self.robot.goto((safe_pos[0], safe_pos[1], angle_away), wait=False)
            except ClientError:
                pass
            
            # Reset navigation
            self.nav_state.reset()
            return False
        
        # ÉTAPE 1 : Vérifier si la balle est accessible
        safe_ball_pos, can_shoot = self._get_safe_ball_approach_position(ball)
        
        if not can_shoot:
            # Balle dans zone adverse → On ne peut rien faire
            # On va juste à la limite et on attend
            try:
                angle_to_ball = FieldUtils.angle(rpos, ball)
                self.robot.goto((safe_ball_pos[0], safe_ball_pos[1], angle_to_ball), wait=False)
            except ClientError:
                pass
            return False
        
        # ÉTAPE 2 : Navigation vers la balle (position derrière la balle)
        from navigation import aller_derriere_balle
        is_in_zone = aller_derriere_balle(
            self.robot, ball, self.goal, self.nav_state
        )
        
        # Vérifier à nouveau après navigation
        if not self._is_position_safe(self.robot.position):
            # La navigation nous a amenés trop proche de la zone !
            if config.DEBUG_VERBOSE:
                print(f"[{self.name}] ⚠️  Navigation trop proche zone adverse")
            self.nav_state.reset()
            return False
        
        if not is_in_zone:
            return False
        
        # ÉTAPE 3 : Orientation vers la cible
        if self._handle_orientation(rpos, rtheta):
            return False
        
        # ÉTAPE 4 : Tir (avec vérifications finales)
        return self._handle_kick(ball, rpos, rtheta)
    
    def _handle_orientation(self, rpos, rtheta):
        """Gère l'orientation du robot vers la cible"""
        desired_theta = FieldUtils.angle(rpos, self.goal)
        ang_err = FieldUtils.wrap(desired_theta - rtheta)
        angle_tol = config.FAST_ANGLE_TOL if config.FAST_MODE else config.ANGLE_TOL
        
        if abs(ang_err) > angle_tol:
            try:
                wait_for_orientation = not config.FAST_MODE
                self.robot.goto((rpos[0], rpos[1], desired_theta), wait=wait_for_orientation)
            except ClientError:
                pass
            return not config.FAST_MODE
        
        return False
    
    def _handle_kick(self, ball, rpos, rtheta):
        """
        Gère l'approche finale et le tir
        VÉRIFICATIONS MULTIPLES de la zone adverse
        """
        # VÉRIFICATION 1 : On n'est pas dans la zone adverse
        if not self._is_position_safe(rpos):
            if config.DEBUG_VERBOSE:
                print(f"[{self.name}] ⚠️  Tir annulé : dans zone adverse")
            return False
        
        # VÉRIFICATION 2 : La balle n'est pas dans la zone adverse
        if not self._is_position_safe(ball):
            if config.DEBUG_VERBOSE:
                print(f"[{self.name}] ⚠️  Tir annulé : balle dans zone adverse")
            return False
        
        # Distances et angles
        d_to_ball = FieldUtils.dist(rpos, ball)
        desired_theta = FieldUtils.angle(rpos, self.goal)
        ang_err = FieldUtils.wrap(desired_theta - rtheta)
        
        # Tolérances
        capture_dist = config.FAST_CAPTURE_DISTANCE if config.FAST_MODE else config.CAPTURE_DISTANCE
        angle_tol = config.FAST_ANGLE_TOL if config.FAST_MODE else config.ANGLE_TOL
        
        # Phase 1 : Approche finale
        if d_to_ball > capture_dist:
            u_rg = FieldUtils.unit_vector(rpos, self.goal)
            
            if config.FAST_MODE:
                target_pos = (ball[0], ball[1], desired_theta)
            else:
                target_pos = (
                    ball[0] - u_rg[0] * 0.02,
                    ball[1] - u_rg[1] * 0.02,
                    desired_theta
                )
            
            # VÉRIFICATION 3 : Position d'approche hors zone adverse
            if not self._is_position_safe(target_pos):
                if config.DEBUG_VERBOSE:
                    print(f"[{self.name}] ⚠️  Approche trop proche zone adverse")
                return False
            
            try:
                self.robot.goto(target_pos, wait=False)
            except ClientError:
                pass
            return False
        
        # Phase 2 : Tir final
        if d_to_ball <= capture_dist and abs(ang_err) <= angle_tol:
            # VÉRIFICATION FINALE avant de tirer
            if not self._is_position_safe(rpos) or not self._is_position_safe(ball):
                if config.DEBUG_VERBOSE:
                    print(f"[{self.name}] ⚠️  Tir annulé : zone adverse")
                return False
            
            try:
                if config.DEBUG_VERBOSE:
                    print(f"\n[{self.name}] 🚀 KICK (Power={self.kick_power:.1f}) !")
                
                self.robot.kick(power=self.kick_power)
                self.nav_state.reset()
                return True
                
            except ClientError as e:
                if "preempted" in str(e):
                    if config.DEBUG_VERBOSE:
                        print(f"\n[{self.name}] Robot préempté pendant le tir")
                else:
                    print(f"\n[{self.name}] ❌ Erreur kick: {e}")
                return False
        
        return False
    
    def goto_position(self, target_pos, target_theta=None):
        """
        Envoie le robot à une position donnée
        VÉRIFIE que la position est hors zone adverse
        """
        if target_theta is None:
            target_theta = self.robot.orientation
        
        # Vérifier que la position cible est sûre
        if not self._is_position_safe(target_pos):
            # Position dangereuse, trouver une position sûre proche
            safe_pos = FieldUtils.get_safe_position_outside_penalty(target_pos, self.goal[0])
            target_pos = safe_pos
            
            if config.DEBUG_VERBOSE:
                print(f"[{self.name}] ⚠️  Position corrigée pour éviter zone adverse")
        
        try:
            self.robot.goto((target_pos[0], target_pos[1], target_theta), wait=False)
        except ClientError:
            pass
    
    def reset_navigation(self):
        """Réinitialise l'état de navigation"""
        self.nav_state.reset()