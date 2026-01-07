import rsk 
from Jules import formule
from math import sin, cos, tan, sqrt, atan2, pi
import time
import threading

class action :     

    def __init__(self, client):
        self.client = client
        self.Formule = formule(client)    

    def Tire_vers_le_but(self,robot1,robot2,terrain):
        D1 = self.Formule.distance_ball(robot1) # Distance balle-robot1
        D2 = self.Formule.distance_ball(robot2) # Distance balle-robot2

        if D1 > D2 :
            self.Formule.Spot_shoot(robot2,terrain)
        else:
            self.Formule.Spot_shoot(robot1,terrain)

    def Pass_coéquipier(self, robot1, robot2):
        D1 = self.Formule.distance_ball(robot1) # Distance balle-robot1
        D2 = self.Formule.distance_ball(robot2) # Distance balle-robot2


        if D1 > D2 :
            t1 = threading.Thread(
            target = self.Formule.Pass,
            args=(robot1, robot2) # En 1er robot_reçeveur puis en 2ème robot_passeur
            )

            t2 = threading.Thread(
            target = self.Formule.rapprochement_passeur,
            args=(robot1, 0.5) # Robot_reçeveur, distance à laquelle on veut le rapprocher de la balle
            )

            t1.start()
            t2.start()
            t1.join()
            t2.join()

        else :
            t1 = threading.Thread(
            target = self.Formule.Pass,
            args=(robot2, robot1)
            )

            t2 = threading.Thread(
            target = self.Formule.rapprochement_passeur,
            args=(robot2, 0.5)
            )

            t1.start()
            t2.start()
            t1.join()
            t2.join()

    def Pass_vers_objectif(self,robot1,robot2,objectif,terrain):
        D1 = self.Formule.distance_ball(robot1) # Distance balle-robot1
        D2 = self.Formule.distance_ball(robot2) # Distance balle-robot2

        if D1 > D2:
            receveur = robot1
            passeur = robot2
        else:
            receveur = robot2
            passeur = robot1

        t1 = threading.Thread(
        target = self.Formule.Pass_objectif,
        args=(passeur,objectif) # En 1er robot_reçeveur puis en 2ème l'objectifr
        )

        t1.start()
        t1.join()
        
        t2 = threading.Thread(
        target = self.Formule.suivre_balle,
        args=(receveur,terrain) # En 1er robot_reçeveur puis en 2ème l'objectifr
        )

        t2.start()
        t2.join()
    
        t3 = threading.Thread(
        target = self.Formule.Spot_shoot,
        args=(receveur,terrain) # En 1er robot_reçeveur puis en 2ème l'objectifr
        )

        t3.start()
        t3.join()
            

with rsk.Client() as client:
    Action = action(client)
    Action.Pass_vers_objectif(client.green1, client.green2,(-0.5,0.4),"droit")
    #Action.Tire_vers_le_but(client.green1,client.green2,"droite")      