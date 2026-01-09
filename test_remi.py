from math import sqrt, cos, sin, atan2, pi

class remi:
    def __init__(self, client):
        self.client = client

    def distance_objectif(self, robot, objectif):
        C = robot.position
        B = objectif
        D = (C[0] - B[0], C[1] - B[1])
        return sqrt(D[0]**2 + D[1]**2)

    def vecteur_direction(self, robot, objectif):
        # retourne le vecteur (raw) du robot vers l'objectif (non normalisé)
        C = robot.position
        B = objectif
        return (B[0] - C[0], B[1] - C[1])
    
    def avance(self, vecteur, vitesse):
        vx, vy = vecteur
        # on arrondit la direction puis on scale par la vitesse
        # si vecteur est déjà normalisé, vitesse sera la vitesse finale
        vx = round(vx, 2) * vitesse
        vy = round(vy, 2) * vitesse
        return vx, vy

    def vecteur_robot(self, robot, objectif):
        """Vecteur vers l'objectif dans le repère du robot (normalisé)"""
        vx_terrain, vy_terrain = self.vecteur_direction(robot, objectif)
        theta = robot.orientation
        # rotation: global -> robot
        vx = cos(theta) * vx_terrain + sin(theta) * vy_terrain
        vy = -sin(theta) * vx_terrain + cos(theta) * vy_terrain
        norme = sqrt(vx**2 + vy**2)
        if norme != 0:
            vx_robot = vx / norme
            vy_robot = vy / norme
        else:
            vx_robot, vy_robot = 0.0, 0.0
        return (vx_robot, vy_robot)
    
    def distance_players(self, robot):
        """Renvoie une liste (player, distance) pour les autres joueurs
           en utilisant les objets clients (si présents)."""
        players = []
        # protège si client ou robots manquent
        try:
            players = [self.client.green1, self.client.green2, self.client.blue1, self.client.blue2]
        except Exception:
            players = []

        distance_player = []
        for player in players:
            if player is None:
                continue
            # évite de comparer l'objet identique
            if robot is not player:
                pos_adv = player.position
                ecart_x = robot.position[0] - pos_adv[0]
                ecart_y = robot.position[1] - pos_adv[1]
                distance = sqrt(ecart_x**2 + ecart_y**2)
                distance_player.append((player, distance))
        return distance_player

    def distance_players_to_ball(self,ball):
        """
        Renvoie une liste de tuples (player, distance) représentant 
        la distance entre la balle et chaque joueur présent sur le terrain.
        """
        try:
            ball_pos = ball
        except Exception:
            print("Erreur : Impossible de récupérer la position de la balle.")
            return []
        try:
            players = [self.client.green1, self.client.green2, self.client.blue1, self.client.blue2]
        except Exception:
            players = []
        distance_to_ball = []
        for player in players:
            if player is not None:
                player_pos = player.position
                ecart_x = ball_pos[0] - player_pos[0]
                ecart_y = ball_pos[1] - player_pos[1]
                distance = sqrt(ecart_x**2 + ecart_y**2)
                distance_to_ball.append((player, distance))

        return distance_to_ball

    def evite(self, robot, seuil_player, force):
        """Renvoie [ (repulsion_x, repulsion_y), facteur ].
           - repulsion est un vecteur (dans le repère robot) normalisé si non nul.
           - facteur est un nombre entre 0 et 1 qui représente l'intensité max appliquée.
        """
        x, y = 0.0, 0.0
        distances = self.distance_players(robot)
        theta = robot.orientation
        facteur_max = 0.0

        for player, dist in distances:
            if dist < seuil_player and dist > 0:
                dx = robot.position[0] - player.position[0]
                dy = robot.position[1] - player.position[1]
                # facteur local proportionnel à la proximité
                facteur_local = (seuil_player - dist) / seuil_player  # dans (0,1]
                # contribution pondérée par la force et la direction (normalisée par dist)
                # protection dist != 0 déjà faite
                contrib_x = (force * dx / dist) * facteur_local
                contrib_y = (force * dy / dist) * facteur_local
                x += contrib_x
                y += contrib_y
                if facteur_local > facteur_max:
                    facteur_max = facteur_local

        # transformation du repère global -> repère robot
        repulsion_x = x * cos(theta) + y * sin(theta)
        repulsion_y = -x * sin(theta) + y * cos(theta)

        # normalisation du vecteur de répulsion pour éviter des sauts trop forts
        norme = sqrt(repulsion_x**2 + repulsion_y**2)
        if norme != 0:
            repulsion_x /= norme
            repulsion_y /= norme
        else:
            repulsion_x, repulsion_y = 0.0, 0.0

        # facteur renvoyé : on le clamp entre 0 et 1
        facteur_out = min(1.0, facteur_max)

        return (repulsion_x, repulsion_y), facteur_out

    def mouvement(self, robot, destination, vitesse_max, seuil_ball, seuil_player, force):
        """Effectue un mouvement complet vers la destination avec évitement."""
        distance_objectif = self.distance_objectif(robot, destination)
        # si proche de la cible, oriente et arrête
        if distance_objectif <= seuil_ball:
            delta_x, delta_y = self.vecteur_direction(robot, destination)
            theta = atan2(delta_y, delta_x)
            thetha_robot = robot.orientation
            w = (theta - thetha_robot + pi) % (2 * pi) - pi
            robot.control(0, 0, 5 * w)
            # retourne True si on a atteint/presque atteint l'objectif
            return True
        else:
            # vecteur vers la cible (dans repère robot) -- normalisé
            vx, vy = self.vecteur_robot(robot, destination)

            # évitement (un seul appel)
            (ex, ey), facteur = self.evite(robot, seuil_player, force)

            # combinaison : interpolation entre direction vers but et évitement
            vx_total = (1.0 - facteur) * vx + facteur * ex
            vy_total = (1.0 - facteur) * vy + facteur * ey

            # normalisation du total
            norme = sqrt(vx_total**2 + vy_total**2)
            if norme != 0:
                vx_total /= norme
                vy_total /= norme
            else:
                vx_total, vy_total = 0.0, 0.0

            # calcul vitesse finale (utilise ton avance)
            vx_final, vy_final = self.avance((vx_total, vy_total), vitesse_max)

            # envoie au robot
            robot.control(vx_final, vy_final, 0)
            return False

    def point_intermediaire(self, position1, position2, distance, marge, role):
        x1, y1 = position1
        x2, y2 = position2
        D = sqrt((x2 - x1)**2 + (y2 - y1)**2)

        if D == 0:
            return (x1, y1)

        if distance > D:
            raise ValueError("La distance demandée dépasse la distance entre A et B")

        ratio = distance / D
        x = x1 + (x2 - x1) * ratio
        y = y1 + (y2 - y1) * ratio

        if role == "back":
            dx = x1 - x2
            dy = y1 - y2
            norme = sqrt(dx**2 + dy**2)
            if norme != 0:
                x = x2 + dx / norme * marge
                y = y2 + dy / norme * marge
        elif role == "front":
            dx = x2 - x1
            dy = y2 - y1
            norme = sqrt(dx**2 + dy**2)
            if norme != 0:
                x = x1 + dx / norme * marge
                y = y1 + dy / norme * marge

        return (x, y)

    def distance_securite(self, distance_ball_but):
        taille_but = 0.6
        taille_robot = 0.08
        # évite division par zero (taille_but non nulle)
        return (taille_robot * distance_ball_but) / taille_but

    def position_defense(self, ball, zone_defense, marge, role):
        x_ball, y_ball = ball
        x_defense, y_defense = zone_defense
        distance_ball_but = sqrt((x_defense - x_ball)**2 + (y_defense - y_ball)**2)
        distance = self.distance_securite(distance_ball_but)
        x_objectif, y_objectif = self.point_intermediaire(ball, zone_defense, distance, marge, role)
        return x_objectif, y_objectif

    def defense_passive(self, robot, ball, zone_defense, erreur_placement, vitesse, marge, seuil_ball, role, cote, seuil):
        if ball is None:
            robot.control(0, 0, 0)
            return

        (x, y) = robot.position
        delta_x, delta_y = ball[0] - zone_defense[0], ball[1] - zone_defense[1]
        theta = atan2(delta_y, delta_x)
        theta_robot = robot.orientation
        w = (theta - theta_robot + pi) % (2 * pi) - pi

        # position défensive calculée
        x_def, y_def = self.position_defense(ball, zone_defense, marge, role)
        vx, vy = self.vecteur_robot(robot, (x_def, y_def))

        distance_to_def = self.distance_objectif(robot, (x_def, y_def))
        distance_to_ball = self.distance_objectif(robot, ball)

        # logique back / front (conserve ton intention)
        if role == "back":
            # zone de tir simplifiée — garde ta logique initiale si tu veux des conditions plus fines
            if (((ball[1] <= 0.45 and ball[1] >= -0.45) and ball[0] >= cote * 0.5) and cote > 0) \
               or (((ball[1] <= 0.45 and ball[1] >= -0.45) and ball[0] <= cote * 0.5) and cote < 0):
                if distance_to_ball <= seuil_ball:
                    xs, ys = self.vecteur_direction(robot, ball)
                    theta_shoot = atan2(ys, xs)
                    robot.goto((ball[0], ball[1], theta_shoot), wait=False)
                    robot.kick()
                else:
                    vx_ball, vy_ball = self.vecteur_robot(robot, ball)
                    robot.control(vx_ball * vitesse, vy_ball * vitesse, 0)
            else:
                if distance_to_def > erreur_placement:
                    robot.control(vx * vitesse, vy * vitesse, 0)
                else:
                    robot.control(0, 0, 4 * w)  # rotation plus douce
        elif role == "front":
            if (ball[0] > cote*seuil and cote > 0) or (ball[0] < cote*seuil and cote < 0):
                if distance_to_ball <= seuil_ball:
                    xs, ys = self.vecteur_direction(robot, ball)
                    theta_shoot = atan2(ys, xs)
                    robot.goto((ball[0], ball[1], theta_shoot), wait=False)
                    robot.kick()
                else:
                    vx_ball, vy_ball = self.vecteur_robot(robot, ball)
                    robot.control(vx_ball * vitesse, vy_ball * vitesse, 0)
            else:
                if distance_to_def > erreur_placement:
                    robot.control(vx * vitesse, vy * vitesse, 0)
                else:
                    robot.control(0, 0, 4 * w)

    # méthodes referee / état (conservées mais en utilisant self.client)
    def is_penalized(self, team, robot_id):
        return self.client.referee["teams"][team]["robots"][str(robot_id)]["penalized"]

    def penalty_reason(self, team, robot_id):
        return self.client.referee["teams"][team]["robots"][str(robot_id)].get("penalty_reason", "unknown")

    def is_preempted(self, team, robot_id):
        return self.client.referee["teams"][team]["robots"][str(robot_id)]["preempted"]

    def preemption_reason(self, team, robot_id):
        return self.client.referee["teams"][team]["robots"][str(robot_id)].get("preemption_reason", "unknown")

    def can_move(self, team, robot_id):
        penalized = self.is_penalized(team, robot_id)
        preempted = self.is_preempted(team, robot_id)

        if penalized:
            print(f"🚫 Robot {robot_id} ({team}) pénalisé : {self.penalty_reason(team, robot_id)}")
            return False
        elif preempted:
            print(f"⏸️ Robot {robot_id} ({team}) préempté : {self.preemption_reason(team, robot_id)}")
            return False
        else:
            return True

    def position_before_shoot(self, ball, objectif_shoot, offset):
        # compute unit vector from ball -> goal (objectif_shoot)
        dx = objectif_shoot[0] - ball[0]
        dy = objectif_shoot[1] - ball[1]
        L = sqrt(dx**2 + dy**2)
        if L == 0:
            # fallback: no meaningful direction, stay on the ball
            return (ball[0], ball[1])
        ux = dx / L
        uy = dy / L
        # position behind the ball (away from the goal) by 'offset'
        x_position_shoot = ball[0] - ux * offset
        y_position_shoot = ball[1] - uy * offset
        return (x_position_shoot, y_position_shoot)

    def attaque(self, robot, ball, objectif_shoot, offset, seuil=0.03):
        # safety: require ball to be not None and a valid tuple
        if ball is None:
            return

        # compute the desired position behind the ball
        x_before_shoot, y_before_shoot = self.position_before_shoot(ball, objectif_shoot, offset)

        # robot and ball positions
        x, y = robot.position
        xb, yb = ball

        # correct Euclidean distance
        distance = sqrt((x_before_shoot - x) ** 2 + (y_before_shoot - y) ** 2)

        if distance >= seuil:
            # if far from the "behind the ball" position, go there and face the goal
            xs = objectif_shoot[0] - xb
            ys = objectif_shoot[1] - yb
            theta_shoot = atan2(ys, xs)
            # go to the intermediate position (behind the ball), facing the goal
            robot.goto((x_before_shoot, y_before_shoot, theta_shoot), wait=False)
        else:
            # close enough: go to the ball, face it and kick
            xs, ys = self.vecteur_direction(robot, ball)  # robot -> ball
            theta_shoot = atan2(ys, xs)
            robot.goto((xb, yb, theta_shoot), wait=False)
            robot.kick()

    def score_total(self,team):
        self.client.referee["teams"][team]["score"]
        
