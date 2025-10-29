from math import *

class Mouvement:
    def __init__(self, client):
        self.client = client

    def distance_objectif(self, robot, objectif):
        C = robot.position
        B = objectif
        D = (C[0] - B[0], C[1] - B[1])
        return sqrt(D[0]**2 + D[1]**2)

    def vecteur_direction(self, robot, objectif):
        C = robot.position
        B = objectif
        return (B[0] - C[0], B[1] - C[1])
    
    def avance(self, vecteur, vitesse):
        vx, vy = vecteur
        vx = round(vx, 2) * vitesse
        vy = round(vy, 2) * vitesse
        return vx, vy

    def vecteur_robot(self, robot, objectif):
        """Vecteur vers la balle dans le repère du robot"""
        vx_terrain, vy_terrain = self.vecteur_direction(robot, objectif)
        theta = robot.orientation
        vx = cos(theta) * vx_terrain + sin(theta) * vy_terrain
        vy = -sin(theta) * vx_terrain + cos(theta) * vy_terrain
        norme = sqrt(vx**2 + vy**2)
        if norme != 0:
            vx_robot = vx / norme
            vy_robot = vy / norme
        else:
            vx_robot, vy_robot = 0, 0
        return (vx_robot, vy_robot)
    
    def distance_players(self, robot):
        """Renvoie la distance entre le robot et les autres joueurs"""
        players = [self.client.green1, self.client.green2, self.client.blue1, self.client.blue2]
        distance_player = []
        for player in players:
            if robot != player:
                pos_adv = player.position
                ecart_x = robot.position[0] - pos_adv[0]
                ecart_y = robot.position[1] - pos_adv[1]
                distance = sqrt(ecart_x**2 + ecart_y**2)
                distance_player.append((player, distance))
        return distance_player #distance_player[0]=nom du robot et distance_player[1]=distance

    def evite(self, robot, seuil_player, force):
        """Renvoie un vecteur de répulsion si un joueur est trop proche"""
        x, y = 0, 0
        distances = self.distance_players(robot)
        theta = robot.orientation
        facteur = 0
        # On cumule la répulsion pour tous les joueurs proches
        for player, dist in distances:
            if dist < seuil_player and dist > 0:  # éviter division par zéro
              dx = robot.position[0] - player.position[0]
              dy = robot.position[1] - player.position[1]
              facteur = (seuil_player - dist) / seuil_player
              x += (force * dx / dist) * facteur
              y += (force * dy / dist) * facteur

        # Conversion du repère global -> repère robot
        repulsion_x = x * cos(theta) + y * sin(theta)
        repulsion_y = -x * sin(theta) + y * cos(theta)
        return [(repulsion_x, repulsion_y), facteur]

    
    def mouvement(self, robot, destination, vitesse_max, seuil_ball, seuil_player, force):
        """Effectue un mouvement complet vers la balle avec évitement"""
        distance_objectif = self.distance_objectif(robot,destination)
        if distance_objectif <= seuil_ball:
            delta_x, delta_y = self.vecteur_direction(robot, destination)
            theta = atan2(delta_y, delta_x)
            thetha_robot = robot.orientation
            w = (theta - thetha_robot + pi) % (2 * pi) - pi
            robot.control(0, 0, 5*w)
            print(f"✅ Arrêt : distance {round(distance_objectif,2)} < seuil {seuil_ball}")
            return False
        else:

            # vecteur vers la balle
            vx, vy = self.vecteur_robot(robot, destination)
            # vecteur d’évitement
            ex, ey = self.evite(robot, seuil_player, force)[0]
            facteur = self.evite(robot, seuil_player, force)[1]
            # combinaison des deux vecteurs
            vx_total = (1-facteur)*vx + facteur*ex
            vy_total = (1-facteur)*vy + facteur*ey

            # normalisation
            norme = sqrt(vx_total**2 + vy_total**2)
            if norme != 0:
                vx_total /= norme
                vy_total /= norme

            # calcul vitesse finale
            vx_final, vy_final = self.avance((vx_total, vy_total), vitesse_max)

            # mouvement du robot
            robot.control(vx_final, vy_final, 0)
            print(f"🚗 Vers balle | Dist: {distance_objectif:.2f} | vx={vx_final:.2f}, vy={vy_final:.2f}")
            return False

    

class Defense:
    def __init__(self, client):
        self.client = client


    def point_intermediaire(self, position1, position2, distance, marge):
        x1, y1 = position1
        x2, y2 = position2
        D = sqrt((x2 - x1)**2 + (y2 - y1)**2)+0.04

        # Si la distance demandée dépasse la distance totale
        if distance > D:
            raise ValueError("La distance d dépasse la distance entre A et B")
        
        ratio = distance / D
        x = x1 + (x2 - x1) * (ratio + marge)
        y = y1 + (y2 - y1) * (ratio + marge)
        return (x, y)
    
    def distance_securite(self, distance_ball_but):
        taille_but = 0.6
        taille_robot = 0.08
        distance_balle_robot = (taille_robot * distance_ball_but) / taille_but

        return distance_balle_robot

    def position_defense(self, ball, zone_defense, marge):
        x_ball, y_ball = ball
        x_defense, y_defense = zone_defense
        distance_ball_but = sqrt((x_defense-x_ball)**2 + (y_defense-y_ball)**2)
        distance = self.distance_securite(distance_ball_but)
        x_objectif, y_objectif = self.point_intermediaire(ball, zone_defense, distance, marge)
        return x_objectif, y_objectif
    
    def vecteur_robot(self, robot, objectif):
        """Vecteur vers la balle dans le repère du robot"""
        vx_terrain, vy_terrain = self.vecteur_direction(robot, objectif)
        theta = robot.orientation
        vx = cos(theta) * vx_terrain + sin(theta) * vy_terrain
        vy = -sin(theta) * vx_terrain + cos(theta) * vy_terrain
        norme = sqrt(vx**2 + vy**2)
        if norme != 0:
            vx_robot = vx / norme
            vy_robot = vy / norme
        else:
            vx_robot, vy_robot = 0, 0
        return (vx_robot, vy_robot)
    
    def vecteur_direction(self, robot, objectif):
        C = robot.position
        B = objectif
        return (B[0] - C[0], B[1] - C[1])
    
    def distance_objectif(self, robot, objectif):
        C = robot.position
        B = objectif
        D = (C[0] - B[0], C[1] - B[1])
        return sqrt(D[0]**2 + D[1]**2)
    
    def defense_passive(self, robot, ball, zone_defense, erreur_placement, vitesse, marge):
        (x, y) = robot.position
        delta_x, delta_y = ball[0]-zone_defense[0], ball[1]-zone_defense[1]
        theta = atan2(delta_y, delta_x)
        thetha_robot = robot.orientation
        w = (theta - thetha_robot + pi) % (2 * pi) - pi
        x, y = self.position_defense(ball, zone_defense, marge)
        vx, vy = self.vecteur_robot(robot, (x,y))
        distance = self.distance_objectif(robot, (x,y))
        if (ball[1]<=0.45 or ball[1]>=-0.45) and ball[0]<=0.62:
            if distance > erreur_placement:
                robot.control(vx*vitesse, vy*vitesse, 0)
                return
            else:
                robot.control(0, 0, 10*w)
                return
        else:
            print(ball)
            time.sleep(1)
class Penalty:
    def __init__(self, client):
        self.client = client

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
