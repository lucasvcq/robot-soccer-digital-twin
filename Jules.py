import math
import time 
from math import sin, cos, tan, sqrt, atan2, pi
from rsk import constants


class formule:
    def __init__(self, client):
        self.client = client


    def distance_ball(self, robot): # Distance entre le robot et la balle
        R = robot.position  
        B = self.client.ball 

        D = (R[0] - B[0], R[1] - B[1])
        return sqrt(D[0]**2 + D[1]**2)
    
# On attend dans () la position de l'objectif sous forme (x,y)
    def distance_ball_objectif(self,objectif): # Distance entre la balle et l'objectif
        B = self.client.ball

        PO = objectif
        D =(PO[0] - B[0],PO[1]-B[1])
        return sqrt(D[0]**2 + D[1]**2)
    
# On attend dans () les deux positions des objectifs sous forme (x,y),(x,y)
    def distance_objectif_objectif(self,objectif1,objectif2):
        PO1 = objectif1
        PO2 = objectif2

        D =(PO1[0] - PO2[0],PO1[1]-PO2[1])
        return sqrt(D[0]**2 + D[1]**2)


    def Angle_but(self, terrain):  # Angle entre l'axe des x et la balle
        B = self.client.ball
        
        #Définir la position exacte du but visé (x, y)
        if terrain == "gauche":
            # Le but gauche est en X négatif 
            but_x = constants.field_length / 2 
        else: 
            # Le but droit est en X positif 
            but_x = -constants.field_length / 2
            
        but_y = 0 # Le but est toujours centré en hauteur (Y=0)

        # 2. Calcul du vecteur (Balle -> But)
        dx = but_x - B[0]
        dy = but_y - B[1]

        # 3. Calcul de l'angle
        O = atan2(dy, dx) - pi 
        return O
    
# On attend dans () la position de l'objectif sous forme (x,y)
    def Angle_vecteur_objectif_objectif(self,Objectif1,Objectif2): # Angle du vecteur balle-objectif par rapport à l'horizontal

        dx = Objectif1[0] - Objectif2[0] # distance en x entre l'objectif et la balle
        dy = Objectif1[1] - Objectif2[1] # distance en y entre l'objectif et la balle

        O = atan2(dy,dx)
        return O
    
# Fonction qui cré des points autour de la balle formant un arc de cercle, pour l'éviter et se positionner vers l'objectif    
# On attend dans () le robot, l'angle du vecteur balle-objectif pour ça utiliser la fonction juste au dessus, 
# et l'angle entre l'horizontal et la droite reliant l'objectif au centre du terrain 
    def Placement_vers_objectif(self, robot, Angle_robot, Objectif): 
        B = self.client.ball

        points = []
        rayon = [0.15,0.2,0.2,0.2,0.15]
        steps = 4

        Angle_robot_norm = self.normalize_angle(Angle_robot)
        Objectif_norm = self.normalize_angle(Objectif)
        d = Objectif_norm - Angle_robot_norm        
        delta_angle = self.normalize_angle(d)
        
        for i in range(steps + 1):  
            AB = Angle_robot_norm + (i / steps) * delta_angle 
            x = B[0] + rayon[i] * math.cos(AB)
            y = B[1] + rayon[i] * math.sin(AB)
            points.append((x, y))

        index = 0
        fin_x, fin_y = points[-1]

        while True:
            x_robot, y_robot = robot.position
            theta_robot = robot.orientation
            dx = points[0][0] - x_robot
            dy = points[0][1] - y_robot

            distance = self.distance_objectif_objectif(robot.position,points[0])
            print(distance)

            if distance < 0.1 :
                break

            # 3. La formule magique (Rotation de repère)
            # On transforme le vecteur global (dx, dy) en vecteur robot (vx, vy)
            # C'est de la trigonométrie : on tourne le vecteur de l'angle -theta
            vx_local = dx * cos(theta_robot) + dy * sin(theta_robot)
            vy_local = -dx * sin(theta_robot) + dy * cos(theta_robot)

            # --- 4. Vitesse Maximale Constante ---
            VITESSE_CIBLE = 0.5  # Vitesse désirée en m/s (ex: 1.0 c'est très rapide)

            # On calcule la norme (la longueur) du vecteur local
            norme_vecteur = sqrt(vx_local**2 + vy_local**2)

            if norme_vecteur > 0:
                # On "normalise" le vecteur (on le ramène à une longueur de 1)
                # Puis on multiplie par la vitesse cible pour forcer l'allure
                vitesse_x = (vx_local / norme_vecteur) * VITESSE_CIBLE
                vitesse_y = (vy_local / norme_vecteur) * VITESSE_CIBLE
            else:
                vitesse_x = 0
                vitesse_y = 0

            # 5. Envoyer la commande
            robot.control(vitesse_x, vitesse_y, 0)
            
            time.sleep(0.05)

        while index < steps - 1:
            a = robot.position
            b = points[index+1]

            distance = self.distance_objectif_objectif(a, b)
            Seuil_atteinte_point = 0.4
            
            index += 1

            ox = points[index][0]
            oy = points[index][1]

            robot.goto((ox, oy, Objectif-pi), wait = False)
            time.sleep(0.25)

        robot.goto((fin_x, fin_y, Objectif-pi))
    

    def normalize_angle(self,angle):
    #Ramène un angle dans l'intervalle [-pi, pi]
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle


