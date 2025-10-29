import math
from field_utils import FieldUtils
import config

class AroundPlanner:

    @staticmethod
    def compute_around_waypoint(ball, goal, side=1):
        """
        Calcule un waypoint latéral pour contourner la balle.
        side = +1 pour droite (vu ball->goal), -1 pour gauche.
        """
        # direction ball -> goal (unitaire)
        u_bg = FieldUtils.unit_vector(ball, goal)
        # vecteur perpendiculaire (left) and signed
        perp = (-u_bg[1], u_bg[0])
        perp_signed = (perp[0] * side, perp[1] * side)

        # point de base : derrière la balle
        base = (ball[0] - u_bg[0]*config.ALIGN_DISTANCE, ball[1] - u_bg[1]*config.ALIGN_DISTANCE)

        lateral = config.AROUND_DISTANCE_BASE
        tried = 0
        wp = None
        
        max_lateral = config.AROUND_DISTANCE_BASE * config.AROUND_DISTANCE_MAX_FACTOR
        
        while lateral <= max_lateral:
            candidate = (
                base[0] + perp_signed[0]*lateral + u_bg[0]*config.AROUND_FORWARD_OFFSET,
                base[1] + perp_signed[1]*lateral + u_bg[1]*config.AROUND_FORWARD_OFFSET
            )
            candidate = FieldUtils.clamp(candidate)
            clearance = FieldUtils.dist(candidate, ball)

            if clearance >= config.MIN_AROUND_CLEARANCE:
                wp = candidate
                if tried > 0:
                    print(f"[AroundPlanner] élargi lateral={lateral:.3f}m après {tried} essais, clearance={clearance:.3f}m")
                break
            
            lateral *= config.AROUND_DISTANCE_STEP_FACTOR
            tried += 1

        if wp is None:
            lateral = min(lateral, max_lateral)
            wp = (
                base[0] + perp_signed[0]*lateral + u_bg[0]*config.AROUND_FORWARD_OFFSET,
                base[1] + perp_signed[1]*lateral + u_bg[1]*config.AROUND_FORWARD_OFFSET
            )
            wp = FieldUtils.clamp(wp)
            print(f"[AroundPlanner] WARNING: clearance insuffisante. Utilisation fallback.")

        return wp