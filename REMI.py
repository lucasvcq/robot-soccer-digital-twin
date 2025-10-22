from math import sqrt, cos, sin, atan2

class Remi:
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
        """Renvoie un petit vecteur de répulsion si un joueur est trop proche"""
        repulsion_x, repulsion_y = 0, 0
        distances = self.distance_players(robot)
        theta = robot.orientation
        for player, dist in distances:
            if dist < seuil_player:
                dx = robot.position[0] - player.position[0]
                dy = robot.position[1] - player.position[1]
                facteur = force*(seuil_player - dist) / seuil_player
                repulsion_x += (dx / dist * facteur)*cos(theta)
                repulsion_y += (dy / dist * facteur)*sin(theta)
        return (repulsion_x, repulsion_y)
    
    def mouvement(self, robot, destination, vitesse_max, seuil_ball, seuil_player, force):
        """Effectue un mouvement complet vers la balle avec évitement"""
        distance_objectif = self.distance_objectif(robot,destination)
        if distance_objectif <= seuil_ball:
            robot.control(0, 0, 0)
            print(f"✅ Arrêt : distance {round(distance_objectif,2)} < seuil {seuil_ball}")
            return True  # indique que la balle est atteinte

        # vecteur vers la balle
        vx, vy = self.vecteur_robot(robot, destination)
       
        # vecteur d’évitement
        ex, ey = self.evite(robot, seuil_player, force)
        print( ex, ey)
        if abs(ey) <= abs(ex):
            if ey < 0:
                ey = abs(ex)
            else:
                ey = -abs(ex)
        
        # combinaison des deux vecteurs
        vx_total = vx + ex
        vy_total = vy + ey

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

    def angle(self, robot, objectif):
        x, y = self.vecteur_direction(robot, objectif)
        theta_direction = atan2(y, x)
        return theta_direction

    def rotation_mouvement(self, robot, objectif, marge_rotation):
        theta_direction = self.angle(robot, objectif)
        orientation = robot.orientation
        rotation = theta_direction - orientation
        x1, y1 = robot.position
        if rotation >= marge_rotation:
            robot.goto((x1, y1, rotation))

