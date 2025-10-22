# two_robots_shoot_debug_around.py
import math
import time
import rsk
from rsk import constants

# ---------- paramètres à ajuster ----------
ALIGN_DISTANCE = 0.18      # distance derrière la balle où se placer (m)
CAPTURE_DISTANCE = 0.09    # distance à la balle pour déclencher le tir (m)
ANGLE_TOL = math.radians(8) # tolérance d'orientation pour tirer (rad)
MIN_ACTOR_TIME = 0.6       # temps min avant de changer d'acteur (s)
SWITCH_MARGIN = 0.02       # marge de distance pour changer d'acteur (m)
LOOP_DT = 0.05             # période de la boucle principale (s)

# paramètres pour le contournement (pour éviter de pousser la balle)
AROUND_DISTANCE = ALIGN_DISTANCE * 1.2   # distance latérale pour le point de contournement
AROUND_CLEARANCE = 0.02                  # petit offset pour ne pas toucher la balle en waypoint

MAX_FIELD_X = constants.field_length/2.0
MIN_FIELD_X = -constants.field_length/2.0
MAX_FIELD_Y = constants.field_width/2.0
MIN_FIELD_Y = -constants.field_width/2.0

# seuils de détection (tweakables)
ANGLE_THRESHOLD_DEG = 18.0   # angle max (deg) entre robot->ball et robot->goal pour considérer alignement
DOT_MARGIN = 0.0             # produit scalaire strict < DOT_MARGIN => balle "derrière"
DIST_NEARBY = 0.35           # si robot à moins de cette distance, on est dans zone d'interaction

# ---------- helpers ----------
def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def unit_vector_from_to(a, b):
    dx = b[0] - a[0]; dy = b[1] - a[1]
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return (1.0, 0.0)
    return (dx/d, dy/d)

def angle_between(a, b):
    """angle de a->b"""
    return math.atan2(b[1]-a[1], b[0]-a[0])

def wrap(a):
    return (a + math.pi) % (2*math.pi) - math.pi

def behind_point(ball, goal, distance_behind):
    """Point derrière la balle (opposé au goal)."""
    u = unit_vector_from_to(ball, goal)
    return (ball[0] - u[0]*distance_behind, ball[1] - u[1]*distance_behind)

def clamp_to_field(point):
    x = min(max(point[0], MIN_FIELD_X + 0.01), MAX_FIELD_X - 0.01)
    y = min(max(point[1], MIN_FIELD_Y + 0.01), MAX_FIELD_Y - 0.01)
    return (x, y)

# ---------- détection améliorée ----------
def is_robot_between_ball_and_goal(robot_pos, ball, goal, angle_threshold_deg=20):
    """
    Détecte si le robot est *entre* la balle et le but.
    Correction : pour être *entre*, robot->ball et robot->goal sont presque opposés (~180°),
    ET le produit scalaire robot->ball · robot->goal est négatif (la balle est "derrière" le robot).
    angle_threshold_deg ici représente la marge autour de 180° (ex : 20° -> on accepte angles > 180-20 = 160°).
    """
    u_rg = unit_vector_from_to(robot_pos, goal)   # robot -> goal (unitaire)
    v_rb = (ball[0] - robot_pos[0], ball[1] - robot_pos[1])  # robot -> ball
    dot = v_rb[0]*u_rg[0] + v_rb[1]*u_rg[1]
    # angle entre robot->ball et robot->goal (0..180)
    angle_rb = abs(math.degrees(wrap(angle_between(robot_pos, ball) - angle_between(robot_pos, goal))))
    # on considère "between" si dot négatif et angle proche de 180 (i.e. angle_rb > 180 - angle_threshold_deg)
    return (dot < 0.0) and (angle_rb > (180.0 - angle_threshold_deg))

def compute_around_waypoint(ball, goal, side=1):
    """
    Calcule un waypoint latéral pour contourner la balle.
    side = +1 droite (vu ball->goal), -1 gauche.
    """
    u_bg = unit_vector_from_to(ball, goal)  # ball -> goal
    perp = (-u_bg[1], u_bg[0])
    perp_signed = (perp[0] * side, perp[1] * side)
    # base point derrière la balle
    base = (ball[0] - u_bg[0]*ALIGN_DISTANCE, ball[1] - u_bg[1]*ALIGN_DISTANCE)
    wp = (base[0] + perp_signed[0]*AROUND_DISTANCE + u_bg[0]*AROUND_CLEARANCE,
          base[1] + perp_signed[1]*AROUND_DISTANCE + u_bg[1]*AROUND_CLEARANCE)
    return clamp_to_field(wp)

