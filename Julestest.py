import rsk 
from rsk import constants 
import math 
from math import sin, cos, tan, sqrt, atan2, pi , degrees
from Jules import formule

class Jules: 
    def __init__(self, client): 
        self.client = client 
        
    def test(self,dmax):
        Formule = formule(client)

        P1 = client.green1.position
        P2 = client.green2.position
        DB = Formule.distance_objectif_objectif(P1,P2)

        D1 = Formule.distance_ball(client.green1)
        D2 = Formule.distance_ball(client.green2)

        if DB < dmax : 
            if D1 > D2 :
                A = Formule.Angle_vecteur_balle_objectif(P2) # Angle du vecteur balle-robot passeur par rapport à l'horizontal
                O = Formule.Angle_vecteur_balle_objectif(P1) - pi # Angle du vecteur balle-robot qui va recevoir la passe par rapport à l'horizontal
                Formule.Placement_vers_objectif(client.green2,A,O) # Fonction d'évitement de la balle et de placement vers le robot receveur
                x,y = Formule.arret_balle(client.green2)
                client.green2.goto((x,y,O-pi)) # Une fois placé on avance et on fait la passe
                client.green2.kick(Formule.calc_kick_strength(DB,0.99)) # Fonction qui calcule la force du tir en fonction de la distance
                print(Formule.calc_kick_strength(DB,0.99))
                print(DB)
            else :
                A = Formule.Angle_vecteur_balle_objectif(P1)
                O = Formule.Angle_vecteur_balle_objectif(P2) -pi 
                Formule.Placement_vers_objectif(client.green1,A,O)
                x,y = Formule.arret_balle(client.green1)
                client.green1.goto((x,y,O-pi))
                client.green1.kick(Formule.calc_kick_strength(DB,0.99))
                print(Formule.calc_kick_strength(DB,0.99))
                print(DB)
        else :
            if D1 > D2 :
                A = Formule.Angle_vecteur_balle_objectif(P2) 
                O = Formule.Angle_vecteur_balle_objectif(P1) - pi

                arrived =False

                while not arrived:
                    xr,yr = Formule.rapprochement_passeur(client.green1,0.6)
                    robot1 = client.green1.goto((xr,yr,O), avoid_obstacles=True, wait=False)

                    Formule.Placement_vers_objectif(client.green2,A,O)
                    B = self.client.ball

                    rayon = 0.2 # rayon de l'arc de cercle
                    steps = 5 # Nombre de points créés pour éviter la balle
                    
                    d = O - A
                    delta_angle = Formule.normalize_angle(d)

                    robot2 = None

                    for i in range (steps + 1):
                        AB = A + (i / steps)*(delta_angle) # Angle des points positionné sur le cercle 
                        x = B[0] + rayon*math.cos((AB)) # Génération des coordonnées des points intermediaire pour atteindre la position finale
                        y = B[1] + rayon*math.sin((AB))
                        # Le robot va à tous les points, MAIS
                        # robot2 ne sera mis à jour qu'au DERNIER point.
                        if i == steps:
                            robot2 = client.green2.goto((x, y, O - pi), avoid_obstacles=True, wait=False)
                        else:
                            client.green2.goto((x, y, O - pi), avoid_obstacles=True, wait=False)

                    x,y = Formule.arret_balle(client.green2)
                    client.green2.goto((x,y,O-pi))
                    arrived = robot1 and robot2 
                
                    client.green2.kick(Formule.calc_kick_strength(DB,0.99)) # Fonction qui calcule la force du tir en fonction de la distance
                    print(robot1,robot2)

            else : 
                A = Formule.Angle_vecteur_balle_objectif(P1) 
                O = Formule.Angle_vecteur_balle_objectif(P2) - pi

                xr,yr = Formule.rapprochement_passeur(client.green2,0.6)
                client.green2.goto((xr,yr,O))

                Formule.Placement_vers_objectif(client.green1,A,O)
                x,y = Formule.arret_balle(client.green1)
                client.green1.goto((x,y,O-pi))
                client.green1.kick(Formule.calc_kick_strength(DB,0.99)) # Fonction qui calcule la force du tir en fonction de la distance
                print(Formule.calc_kick_strength(DB,0.99))
                print(DB)


with rsk.Client() as client: 
    jules = Jules(client)
    jules.test(0.5)