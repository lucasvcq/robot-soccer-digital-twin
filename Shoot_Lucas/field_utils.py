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
        
        Args:
            point: Tuple (x, y) à limiter
            margin: Marge de sécurité en mètres (défaut: 0.01)
            
        Returns:
            Tuple (x, y): Point limité
        """
        x = min(max(point[0], FieldUtils.MIN_X + margin), FieldUtils.MAX_X - margin)
        y = min(max(point[1], FieldUtils.MIN_Y + margin), FieldUtils.MAX_Y - margin)
        return (x, y)

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