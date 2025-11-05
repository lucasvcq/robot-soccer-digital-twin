import rsk 
from Jules import formule
from math import pi 


class Jules: 
    def __init__(self, client): 
        self.client = client 

    def test(self,robot):
        Formule = formule(self.client)
        P = Formule.calcul_coefficient(robot)
        print(f"La distance pour un kick(1) est {P}")
        
        
    def Spot_shoot(self): # Tire au milieu des buts
        Formule = formule(self.client)

        B = self.client.ball # Position de la balle
        P1 = client.green1.position # Position du robot 1
        P2 = client.green2.position # Position du robot 2

        D1 = Formule.distance_ball(client.green1) # Distance balle-robot1
        D2 = Formule.distance_ball(client.green2) # Distance balle-robot2

        
        if D1 > D2 : 
            A = Formule.Angle_vecteur_balle_objectif(P2) # Angle du vecteur balle-robot par rapport à l'horizontal
            O = Formule.Angle_but() # Angle pour tirer dans les but par rapport à l'horizontal
        
            Formule.Placement_vers_objectif(client.green2,A,O) # Fonction d'évitement de la balle et de placement
            client.green2.goto((B[0],B[1],O-pi)) # Une fois placé on avance et on tire
            client.green2.kick(1)
        
        else : 
            A = Formule.Angle_vecteur_balle_objectif(P1) 
            O = Formule.Angle_but() 
            Formule.Placement_vers_objectif(client.green1,A,O)
            client.green1.goto((B[0],B[1],O-pi)) 
            client.green1.kick(1)

        
    def Pass(self): # Passe au coéquipier
        Formule = formule(self.client)
        B = self.client.ball # Position de la balle
        P1 = client.green1.position # Position du robot 1
        P2 = client.green2.position # Position du robot 2

        D1 = Formule.distance_ball(client.green1) # Distance balle-robot1
        D2 = Formule.distance_ball(client.green2) # Distance balle-robot2
        DB = Formule.distance_objectif_objectif(P1,P2)


        if D1 > D2 :
            A = Formule.Angle_vecteur_balle_objectif(P2) # Angle du vecteur balle-robot passeur par rapport à l'horizontal
            O = Formule.Angle_vecteur_balle_objectif(P1) - pi # Angle du vecteur balle-robot qui va recevoir la passe par rapport à l'horizontal
            Formule.Placement_vers_objectif(client.green2,A,O) # Fonction d'évitement de la balle et de placement vers le robot receveur
            client.green2.goto((B[0],B[1],O-pi)) # Une fois placé on avance et on fait la passe
            client.green2.kick(Formule.calc_kick_strength(DB,0.05,0.92)) # Fonction qui calcule la force du tir en fonction de la distance
            print(Formule.calc_kick_strength(DB,0.01,0.92))
            print(DB)

        else : 
            A = Formule.Angle_vecteur_balle_objectif(P1)
            O = Formule.Angle_vecteur_balle_objectif(P2) -pi 
            Formule.Placement_vers_objectif(client.green1,A,O)
            client.green1.goto((B[0],B[1],O-pi))
            client.green1.kick(Formule.calc_kick_strength(DB,0.05,0.92))
            print(Formule.calc_kick_strength(DB,0.01,0.92))
            print(DB)

    def Pass_objectif(self,Objectif): # Faire une passe à endroit précis "objectif", on attend une coordonnée (x,y)
        Formule = formule(self.client)
        
        B = self.client.ball
        P1 = client.green1.position # Coordonnée du robot 1
        P2 = client.green2.position # Coordonnée du robot 2
        PO = Objectif # Coordonnée de l'objectif

        D1 = Formule.distance_ball(client.green1) # Distance balle-robot1
        D2 = Formule.distance_ball(client.green2) # Distance balle-robot2

        DB = Formule.distance_ball_objectif() # Distance balle-objectif

        if D1 > D2 :
            A = Formule.Angle_vecteur_balle_objectif(P2) # Angle du vecteur balle-robot passeur par rapport à l'horizontal
            O = Formule.Angle_vecteur_balle_objectif(PO) - pi # Angle du vecteur balle-objectif par rapport à l'horizontal

            Formule.Placement_vers_objectif(client.green2,A,O) # Fonction d'évitement de la balle et de placement vers l'objectif
            client.green2.goto((B[0],B[1],O-pi)) # Une fois placé on avance et on fait la passe
            client.green2.kick(Formule.calc_kick_strength(DB,0.05,0.92)) # Fonction qui calcule la force du tir en fonction de la distance
            print(Formule.calc_kick_strength(DB,0.05,0.92))
        
        else : 
            A = Formule.Angle_vecteur_balle_objectif(P1)
            O = Formule.Angle_vecteur_balle_objectif(PO) - pi

            Formule.Placement_vers_objectif(client.green1,A,O)
            client.green1.goto((B[0],B[1],O-pi))
            client.green2.kick(Formule.calc_kick_strength(DB,0.05,0.92))
            print(Formule.calc_kick_strength(DB,0.05,0.92))



        

        



with rsk.Client() as client: 
    jules = Jules(client)
    jules.test(client.green1)
    #jules.Spot_shoot()
    #jules.Pass() 
    #jules.Pass_objectif((1,0))