def needs_around(robot_pos, ball, goal):
    """
    Décision : faut-il contourner la balle ?
    - Si robot est clairement *entre* la balle et le but (détecté avec is_robot_between_ball_and_goal) -> True.
    - Sinon, si robot est proche et l'angle robot->ball vs robot->goal est ambigu (risque de pousser),
      on peut aussi décider de contourner (logique conservatrice).
    - IMPORTANT : si la balle est devant (dot > 0), on n'active PAS le contournement.
    """
    # cas principal : robot est entre ball et goal (ball derrière robot) -> contourner
    if is_robot_between_ball_and_goal(robot_pos, ball, goal, angle_threshold_deg=20):
        return True

    # sinon, cas secondaire : robot proche et angle petit MAIS balle devant -> ne pas contourner
    d = dist(robot_pos, ball)
    u_rg = unit_vector_from_to(robot_pos, goal)
    v_rb = (ball[0]-robot_pos[0], ball[1]-robot_pos[1])
    dot = v_rb[0]*u_rg[0] + v_rb[1]*u_rg[1]
    angle_rb_deg = abs(math.degrees(wrap(angle_between(robot_pos, ball) - angle_between(robot_pos, goal))))

    # si la balle est clairement devant (dot > 0.05), ne pas contourner
    if dot > 0.05:
        return False

    # si la balle est légèrement derrière (dot <= 0.05) et robot très proche, et angle pas trop grand -> contourner
    if d < 0.18 and angle_rb_deg < 30.0 and dot < 0.08:
        return True

    return False

