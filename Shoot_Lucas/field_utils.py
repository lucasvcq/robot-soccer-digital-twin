"""
Utilitaires géométriques pour le Robot Soccer Kit
Fonctions de calcul de distance, angle, vecteurs unitaires, etc.
"""
import math
from rsk import constants

class FieldUtils:
    """Classe utilitaire pour les calculs géométriques sur le terrain"""
    
    # Limites du terrain
    MAX_X = constants.field_length / 2.0
    MIN_X = -constants.field_length / 2.0
    MAX_Y = constants.field_width / 2.0
    MIN_Y = -constants.field_width / 2.0

    @staticmethod
    def dist(a, b):
        """
        Calcule la distance euclidienne entre deux points
        
        Args:
            a: Tuple (x, y) du premier point
            b: Tuple (x, y) du deuxième point
            
        Returns:
            float: Distance en mètres
        """
        return math.hypot(a[0] - b[0], a[1] - b[1])

    @staticmethod
    def unit_vector(a, b):
        """
        Calcule le vecteur unitaire de a vers b
        
        Args:
            a: Tuple (x, y) du point de départ
            b: Tuple (x, y) du point d'arrivée
            
        Returns:
            Tuple (dx, dy): Vecteur unitaire
        """
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        d = math.hypot(dx, dy)
        
        # Éviter la division par zéro
        if d < 1e-9:
            return (1.0, 0.0)
        
        return (dx / d, dy / d)

    @staticmethod
    def angle(a, b):
        """
        Calcule l'angle du vecteur de a vers b
        
        Args:
            a: Tuple (x, y) du point de départ
            b: Tuple (x, y) du point d'arrivée
            
        Returns:
            float: Angle en radians [-π, π]
        """
        return math.atan2(b[1] - a[1], b[0] - a[0])

    @staticmethod
    def wrap(angle):
        """
        Normalise un angle dans l'intervalle [-π, π]
        
        Args:
            angle: Angle en radians
            
        Returns:
            float: Angle normalisé
        """
        return (angle + math.pi) % (2 * math.pi) - math.pi

    @staticmethod
    def clamp(point, margin=0.01):
        """
        Limite un point aux bornes du terrain avec une marge
        ⚠️  ATTENTION: Ne vérifie PAS la zone interdite !
        Utilisez safe_clamp() pour éviter aussi la zone interdite.
        
        Args:
            point: Tuple (x, y) à limiter
            margin: Marge de sécurité en mètres (défaut: 0.01)
            
        Returns:
            Tuple (x, y): Point limité aux bornes du terrain
        """
        x = min(max(point[0], FieldUtils.MIN_X + margin), FieldUtils.MAX_X - margin)
        y = min(max(point[1], FieldUtils.MIN_Y + margin), FieldUtils.MAX_Y - margin)
        return (x, y)
    
    @staticmethod
    def safe_clamp(point, goal_x, margin=0.01):
        """
        Limite un point aux bornes du terrain ET évite la zone interdite
        
        Args:
            point: Tuple (x, y) à limiter
            goal_x: Position X du but (pour connaître la zone interdite)
            margin: Marge de sécurité en mètres (défaut: 0.01)
            
        Returns:
            Tuple (x, y): Point sûr (dans le terrain ET hors zone interdite)
        """
        # 1. D'abord clamp aux limites du terrain
        clamped = FieldUtils.clamp(point, margin)
        
        # 2. Ensuite vérifier la zone interdite
        if FieldUtils.is_in_penalty_area(clamped, goal_x):
            # Le point est dans la zone interdite, le corriger
            clamped = FieldUtils.get_safe_position_outside_penalty(clamped, goal_x)
            # Re-clamp au cas où la correction sortirait du terrain
            clamped = FieldUtils.clamp(clamped, margin)
        
        return clamped
    
    @staticmethod
    def compute_pass_power(distance):
        """
        Calcule la puissance de passe adaptée à la distance
        
        Plus la distance est grande, plus la puissance est élevée
        Interpolation linéaire entre POWER_PASS_MIN et POWER_PASS_MAX
        
        Args:
            distance: Distance en mètres entre le passeur et le receveur
            
        Returns:
            float: Puissance entre 0.0 et 1.0
        """
        import config
        
        # Clamper la distance dans la plage définie
        distance = max(config.PASS_DISTANCE_MIN, 
                      min(distance, config.PASS_DISTANCE_MAX))
        
        # Interpolation linéaire
        # t = 0.0 pour distance minimale → POWER_PASS_MIN
        # t = 1.0 pour distance maximale → POWER_PASS_MAX
        t = (distance - config.PASS_DISTANCE_MIN) / (config.PASS_DISTANCE_MAX - config.PASS_DISTANCE_MIN)
        
        power = config.POWER_PASS_MIN + t * (config.POWER_PASS_MAX - config.POWER_PASS_MIN)
        
        return max(0.0, min(1.0, power))  # Sécurité : clamp entre 0 et 1

    @staticmethod
    def behind_point(ball, goal, distance):
        """
        Calcule un point à une certaine distance derrière la balle
        par rapport au but
        
        Args:
            ball: Position (x, y) de la balle
            goal: Position (x, y) du but
            distance: Distance en mètres derrière la balle
            
        Returns:
            Tuple (x, y): Point derrière la balle
        """
        u = FieldUtils.unit_vector(ball, goal)
        return (ball[0] - u[0] * distance, ball[1] - u[1] * distance)

    @staticmethod
    def is_robot_between_ball_and_goal(robot_pos, ball, goal, angle_threshold_deg=20):
        """
        Détecte si le robot est positionné entre la balle et le but
        
        Args:
            robot_pos: Position (x, y) du robot
            ball: Position (x, y) de la balle
            goal: Position (x, y) du but
            angle_threshold_deg: Seuil d'angle en degrés (défaut: 20)
            
        Returns:
            bool: True si le robot est entre la balle et le but
        """
        # Vecteur robot -> goal (unitaire)
        u_rg = FieldUtils.unit_vector(robot_pos, goal)
        
        # Vecteur robot -> ball
        v_rb = (ball[0] - robot_pos[0], ball[1] - robot_pos[1])
        
        # Produit scalaire
        dot = v_rb[0] * u_rg[0] + v_rb[1] * u_rg[1]
        
        # Angle entre robot->ball et robot->goal
        angle_rb = abs(math.degrees(
            FieldUtils.wrap(
                FieldUtils.angle(robot_pos, ball) - 
                FieldUtils.angle(robot_pos, goal)
            )
        ))
        
        # Le robot est "entre" si le produit scalaire est négatif
        # ET l'angle est proche de 180°
        return (dot < 0.0) and (angle_rb > (180.0 - angle_threshold_deg))

    @staticmethod
    def angle_difference(angle1, angle2):
        """
        Calcule la différence entre deux angles (normalisée)
        
        Args:
            angle1: Premier angle en radians
            angle2: Deuxième angle en radians
            
        Returns:
            float: Différence d'angle normalisée [-π, π]
        """
        return FieldUtils.wrap(angle1 - angle2)
    
    @staticmethod
    def point_to_line_distance(point, line_start, line_end):
        """
        Calcule la distance d'un point à une ligne
        
        Args:
            point: Tuple (x, y) du point
            line_start: Tuple (x, y) du début de la ligne
            line_end: Tuple (x, y) de la fin de la ligne
            
        Returns:
            float: Distance perpendiculaire du point à la ligne
        """
        # Vecteur ligne
        lx = line_end[0] - line_start[0]
        ly = line_end[1] - line_start[1]
        
        # Longueur de la ligne au carré
        l2 = lx * lx + ly * ly
        
        if l2 < 1e-9:
            # La ligne est un point
            return FieldUtils.dist(point, line_start)
        
        # Projection du point sur la ligne
        t = max(0, min(1, (
            (point[0] - line_start[0]) * lx + 
            (point[1] - line_start[1]) * ly
        ) / l2))
        
        # Point le plus proche sur la ligne
        proj_x = line_start[0] + t * lx
        proj_y = line_start[1] + t * ly
        
        return FieldUtils.dist(point, (proj_x, proj_y))
    
    @staticmethod
    def is_in_penalty_area(point, goal_x):
        """
        Vérifie si un point est dans la zone interdite (surface de réparation)
        La zone RÉELLE est de 0.30m × 0.90m DEVANT les cages (côté terrain)
        La MARGE est une extension de sécurité pour éviter les violations
        
        IMPORTANT: La zone est DEVANT le but (vers le terrain), pas derrière !
        
        Args:
            point: Tuple (x, y) à vérifier
            goal_x: Position X du but (pour savoir de quel côté)
            
        Returns:
            bool: True si le point est dans la zone interdite (incluant la marge)
        """
        from config import PENALTY_AREA_DEPTH, PENALTY_AREA_WIDTH, PENALTY_AREA_MARGIN
        
        # La zone TOTALE = zone réglementaire + marge de sécurité
        total_depth = PENALTY_AREA_DEPTH + PENALTY_AREA_MARGIN
        total_width = PENALTY_AREA_WIDTH + 2 * PENALTY_AREA_MARGIN
        
        # CORRECTION: La zone s'étend DEPUIS le but VERS le terrain
        if goal_x < 0:
            # But à GAUCHE (X négatif)
            # Zone: du bord gauche (MIN_X) jusqu'à (MIN_X + depth)
            # Un point est dans la zone si: MIN_X <= X <= MIN_X + depth
            zone_start = FieldUtils.MIN_X
            zone_end = FieldUtils.MIN_X + total_depth
            in_x_range = zone_start <= point[0] <= zone_end
        else:
            # But à DROITE (X positif)
            # Zone: de (MAX_X - depth) jusqu'au bord droit (MAX_X)
            # Un point est dans la zone si: MAX_X - depth <= X <= MAX_X
            zone_start = FieldUtils.MAX_X - total_depth
            zone_end = FieldUtils.MAX_X
            in_x_range = zone_start <= point[0] <= zone_end
        
        # Limites en Y (centrées sur 0)
        y_half_width = total_width / 2.0
        in_y_range = -y_half_width <= point[1] <= y_half_width
        
        return in_x_range and in_y_range
    
    @staticmethod
    def get_safe_position_outside_penalty(point, goal_x):
        """
        Si un point est dans la zone interdite, retourne le point le plus proche à l'extérieur
        AVEC UNE MARGE SUPPLÉMENTAIRE de sécurité
        
        Args:
            point: Tuple (x, y) potentiellement dans la zone
            goal_x: Position X du but
            
        Returns:
            Tuple (x, y): Point sûr à l'extérieur de la zone
        """
        if not FieldUtils.is_in_penalty_area(point, goal_x):
            return point  # Déjà à l'extérieur
        
        from config import PENALTY_AREA_DEPTH, PENALTY_AREA_WIDTH, PENALTY_AREA_MARGIN
        
        x, y = point
        total_depth = PENALTY_AREA_DEPTH + PENALTY_AREA_MARGIN
        total_width = PENALTY_AREA_WIDTH + 2 * PENALTY_AREA_MARGIN
        
        # MARGE SUPPLÉMENTAIRE pour sortir vraiment de la zone
        EXTRA_SAFETY = 0.10  # 10cm de plus
        
        # Déterminer les limites de la zone
        if goal_x < 0:
            # But à gauche : pousser vers la droite (X positif)
            x_boundary = FieldUtils.MIN_X + total_depth
            safe_x = x_boundary + EXTRA_SAFETY
        else:
            # But à droite : pousser vers la gauche (X négatif)
            x_boundary = FieldUtils.MAX_X - total_depth
            safe_x = x_boundary - EXTRA_SAFETY
        
        y_half_width = total_width / 2.0
        
        # Stratégie en Y : sortir par le côté le plus proche
        if abs(y) > y_half_width:
            # Déjà hors de la zone en Y
            safe_y = y
        else:
            # Pousser vers le bord le plus proche en Y
            if abs(y) < 0.1:
                # Très proche du centre : pousser vers le haut
                safe_y = y_half_width + EXTRA_SAFETY
            elif y > 0:
                safe_y = y_half_width + EXTRA_SAFETY
            else:
                safe_y = -y_half_width - EXTRA_SAFETY
        
        # Clamp pour rester dans le terrain
        safe_pos = FieldUtils.clamp((safe_x, safe_y), margin=0.05)
        
        return safe_pos