# On attend dans (), la distance entre la balle et le robot tireur, la distance max de la balle lorsqu'on kick(1)
    def calc_kick_strength(self,distance, d_max):     #Calcule la force de frappe (entre 0 et 1) en fonction de la distance.
        d_min = 0.01
        if distance >= d_max:     #d_max : distance maximale pour une frappe forte
            return 1.0
    # Interpolation linéaire
        kick = (distance - d_min) / (d_max - d_min)
        return kick


    def arret_balle(self, robot):
            R = robot.position
            B = self.client.ball
            d = 0.08
        
            V = (B[0] - R[0], B[1] - R[1])
            dx = V[0]
            dy = V[1]
            norme = math.sqrt(dx**2 + dy**2)

            if norme == 0:
                return (B[0], B[1], 0)  # Évite la division par zéro
            ux = dx / norme
            uy = dy / norme
            x_stop = B[0] - d * ux
            y_stop = B[1] - d * uy
            return (x_stop, y_stop)

    
    def calcul_coefficient(self, robot): # Permet de calculer la moyenne sur 3 frappes de la distance parcourue par la balle quand kick(1)
        Objectif = [0,pi,0] 
        L=[]
        Li = 0
        i = -1
        while i < 2 :
            i = i + 1 
            print(i)
            B = self.client.ball
            A = self.Angle_vecteur_objectif_objectif(robot.position,self.client.ball)
            self.Placement_vers_objectif(robot, A, Objectif[i])
            x,y = self.arret_balle(robot)
            robot.goto((x,y,Objectif[i]-pi),avoid_obstacles=True)
            robot.kick(1)
            time.sleep(4)
            D = self.distance_ball_objectif(B)
            print(D)
            L.append(D)
            Li= Li + D
            S =Li/3
        return S  # Retourne la moyenne, que l'on peut utiliser en distance max pour le calcul de la force de frappe.
    
    def rapprochement_passeur(self, robot_a_rapprocher, distance_rapprochement):
            P1 = robot_a_rapprocher.position
            B = self.client.ball
            O = self.Angle_vecteur_objectif_objectif(P1,B) - pi

            d = distance_rapprochement
        
            V = (B[0] - P1[0], B[1] - P1[1])
            dx = V[0]
            dy = V[1]
            norme = math.sqrt(dx**2 + dy**2)

            if norme == 0:
                return (P1[0], P1[1], 0)  # Évite la division par zéro
            
            ux = dx / norme
            uy = dy / norme

            x = B[0] - d * ux
            y = B[1] - d * uy
            robot_a_rapprocher.goto((x,y,O),avoid_obstacles=True)
    
    def Pass(self, robot_reçeveur, robot_passeur):
        P1 = robot_reçeveur.position
        P2 = robot_passeur.position
        DB = self.distance_objectif_objectif(P1,P2)
       
        A = self.Angle_vecteur_objectif_objectif(P2,self.client.ball) # Angle du vecteur balle-robot passeur par rapport à l'horizontal
        O = self.Angle_vecteur_objectif_objectif(P1,self.client.ball) - pi # Angle du vecteur balle-robot qui va recevoir la passe par rapport à l'horizontal
    
        self.Placement_vers_objectif(robot_passeur,A,O) # Fonction d'évitement de la balle et de placement vers le robot receveur
        x,y = self.arret_balle(robot_passeur)
        robot_passeur.goto((x,y,O-pi)) # Une fois placé on avance et on fait la passe
        robot_passeur.kick(self.calc_kick_strength(DB,0.99)) # Fonction qui calcule la force du tir en fonction de la distance

    def Spot_shoot(self,robot_tireur,terrain): # Tire au milieu des buts
        P = robot_tireur.position # Position du robot tireur
        
        A = self.Angle_vecteur_objectif_objectif(P,self.client.ball) 
        O = self.Angle_but(terrain) 
            
        self.Placement_vers_objectif(robot_tireur,A,O)
        
        x,y = self.arret_balle(robot_tireur)
        robot_tireur.goto((x,y,O-pi)) 
        robot_tireur.kick(1)

    def Pass_objectif(self,robot_passeur,Objectif): # Faire une passe à endroit précis "objectif", on attend une coordonnée (x,y)
        Formule = formule(self.client)
 
        P = robot_passeur.position # Coordonnée du robot 1
        PO = Objectif # Coordonnée de l'objectif
        
        DB = Formule.distance_ball_objectif(Objectif) # Distance balle-objectif
        A = Formule.Angle_vecteur_objectif_objectif(P,self.client.ball)
        O = Formule.Angle_vecteur_objectif_objectif(PO,self.client.ball) - pi

        Formule.Placement_vers_objectif(robot_passeur,A,O)
        x,y =Formule.arret_balle(robot_passeur)
        robot_passeur.goto((x,y,O-pi))
        robot_passeur.kick(Formule.calc_kick_strength(DB,0.99))

    def deplacement_objectif(self, robot, terrain):
        Angle_Vers_But = self.Angle_but(terrain) 
        A = self.Angle_vecteur_objectif_objectif(robot.position, self.client.ball)
        
        self.Placement_vers_objectif(robot, A, Angle_Vers_But)

        x, y = self.arret_balle(robot)
        robot.goto((x, y, Angle_Vers_But - pi))

        
        



    

        

    