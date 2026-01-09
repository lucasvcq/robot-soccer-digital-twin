<<<<<<< HEAD
# two_robots_shoot_aligned.py
=======
# two_robots_shoot_debug_around.py
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
import math
import time
import rsk
from rsk import constants

# ---------- paramètres à ajuster ----------
<<<<<<< HEAD
ALIGN_DISTANCE = 0.2      # distance derrière la balle où se placer (m)
CAPTURE_DISTANCE = 0.1    # distance à la balle pour déclencher le tir (m)
=======
ALIGN_DISTANCE = 0.18      # distance derrière la balle où se placer (m)
CAPTURE_DISTANCE = 0.09    # distance à la balle pour déclencher le tir (m)
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
ANGLE_TOL = math.radians(8) # tolérance d'orientation pour tirer (rad)
MIN_ACTOR_TIME = 0.6       # temps min avant de changer d'acteur (s)
SWITCH_MARGIN = 0.02       # marge de distance pour changer d'acteur (m)
LOOP_DT = 0.05             # période de la boucle principale (s)

<<<<<<< HEAD
# helper math
=======
# clearance minimale entre le waypoint et la balle (m). Assure que le robot ne frôle pas la balle.
MIN_AROUND_CLEARANCE = 0.12   # 10 cm par défaut — augmente si le robot continue de toucher la balle
# multiplicateur initial et maximum appliqué à la distance latérale de base
AROUND_DISTANCE_BASE = ALIGN_DISTANCE * 1.2
AROUND_DISTANCE_MAX_FACTOR = 3.0
AROUND_DISTANCE_STEP_FACTOR = 1.25  # facteur multiplicatif appliqué à chaque essai
# petit offset pour éviter d'être exactement sur la ligne de tir (en avant du point de contournement)
AROUND_FORWARD_OFFSET = 0.02

MAX_FIELD_X = constants.field_length/2.0
MIN_FIELD_X = -constants.field_length/2.0
MAX_FIELD_Y = constants.field_width/2.0
MIN_FIELD_Y = -constants.field_width/2.0

# seuils de détection (tweakables)
ANGLE_THRESHOLD_DEG = 18.0   # angle max (deg) entre robot->ball et robot->goal pour considérer alignement
DOT_MARGIN = 0.0             # produit scalaire strict < DOT_MARGIN => balle "derrière"
DIST_NEARBY = 0.35           # si robot à moins de cette distance, on est dans zone d'interaction

# ---------- helpers ----------
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
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

<<<<<<< HEAD
# point "behind" the ball relative to the goal:
def behind_point(ball, goal, distance_behind):
    # direction from ball to goal:
    u = unit_vector_from_to(ball, goal)
    # behind = ball - u * distance_behind (côté opposé au but)
    return (ball[0] - u[0]*distance_behind, ball[1] - u[1]*distance_behind)

# vérifie si robot est orienté vers target avec tolérance angulaire
def is_oriented(robot_theta, robot_pos, target_pos, tol=ANGLE_TOL):
    desired = angle_between(robot_pos, target_pos)
    return abs(wrap(desired - robot_theta)) <= tol

