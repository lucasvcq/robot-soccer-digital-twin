# Fichier: remi_attack.py

from math import sqrt, cos, sin, atan2, pi

class remi:
    """
    Classe utilitaire contenant toutes les fonctions de bas niveau pour 
    le contrôle, la navigation, l'arbitrage et la stratégie d'attaque des robots.
    """
    def __init__(self, client):
        self.client = client

    # --- Fonctions de base ---

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
    
    # --- Arbitrage et État ---

    def is_penalized(self, team, robot_id):
        return self.client.referee["teams"][team]["robots"][str(robot_id)]["penalized"]

    def is_preempted(self, team, robot_id):
        return self.client.referee["teams"][team]["robots"][str(robot_id)]["preempted"]

    def can_move(self, team, robot_id):
        """Vérifie si le robot est autorisé à bouger par l'arbitre."""
        penalized = self.is_penalized(team, robot_id)
        preempted = self.is_preempted(team, robot_id)
        return not penalized and not preempted

    # --- Répulsion de la balle (NOUVELLE MÉTHODE) ---
    
    def repulsion_ball(self, robot, ball, seuil_repulsion_ball, force_repulsion_ball):
        """
        Calcule un vecteur de répulsion si le robot est trop proche de la balle.
        Retourne ((repulsion_x, repulsion_y), facteur) dans le repère robot (normalisé).
        """
        x_rob, y_rob = robot.position
        x_ball, y_ball = ball
        theta = robot.orientation
        
        dist = self.distance_objectif(robot, ball)
        
        repulsion_x_global, repulsion_y_global = 0.0, 0.0
        facteur = 0.0

        if dist < seuil_repulsion_ball and dist > 0.1:
            # Vecteur de répulsion dans le repère global (du robot s'éloignant de la balle)
            dx = x_rob - x_ball
            dy = y_rob - y_ball
            
            # Facteur local : (0, 1] (plus proche, plus intense)
            facteur_local = (seuil_repulsion_ball - dist) / seuil_repulsion_ball
            
            # Contribution pondérée par la force et la direction
            contrib_x = (force_repulsion_ball * dx / dist) * facteur_local
            contrib_y = (force_repulsion_ball * dy / dist) * facteur_local
            
            repulsion_x_global += contrib_x
            repulsion_y_global += contrib_y
            facteur = facteur_local
            
        # Transformation du repère global -> repère robot
        repulsion_x = repulsion_x_global * cos(theta) + repulsion_y_global * sin(theta)
        repulsion_y = -repulsion_x_global * sin(theta) + repulsion_y_global * cos(theta)

        # Normalisation du vecteur de répulsion
        norme = sqrt(repulsion_x**2 + repulsion_y**2)
        if norme != 0:
            repulsion_x /= norme
            repulsion_y /= norme
        else:
            repulsion_x, repulsion_y = 0.0, 0.0

        # On clamp le facteur entre 0 et 1 (bien que mathématiquement il doive être dans (0,1])
        facteur_out = min(1.0, facteur)
        return (repulsion_x, repulsion_y), facteur_out

    # --- Fonctions d'Attaque ---
    
    def position_before_shoot(self, ball, objectif_shoot, offset, offset_lateral=0.08):
        """
        Calcule la position derrière la balle pour s'aligner, avec décalage latéral.
        """
        dx = objectif_shoot[0] - ball[0]
        dy = objectif_shoot[1] - ball[1]
        L = sqrt(dx**2 + dy**2)
        
        if L == 0:
            return (ball[0], ball[1])
            
        ux = dx / L
        uy = dy / L
        
        # Vecteur unitaire PERPENDICULAIRE (pour l'esquive)
        vx_perp = -uy
        vy_perp = ux
        
        # Position alignée
        x_align = ball[0] - ux * offset
        y_align = ball[1] - uy * offset
        
        # Position finale (alignée + décalage)
        x_position_shoot = x_align + vx_perp * offset_lateral
        y_position_shoot = y_align + vy_perp * offset_lateral
        
        return (x_position_shoot, y_position_shoot)

    def attaque(self, robot, ball, objectif_shoot, offset, offset_lateral, vitesse, seuil_repulsion_ball, force_repulsion_ball, seuil=0.03):
        """
        Stratégie d'attaque utilisant la combinaison de vecteurs (Attraction + Répulsion).
        """
        if ball is None:
            robot.control(0, 0, 0)
            return

        # 1. Calculer la position cible
        x_before_shoot, y_before_shoot = self.position_before_shoot(ball, objectif_shoot, offset, offset_lateral)

        # 2. Distance à la cible
        distance_to_target = self.distance_objectif(robot, (x_before_shoot, y_before_shoot))
        
        # 3. Mouvement vers la cible (avec combinaison de vecteurs)
        if distance_to_target >= seuil:
            
            # a) Vecteur d'attraction vers la cible (repère robot, normalisé)
            vx_target, vy_target = self.vecteur_robot(robot, (x_before_shoot, y_before_shoot))
            
            # b) Vecteur de répulsion de la balle
            (ex, ey), facteur_repulsion = self.repulsion_ball(robot, ball, seuil_repulsion_ball, force_repulsion_ball)
            
            # c) Combinaison (Potential Field)
            # Interpolation entre la direction vers le but et la répulsion
            vx_total = (1.0 - facteur_repulsion) * vx_target + facteur_repulsion * ex
            vy_total = (1.0 - facteur_repulsion) * vy_target + facteur_repulsion * ey
            
            # Normalisation du total
            norme = sqrt(vx_total**2 + vy_total**2)
            if norme != 0:
                vx_total /= norme
                vy_total /= norme
            else:
                vx_total, vy_total = 0.0, 0.0

            # Calcul vitesse finale
            vx_final, vy_final = self.avance((vx_total, vy_total), vitesse)
            
            # Orientation vers le but (w)
            xs = objectif_shoot[0] - ball[0]
            ys = objectif_shoot[1] - ball[1]
            theta_shoot = atan2(ys, xs)
            theta_robot = robot.orientation
            w = (theta_shoot - theta_robot + pi) % (2 * pi) - pi
            
            # Envoi du contrôle (utilisation de robot.control pour le blending)
            robot.control(vx_final, vy_final, 5 * w) 
            
        else:
            # Assez proche: aller vers la balle et tirer (goto est plus simple pour l'exécution finale)
            xb, yb = ball
            xs, ys = self.vecteur_direction(robot, ball)
            theta_shoot = atan2(ys, xs)
            robot.goto((xb, yb, theta_shoot), wait=False)
            robot.kick()