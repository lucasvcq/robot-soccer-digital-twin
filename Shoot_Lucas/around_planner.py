"""
Planificateur de contournement
Calcule des waypoints latéraux pour contourner la balle
"""
import math
from field_utils import FieldUtils
import config

class AroundPlanner:
    """Planifie des trajectoires de contournement autour de la balle"""
    
    @staticmethod
    def compute_around_waypoint(ball, goal, side=1):
        """
        Calcule un waypoint latéral pour contourner la balle
        
        Args:
            ball: Position (x, y) de la balle
            goal: Position (x, y) du but
            side: +1 pour droite (vu ball->goal), -1 pour gauche
            
        Returns:
            Tuple (x, y): Waypoint de contournement
        """
        # Direction ball -> goal (vecteur unitaire)
        u_bg = FieldUtils.unit_vector(ball, goal)
        
        # Vecteur perpendiculaire (tourné de 90° vers la gauche)
        perp = (-u_bg[1], u_bg[0])
        
        # Application du signe selon le côté choisi
        perp_signed = (perp[0] * side, perp[1] * side)
        
        # Point de base : derrière la balle
        base = (
            ball[0] - u_bg[0] * config.ALIGN_DISTANCE,
            ball[1] - u_bg[1] * config.ALIGN_DISTANCE
        )
        
        # Recherche itérative d'une distance latérale suffisante
        lateral = config.AROUND_DISTANCE_BASE
        max_lateral = config.AROUND_DISTANCE_BASE * config.AROUND_DISTANCE_MAX_FACTOR
        tried = 0
        wp = None
        
        while lateral <= max_lateral:
            # Candidat waypoint
            candidate = (
                base[0] + perp_signed[0] * lateral + u_bg[0] * config.AROUND_FORWARD_OFFSET,
                base[1] + perp_signed[1] * lateral + u_bg[1] * config.AROUND_FORWARD_OFFSET
            )
            
            # Clamp aux limites du terrain
            candidate = FieldUtils.clamp(candidate)
            
            # Vérification de la clearance
            clearance = FieldUtils.dist(candidate, ball)
            
            if clearance >= config.MIN_AROUND_CLEARANCE:
                wp = candidate
                if tried > 0 and config.DEBUG_NAVIGATION:
                    print(f"[AroundPlanner] Élargi lateral={lateral:.3f}m "
                          f"après {tried} essais, clearance={clearance:.3f}m")
                break
            
            # Augmentation progressive de la distance latérale
            lateral *= config.AROUND_DISTANCE_STEP_FACTOR
            tried += 1
        
        # Fallback si aucune solution trouvée
        if wp is None:
            lateral = min(lateral, max_lateral)
            wp = (
                base[0] + perp_signed[0] * lateral + u_bg[0] * config.AROUND_FORWARD_OFFSET,
                base[1] + perp_signed[1] * lateral + u_bg[1] * config.AROUND_FORWARD_OFFSET
            )
            wp = FieldUtils.clamp(wp)
            
            if config.DEBUG_NAVIGATION:
                print(f"[AroundPlanner] WARNING: Clearance insuffisante. "
                      f"Utilisation fallback lateral={lateral:.3f}m")
        
        return wp
    
    @staticmethod
    def choose_side(robot_pos, ball, goal):
        """
        Choisit le meilleur côté pour contourner (gauche ou droite)
        
        Args:
            robot_pos: Position (x, y) du robot
            ball: Position (x, y) de la balle
            goal: Position (x, y) du but
            
        Returns:
            int: -1 pour gauche, +1 pour droite
        """
        # Calcul des deux waypoints possibles
        wp_left = AroundPlanner.compute_around_waypoint(ball, goal, side=-1)
        wp_right = AroundPlanner.compute_around_waypoint(ball, goal, side=+1)
        
        # Choix du plus proche
        dist_left = FieldUtils.dist(robot_pos, wp_left)
        dist_right = FieldUtils.dist(robot_pos, wp_right)
        
        return -1 if dist_left <= dist_right else 1