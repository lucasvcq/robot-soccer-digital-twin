import rsk 
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


    def Angle_but(self):  # Angle entre l'axe des x et la balle
        B = self.client.ball

        dx = constants.field_length / 2 + B[0]  # distance en x entre les cages et la balle
        dy = B[1] # distance en y entre le milieu des cages et la balle

        O = atan2(dy,dx)  
        return O
    
# On attend dans () la position de l'objectif sous forme (x,y)
    def Angle_vecteur_balle_objectif(self,Objectif): # Angle du vecteur balle-objectif par rapport à l'horizontal
        B = self.client.ball

        dx = Objectif[0] - B[0] # distance en x entre l'objectif et la balle
        dy = Objectif[1] - B[1] # distance en y entre l'objectif et la balle

        O = atan2(dy,dx)
        return O
    

# Fonction qui cré des points autour de la balle formant un arc de cercle, pour l'éviter et se positionner vers l'objectif    
# On attend dans () le robot, l'angle du vecteur balle-objectif pour ça utiliser la fonction juste au dessus, 
# et l'angle entre l'horizontal et la droite reliant l'objectif au centre du terrain 
    def Placement_vers_objectif(self,robot,Angle_robot,Objectif): 
        B = self.client.ball

        rayon = 0.2 # rayon de l'arc de cercle
        steps = 5 # Nombre de points créés pour éviter la balle
        d = Objectif - Angle_robot

        delta_angle = self.normalize_angle(d)

        for i in range (steps + 1):
                AB = Angle_robot + (i / steps)*(delta_angle) # Angle des points positionné sur le cercle 
                x = B[0] + rayon*math.cos((AB)) # Génération des coordonnées des points intermediaire pour atteindre la position finale
                y = B[1] + rayon*math.sin((AB))
                robot.goto((x,y,Objectif-pi), avoid_obstacles=True)  # Déplacement jusqu'au point souhaité


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
            A = self.Angle_vecteur_balle_objectif(robot.position)
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
            O = self.Angle_vecteur_balle_objectif(P1) - pi

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
       
        A = self.Angle_vecteur_balle_objectif(P2) # Angle du vecteur balle-robot passeur par rapport à l'horizontal
        O = self.Angle_vecteur_balle_objectif(P1) - pi # Angle du vecteur balle-robot qui va recevoir la passe par rapport à l'horizontal
    
        self.Placement_vers_objectif(robot_passeur,A,O) # Fonction d'évitement de la balle et de placement vers le robot receveur

        x,y = self.arret_balle(robot_passeur)
        robot_passeur.goto((x,y,O-pi)) # Une fois placé on avance et on fait la passe
        robot_passeur.kick(self.calc_kick_strength(DB,0.99)) # Fonction qui calcule la force du tir en fonction de la distance

    def Spot_shoot(self,robot_tireur): # Tire au milieu des buts
        P = robot_tireur.position # Position du robot tireur
        
        A = self.Angle_vecteur_balle_objectif(P) 
        O = self.Angle_but() 
            
        self.Placement_vers_objectif(robot_tireur,A,O)
        
        x,y = self.arret_balle(robot_tireur)
        robot_tireur.goto((x,y,O-pi)) 
        robot_tireur.kick(1)

    def Pass_objectif(self,robot_passeur,Objectif): # Faire une passe à endroit précis "objectif", on attend une coordonnée (x,y)
        Formule = formule(self.client)
 
        P = robot_passeur.position # Coordonnée du robot 1
        PO = Objectif # Coordonnée de l'objectif
        
        DB = Formule.distance_ball_objectif() # Distance balle-objectif
        A = Formule.Angle_vecteur_balle_objectif(P)
        O = Formule.Angle_vecteur_balle_objectif(PO) - pi

        Formule.Placement_vers_objectif(robot_passeur,A,O)
        x,y =Formule.arret_balle(robot_passeur)
        robot_passeur.goto((x,y,O-pi))
        robot_passeur.kick(Formule.calc_kick_strength(DB,0.99))
        print(Formule.calc_kick_strength(DB,0.99))


    

        

    