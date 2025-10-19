# two_robots_shoot_aligned.py
import math
import time
import rsk
from rsk import constants

# ---------- paramètres à ajuster ----------
ALIGN_DISTANCE = 0.2      # distance derrière la balle où se placer (m)
CAPTURE_DISTANCE = 0.1    # distance à la balle pour déclencher le tir (m)
ANGLE_TOL = math.radians(8) # tolérance d'orientation pour tirer (rad)
MIN_ACTOR_TIME = 0.6       # temps min avant de changer d'acteur (s)
SWITCH_MARGIN = 0.02       # marge de distance pour changer d'acteur (m)
LOOP_DT = 0.05             # période de la boucle principale (s)

# helper math
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
def main():
    GOAL = (constants.field_length/2.0, 0.0)  # but adverse pour l'équipe verte

    with rsk.Client() as client:
        print("Client RSK connecté ✅")
        actor = None
        last_switch_time = 0.0

        while True:
            # récupération des positions
            ball = client.ball
            g1_pos = client.green1.position
            g2_pos = client.green2.position

            if ball is None or g1_pos is None or g2_pos is None:
                # attente si détection manquante
                time.sleep(0.05)
                continue

            # distances
            d1 = dist(g1_pos, ball)
            d2 = dist(g2_pos, ball)

            # sélection du robot le plus proche avec hystérésis :
            # on ne change d'acteur que si le nouveau est significativement plus proche
            now = time.time()
            if actor is None:
                actor = 'green1' if d1 <= d2 else 'green2'
                last_switch_time = now
            else:
                # si délai min écoulé et l'autre robot est plus proche de > SWITCH_MARGIN
                if now - last_switch_time > MIN_ACTOR_TIME:
                    if actor == 'green1' and d2 + SWITCH_MARGIN < d1:
                        actor = 'green2'; last_switch_time = now
                    elif actor == 'green2' and d1 + SWITCH_MARGIN < d2:
                        actor = 'green1'; last_switch_time = now

            # référence aux objets client
            if actor == 'green1':
                active = client.green1
                passive = client.green2
            else:
                active = client.green2
                passive = client.green1

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
                #passive.goto((-0.3, 0.0, 0.0), wait=False)
                time.sleep(LOOP_DT)
                continue

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
                active.goto((approach_point[0], approach_point[1], desired_theta), wait=False)
                time.sleep(LOOP_DT)
                continue

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
                try:
                    print(f"[{actor}] KICK !")
                    active.kick()
                except rsk.ClientError:
                    print("Erreur lors du kick (préemption ou erreur client).")
                # après le kick, reculer un peu puis reset acteur
                active.goto((rpos[0] - u_rg[0]*0.10, rpos[1] - u_rg[1]*0.10, rtheta), wait=True)
                actor = None
                last_switch_time = time.time()
                time.sleep(0.5)

            # remet le robot passif en place (soutien)
            #passive.goto((-0.3, 0.0, 0.0), wait=False)

            time.sleep(LOOP_DT)

if __name__ == "__main__":
    main()