# ---------- main amélioré avec logs ----------
def main():
    GOAL = (constants.field_length/2.0, 0.0)  # but adverse pour l'équipe verte

    with rsk.Client() as client:
        print("Client RSK connecté ✅")
        actor = None
        last_switch_time = 0.0

        # État pour le contournement
        around_in_progress = False
        around_wp = None
        around_start_time = 0.0
        AROUND_ARRIVAL_THRESH = 0.06   # distance pour considérer waypoint atteint (m)
        AROUND_TIMEOUT = 3.0           # délai max pour atteindre waypoint (s)



        while True:
            ball = client.ball
            g1_pos = client.green1.position
            g2_pos = client.green2.position

            if ball is None or g1_pos is None or g2_pos is None:
                time.sleep(0.05)
                continue

            # distances
            d1 = dist(g1_pos, ball)
            d2 = dist(g2_pos, ball)

            # choix acteur (avec hystérésis)
            now = time.time()
            if actor is None:
                actor = 'green1' if d1 <= d2 else 'green2'
                last_switch_time = now
            else:
                if now - last_switch_time > MIN_ACTOR_TIME:
                    if actor == 'green1' and d2 + SWITCH_MARGIN < d1:
                        actor = 'green2'; last_switch_time = now
                    elif actor == 'green2' and d1 + SWITCH_MARGIN < d2:
                        actor = 'green1'; last_switch_time = now

            # références
            if actor == 'green1':
                active = client.green1
                passive = client.green2
            else:
                active = client.green2
                passive = client.green1

            rpos = active.position
            # Diagnostics : calculs utiles
            d_to_ball = dist(rpos, ball)
            u_rg = unit_vector_from_to(rpos, GOAL)
            v_rb = (ball[0]-rpos[0], ball[1]-rpos[1])
            dot = v_rb[0]*u_rg[0] + v_rb[1]*u_rg[1]
            angle_rb_deg = abs(math.degrees(wrap(angle_between(rpos, ball) - angle_between(rpos, GOAL))))

            # Affiche diagnostics — très utile pour comprendre pourquoi besoin de contournement non déclenché
            print("---- DIAG ----")
            print(f"actor={actor} d1={d1:.3f} d2={d2:.3f} d_to_ball={d_to_ball:.3f}")
            print(f"angle_rb_deg={angle_rb_deg:.2f} dot={dot:.4f} (DIST_NEARBY={DIST_NEARBY})")
            # evaluation besoin contournement
            need = needs_around(rpos, ball, GOAL)
            print(f"needs_around -> {need}")
            print("--------------")

            # si besoin de contourner, calculer waypoint gauche/droite et y aller

            # ---------- GESTION ROBUSTE DU CONTOURNEMENT ----------
            if need:
                # Si on n'est pas déjà en train de contourner, initialiser le contournement
                if not around_in_progress:
                    wp_left = compute_around_waypoint(ball, GOAL, side=-1)
                    wp_right = compute_around_waypoint(ball, GOAL, side=+1)
                    if dist(rpos, wp_left) <= dist(rpos, wp_right):
                        around_wp = wp_left
                        side_str = "left"
                    else:
                        around_wp = wp_right
                        side_str = "right"

                    # enregistre l'état de contournement
                    around_in_progress = True
                    around_start_time = time.time()

                    print(f"[{actor}] situation 'robot entre balle & but' détectée -> contourner par la {side_str}, waypoint={around_wp}")
                    # envoi unique de la commande (non bloquante pour pouvoir monitorer)
                    try:
                        active.goto((around_wp[0], around_wp[1], 0.0), wait=False)
                    except Exception as e:
                        print(f"[{actor}] goto(around_wp) a échoué immédiatement: {e}")
                        # on reste en mode around pour essayer des nudges plus bas

                    # placer le robot passif pendant le contournement
                    #passive.goto((-0.3, 0.0, 0.0), wait=False)
                    time.sleep(LOOP_DT)
                    continue

                else:
                    # déjà en contournement : vérifier arrivée ou timeout
                    elapsed = time.time() - around_start_time
                    # recalculer distance actuelle au waypoint
                    if around_wp is not None:
                        d_to_wp = dist(rpos, around_wp)
                    else:
                        d_to_wp = 999.0

                    # arrivé ?
                    if d_to_wp <= AROUND_ARRIVAL_THRESH:
                        print(f"[{actor}] Arrivé au waypoint de contournement (d={d_to_wp:.3f}). Sortie du contournement.")
                        around_in_progress = False
                        around_wp = None
                        around_start_time = 0.0
                        # petite pause pour stabiliser le robot
                        time.sleep(0.05)
                        continue

                    # timeout ?
                    if elapsed > AROUND_TIMEOUT:
                        print(f"[{actor}] Timeout contournement (elapsed={elapsed:.2f}s, d_to_wp={d_to_wp:.3f}). Tentative de nudge et abandon.")
                        # tentative d'un petit nudge pour sortir d'un blocage potentiel
                        try:
                            # petit coup de control pour pousser latéralement (nudge)
                            active.control(0.0, 0.06, 0.0)  # léger déplacement latéral (si supporté)
                            time.sleep(0.12)
                            active.control(0.0, 0.0, 0.0)
                        except Exception:
                            # si .control indisponible ou erreur, on ignore
                            pass

                        around_in_progress = False
                        around_wp = None
                        around_start_time = 0.0
                        time.sleep(0.05)
                        continue

                    # sinon : on attend que le robot avance vers le waypoint (on réémet goto rarement)
                    # réémettre goto seulement si long time sans progression (sécurité)
                    # on surveille donc sans spam
                    time.sleep(LOOP_DT)
                    continue
            # ---------- FIN GESTION CONTOURNEMENT ----------


            # sinon comportement normal : aller au point 'behind'
            behind = behind_point(ball, GOAL, ALIGN_DISTANCE)
            arrived_align = active.goto((behind[0], behind[1], 0.0), wait=False)
            if not arrived_align:
                print(f"[{actor}] moving to behind point {behind}")
                #passive.goto((-0.3, 0.0, 0.0), wait=False)
                time.sleep(LOOP_DT)
                continue

            # une fois derrière -> orienter vers but, vérifier alignement, approcher, kicker (inchangé)
            rpos = active.position
            rtheta = active.orientation
            desired_theta = angle_between(rpos, GOAL)
            ang_err = wrap(desired_theta - rtheta)
            if abs(ang_err) > ANGLE_TOL:
                print(f"[{actor}] orienting to goal (err {math.degrees(ang_err):.1f} deg)")
                active.goto((rpos[0], rpos[1], desired_theta), wait=True)
                time.sleep(0.05)

            # vérifier alignement robot->ball vs robot->goal
            angle_rb = wrap(angle_between(rpos, ball) - angle_between(rpos, GOAL))
            u_rg = unit_vector_from_to(rpos, GOAL)
            v_rb = (ball[0]-rpos[0], ball[1]-rpos[1])
            dot = v_rb[0]*u_rg[0] + v_rb[1]*u_rg[1]
            aligned = (abs(angle_rb) < math.radians(12)) and (dot > 0.01)

            if not aligned:
                print(f"[{actor}] recaling straight to ball before kick (angle_rb={math.degrees(angle_rb):.1f}, dot={dot:.3f})")
                approach_point = (ball[0] - u_rg[0]*0.01, ball[1] - u_rg[1]*0.01)
                active.goto((approach_point[0], approach_point[1], desired_theta), wait=False)
                time.sleep(LOOP_DT)
                continue

            # approche finale et kick
            d_to_ball = dist(rpos, ball)
            if d_to_ball > CAPTURE_DISTANCE:
                print(f"[{actor}] final approach to ball (d={d_to_ball:.3f} m)")
                target_pos = (ball[0] - u_rg[0]*0.02, ball[1] - u_rg[1]*0.02, desired_theta)
                active.goto(target_pos, wait=True)
                time.sleep(0.02)

            rpos = active.position
            rtheta = active.orientation
            if dist(rpos, ball) <= CAPTURE_DISTANCE and abs(wrap(angle_between(rpos, GOAL) - rtheta)) <= ANGLE_TOL:
                try:
                    print(f"[{actor}] KICK !")
                    active.kick()
                except rsk.ClientError:
                    print("Erreur lors du kick (préemption ou erreur client).")
                active.goto((rpos[0] - u_rg[0]*0.10, rpos[1] - u_rg[1]*0.10, rtheta), wait=True)
                actor = None
                last_switch_time = time.time()
                time.sleep(0.5)

            #passive.goto((-0.3, 0.0, 0.0), wait=False)
            time.sleep(LOOP_DT)

if __name__ == "__main__":
    main()
