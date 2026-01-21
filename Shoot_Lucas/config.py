"""
Configuration centralisée pour le Robot Soccer Kit
Tous les paramètres de jeu sont ici pour un tuning facile
"""
import math

# ============================================================================
# PARAMÈTRES DE NAVIGATION
# ============================================================================

# Distance derrière la balle pour se positionner (m)
ALIGN_DISTANCE = 0.15

# Distance à la balle pour déclencher le tir (m)
CAPTURE_DISTANCE = 0.13

# Tolérance d'orientation pour tirer (radians)
ANGLE_TOL = math.radians(8)

# Période de la boucle principale (secondes)
LOOP_DT = 0.05

# Distance minimale autorisée par rapport au but adverse (m)
# Le robot ne peut pas s'approcher plus près du but que cette distance
MIN_DISTANCE_TO_GOAL = 0.45  # 45cm minimum

# ============================================================================
# PARAMÈTRES DE CHANGEMENT D'ACTEUR
# ============================================================================

# Temps minimum avant de changer d'acteur (secondes)
MIN_ACTOR_TIME = 0.6

# Marge de distance pour déclencher un changement d'acteur (m)
SWITCH_MARGIN = 0.02

# ============================================================================
# PARAMÈTRES DE CONTOURNEMENT (AroundPlanner)
# ============================================================================

# Clearance minimale entre le waypoint et la balle (m)
MIN_AROUND_CLEARANCE = 0.12

# Distance latérale de base pour le contournement (m)
AROUND_DISTANCE_BASE = ALIGN_DISTANCE * 1.2

# Facteur maximum de distance latérale
AROUND_DISTANCE_MAX_FACTOR = 3.0

# Facteur multiplicatif appliqué à chaque essai
AROUND_DISTANCE_STEP_FACTOR = 1.25

# Petit offset pour éviter d'être sur la ligne de tir (m)
AROUND_FORWARD_OFFSET = 0.02

# Distance pour considérer un waypoint atteint (m)
AROUND_ARRIVAL_THRESH = 0.05

# Délai maximum pour atteindre un waypoint (secondes)
AROUND_TIMEOUT = 3.0

# ============================================================================
# PARAMÈTRES DE DÉTECTION (needs_around)
# ============================================================================

# Produit scalaire minimal pour considérer la balle devant
FRONT_DOT = 0.12

# Angle maximum pour considérer la balle devant (degrés)
FRONT_ANGLE_DEG = 55.0

# Angle minimum pour considérer la balle sur le côté (degrés)
SIDE_ANGLE_DEG = 70.0

# Distance considérée comme "proche" (m)
DIST_CLOSE = 0.35

# Angle pour déterminer si un robot est entre la balle et le but (degrés)
BETWEEN_ANGLE_THRESH_DEG = 25.0

# ============================================================================
# PARAMÈTRES DE STRATÉGIE D'ÉQUIPE
# ============================================================================

# Distance devant le receveur pour la passe (m)
# AUGMENTÉE pour que le receveur soit plus proche du but
PASS_DEPTH_OFFSET = 0.60  # 60cm devant (au lieu de 40cm)

# Décalage latéral du receveur pour éviter le centre (m)
# Le receveur ira à Y = ±PASS_LATERAL_OFFSET selon la position de la balle
# AUGMENTÉE pour qu'il soit vraiment sur le côté
PASS_LATERAL_OFFSET = 0.50  # 50cm du centre (au lieu de 35cm)

# Si l'attaquant est plus loin que cette distance, il envisage la passe (m)
DIST_SHOOT_LIMIT = 1.0

# Marge pour considérer qu'un coéquipier est "devant" (m)
TEAMMATE_AHEAD_MARGIN = 0.10

# Marge de sécurité par rapport aux limites du terrain (m)
FIELD_MARGIN = 0.20

# Distance de soutien derrière l'attaquant (m)
SUPPORT_OFFSET = 0.50

# Distance latérale pour le positionnement de soutien (m)
SUPPORT_LATERAL_OFFSET = 0.30

# ============================================================================
# PARAMÈTRES DE PUISSANCE
# ============================================================================

# Puissance maximale pour un tir au but
POWER_SHOOT = 1.0

# Puissance pour une passe (dosée)
POWER_PASS = 0.6

# ============================================================================
# PARAMÈTRES DU TERRAIN
# ============================================================================

# Position X du but adverse (à ajuster selon le côté)
# -1.83/2 pour attaquer vers la gauche
# +1.83/2 pour attaquer vers la droite
GOAL_X = -1.83 / 2

# Position complète du but (X, Y)
GOAL_POSITION = (GOAL_X, 0.0)

# ============================================================================
# ZONES INTERDITES (Surface de réparation)
# ============================================================================

# Dimensions de la zone interdite devant chaque but
PENALTY_AREA_DEPTH = 0.30   # Profondeur de la zone (30cm)
PENALTY_AREA_WIDTH = 0.90   # Largeur de la zone (90cm)

# Marge de sécurité pour éviter d'entrer dans la zone
# AUGMENTÉE pour plus de prudence
PENALTY_AREA_MARGIN = 0.15  # 10cm de marge (au lieu de 5cm)

# ============================================================================
# PARAMÈTRES DE DEBUG
# ============================================================================

# Afficher les messages de debug détaillés
DEBUG_VERBOSE = False

# Afficher les décisions stratégiques
DEBUG_STRATEGY = False

# Afficher les informations de navigation
DEBUG_NAVIGATION = False