# main
=======
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
    Calcule un waypoint latéral pour contourner la balle en garantissant une clearance minimale.
    side = +1 pour droite (vu ball->goal), -1 pour gauche.
    La fonction essaie d'augmenter progressivement la distance latérale si le waypoint est trop proche de la balle.
    """
    # direction ball -> goal (unitaire)
    u_bg = unit_vector_from_to(ball, goal)
    # vecteur perpendiculaire (left) and signed
    perp = (-u_bg[1], u_bg[0])
    perp_signed = (perp[0] * side, perp[1] * side)

    # point de base : derrière la balle (pour viser la trajectoire de tir ensuite)
    base = (ball[0] - u_bg[0]*ALIGN_DISTANCE, ball[1] - u_bg[1]*ALIGN_DISTANCE)

    # on cherche un lateral_distance qui respecte la clearance minimale
    lateral = AROUND_DISTANCE_BASE
    tried = 0
    wp = None
    while lateral <= AROUND_DISTANCE_BASE * AROUND_DISTANCE_MAX_FACTOR:
        # construire waypoint candidate
        candidate = (
            base[0] + perp_signed[0]*lateral + u_bg[0]*AROUND_FORWARD_OFFSET,
            base[1] + perp_signed[1]*lateral + u_bg[1]*AROUND_FORWARD_OFFSET
        )
        # clamp to field (évite de générer waypoint hors-terrain)
        candidate = clamp_to_field(candidate)
        # calcul clearance (distance waypoint -> ball)
        clearance = dist(candidate, ball)
        # si clearance suffisante, on a trouvé le waypoint
        if clearance >= MIN_AROUND_CLEARANCE:
            wp = candidate
            if tried > 0:
                print(f"[compute_around_waypoint] élargi lateral={lateral:.3f}m après {tried} essais, clearance={clearance:.3f}m")
            break
        # sinon augmenter lateral et réessayer
        lateral *= AROUND_DISTANCE_STEP_FACTOR
        tried += 1

    # si on n'a rien trouvé (peu probable), utilise le dernier candidat clamped, mais note le warning
    if wp is None:
        # fallback : prendre dernier candidate calculé (peut être clamped)
        lateral = min(lateral, AROUND_DISTANCE_BASE * AROUND_DISTANCE_MAX_FACTOR)
        wp = (
            base[0] + perp_signed[0]*lateral + u_bg[0]*AROUND_FORWARD_OFFSET,
            base[1] + perp_signed[1]*lateral + u_bg[1]*AROUND_FORWARD_OFFSET
        )
        wp = clamp_to_field(wp)
        print(f"[compute_around_waypoint] WARNING: clearance insuffisante (dernier clearance={dist(wp, ball):.3f}m). Utilisation fallback.")

    return wp

def needs_around(robot_pos, ball, goal):
    """
    Décision améliorée et stabilisée :
    Détermine s’il faut contourner la balle pour se placer derrière.
    Corrige le cas où le robot est déjà derrière mais un peu mal orienté.
    """

    # seuils
    FRONT_DOT = 0.12        # >0.12 : balle devant
    FRONT_ANGLE_DEG = 55.0  # <55° : balle globalement devant, bon axe
    SIDE_ANGLE_DEG = 70.0   # >70° : balle clairement sur le côté
    DIST_CLOSE = 0.35       # distance courte → prudence pour contournement

    # vecteurs
    u_rg = unit_vector_from_to(robot_pos, goal)        # robot → goal
    v_rb = (ball[0] - robot_pos[0], ball[1] - robot_pos[1])  # robot → ball
    d = dist(robot_pos, ball)
    dot = v_rb[0]*u_rg[0] + v_rb[1]*u_rg[1]
    angle_rb_deg = abs(math.degrees(wrap(angle_between(robot_pos, ball) - angle_between(robot_pos, goal))))

    # DIAG
    print("---- DIAG ----")
    print(f"angle_rb_deg={angle_rb_deg:.2f} dot={dot:.4f} d_to_ball={d:.3f}")

    # ✅ Cas 1 : balle bien devant, alignée -> pas besoin de contourner
    if (dot > FRONT_DOT) and (angle_rb_deg < FRONT_ANGLE_DEG):
        return False

    # ✅ Cas 2 : balle sur le côté ou très mal alignée -> contourner
    if (dot < 0) or (angle_rb_deg > SIDE_ANGLE_DEG):
        return True

    # ✅ Cas 3 : balle proche -> prudence
    # si proche et pas parfaitement dans l'axe, contourner
    if (d < DIST_CLOSE) and ((dot < 0.2) or (angle_rb_deg > 45.0)):
        return True

    # ✅ Cas 4 : robot clairement entre balle & but
    if is_robot_between_ball_and_goal(robot_pos, ball, goal, angle_threshold_deg=25):
        return True

    # sinon, pas besoin de contourner
    return False

# ---------- main amélioré avec logs ----------
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
def main():
    GOAL = (constants.field_length/2.0, 0.0)  # but adverse pour l'équipe verte

    with rsk.Client() as client:
        print("Client RSK connecté ✅")
        actor = None
        last_switch_time = 0.0

<<<<<<< HEAD
        while True:
            # récupération des positions
=======
        # État pour le contournement
        around_in_progress = False
        around_wp = None
        around_start_time = 0.0
        AROUND_ARRIVAL_THRESH = 0.06   # distance pour considérer waypoint atteint (m)
        AROUND_TIMEOUT = 3.0           # délai max pour atteindre waypoint (s)



        while True:
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
            ball = client.ball
            g1_pos = client.green1.position
            g2_pos = client.green2.position

            if ball is None or g1_pos is None or g2_pos is None:
<<<<<<< HEAD
                # attente si détection manquante
=======
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
                time.sleep(0.05)
                continue

            # distances
            d1 = dist(g1_pos, ball)
            d2 = dist(g2_pos, ball)

<<<<<<< HEAD
            # sélection du robot le plus proche avec hystérésis :
            # on ne change d'acteur que si le nouveau est significativement plus proche
=======
            # choix acteur (avec hystérésis)
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
            now = time.time()
            if actor is None:
                actor = 'green1' if d1 <= d2 else 'green2'
                last_switch_time = now
            else:
<<<<<<< HEAD
                # si délai min écoulé et l'autre robot est plus proche de > SWITCH_MARGIN
=======
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
                if now - last_switch_time > MIN_ACTOR_TIME:
                    if actor == 'green1' and d2 + SWITCH_MARGIN < d1:
                        actor = 'green2'; last_switch_time = now
                    elif actor == 'green2' and d1 + SWITCH_MARGIN < d2:
                        actor = 'green1'; last_switch_time = now

<<<<<<< HEAD
            # référence aux objets client
=======
            # références
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
            if actor == 'green1':
                active = client.green1
                passive = client.green2
            else:
                active = client.green2
                passive = client.green1

<<<<<<< HEAD
            # calcule le point derrière la balle relatif au but
            behind = behind_point(ball, GOAL, ALIGN_DISTANCE)

            # statut d'arrivée sur le point d'alignement (goto(..., wait=False) renvoie True si déjà arrivé)
            # on utilise non-blocking goto pour contrôler l'état
            arrived_align = active.goto((behind[0], behind[1], 0.0), wait=False)

            # si pas encore aligné spatialement -> continuer vers behind
            if not arrived_align:
                # on peut aussi vérifier orientation et corriger si nécessaire, mais goto fait déjà du positionnement
                #print(f"[{actor}] moving to behind point {behind}")
                # mettre passive en position de soutien
=======
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
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
                #passive.goto((-0.3, 0.0, 0.0), wait=False)
                time.sleep(LOOP_DT)
                continue

<<<<<<< HEAD
            # une fois au point derrière la balle, orienter vers le but
            rpos = active.position
            rtheta = active.orientation
            # orientation souhaitée pour tirer (du robot vers le but)
            desired_theta = angle_between(rpos, GOAL)
            ang_err = wrap(desired_theta - rtheta)

            if abs(ang_err) > ANGLE_TOL:
                # on effectue une petite goto qui fixe la theta (même position x,y mais theta orientée vers goal)
                print(f"[{actor}] orienting to goal (err {math.degrees(ang_err):.1f} deg)")
                active.goto((rpos[0], rpos[1], desired_theta), wait=True)
                # après orientation, vérifier encore
                time.sleep(0.05)

            # maintenant on vérifie que la position du robot, la balle et le goal sont alignés
            # c.-à-d. la projection de la balle sur la ligne robot->goal doit être entre robot et goal, et la balle devant le robot
            # pour simplifier : on vérifie que l'angle robot->ball par rapport à robot->goal est petit (alignement) et que la balle est devant
            angle_rb = wrap(angle_between(rpos, ball) - angle_between(rpos, GOAL))
            # vecteur robot->ball
            v_rb = (ball[0]-rpos[0], ball[1]-rpos[1])
            # produit scalaire entre robot->goal et robot->ball pour vérifier "devant"
            u_rg = unit_vector_from_to(rpos, GOAL)
            dot = v_rb[0]*u_rg[0] + v_rb[1]*u_rg[1]

            aligned = (abs(angle_rb) < math.radians(12)) and (dot > 0.01)

            if not aligned:
                # si pas bien aligné (ex : balle pas exactement devant), on se recale légèrement : on approche la balle tout droit en limitant la vitesse
                print(f"[{actor}] recaling straight to ball before kick (angle_rb={math.degrees(angle_rb):.1f}, dot={dot:.3f})")
                # on ordonne un goto très proche de la balle avec theta orienté vers goal pour "pousser droit"
                approach_point = (ball[0] - u_rg[0]*0.01, ball[1] - u_rg[1]*0.01)  # petit offset pour ne pas superposer
=======
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
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
                active.goto((approach_point[0], approach_point[1], desired_theta), wait=False)
                time.sleep(LOOP_DT)
                continue

<<<<<<< HEAD
            # si on est bien placé et orienté, on s'approche doucement vers la balle et kick
            d_to_ball = dist(rpos, ball)
            if d_to_ball > CAPTURE_DISTANCE:
                print(f"[{actor}] final approach to ball (d={d_to_ball:.3f} m)")
                # goto position très proche de la balle, en bloquant pour arriver proprement
                target_theta = desired_theta
                target_pos = (ball[0] - u_rg[0]*0.02, ball[1] - u_rg[1]*0.02, target_theta)
                active.goto(target_pos, wait=True)
                time.sleep(0.02)

            # Recalcule position juste avant le kick et vérifie orientation
            rpos = active.position
            rtheta = active.orientation
            if dist(rpos, ball) <= CAPTURE_DISTANCE and is_oriented(rtheta, rpos, GOAL):
=======
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
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
                try:
                    print(f"[{actor}] KICK !")
                    active.kick()
                except rsk.ClientError:
                    print("Erreur lors du kick (préemption ou erreur client).")
<<<<<<< HEAD
                # après le kick, reculer un peu puis reset acteur
=======
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
                active.goto((rpos[0] - u_rg[0]*0.10, rpos[1] - u_rg[1]*0.10, rtheta), wait=True)
                actor = None
                last_switch_time = time.time()
                time.sleep(0.5)

<<<<<<< HEAD
            # remet le robot passif en place (soutien)
            #passive.goto((-0.3, 0.0, 0.0), wait=False)

=======
            #passive.goto((-0.3, 0.0, 0.0), wait=False)
>>>>>>> 5611e1ab18bf8966a3d9a84b895a44a4ea268b7a
            time.sleep(LOOP_DT)

if __name__ == "__main__":
    main()
