import math

# --- Constantes de jeu ---
ALIGN_DISTANCE = 0.18      # distance derrière la balle où se placer (m)
CAPTURE_DISTANCE = 0.13    # distance à la balle pour déclencher le tir (m)
ANGLE_TOL = math.radians(8) # tolérance d'orientation pour tirer (rad)
LOOP_DT = 0.05             # période de la boucle principale (s)
KICK_MAX_DIST = 0.5  # À 0.5 mètres ou plus, on tire à puissance 1.0 (max)

# --- Constantes de changement d'acteur ---
MIN_ACTOR_TIME = 0.6       # temps min avant de changer d'acteur (s)
SWITCH_MARGIN = 0.02       # marge de distance pour changer d'acteur (m)

# --- Constantes de contournement (AroundPlanner) ---
MIN_AROUND_CLEARANCE = 0.12   # clearance minimale entre le waypoint et la balle (m).
AROUND_DISTANCE_BASE = ALIGN_DISTANCE * 1.2 # multiplicateur initial
AROUND_DISTANCE_MAX_FACTOR = 3.0
AROUND_DISTANCE_STEP_FACTOR = 1.25  # facteur multiplicatif appliqué à chaque essai
AROUND_FORWARD_OFFSET = 0.02 # petit offset pour éviter d'être sur la ligne de tir
AROUND_ARRIVAL_THRESH = 0.1   # distance pour considérer waypoint atteint (m)
AROUND_TIMEOUT = 3.0           # délai max pour atteindre waypoint (s)

# --- Constantes de détection (needs_around) ---
FRONT_DOT = 0.12        # >0.12 : balle devant
FRONT_ANGLE_DEG = 55.0  # <55° : balle globalement devant, bon axe
SIDE_ANGLE_DEG = 70.0   # >70° : balle clairement sur le côté
DIST_CLOSE = 0.35       # distance courte → prudence pour contournement
BETWEEN_ANGLE_THRESH_DEG = 25.0 # Angle pour "is_robot_between_ball_and_goal"