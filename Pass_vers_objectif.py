import threading
import rsk 
from Jules import formule

with rsk.Client() as client: 
    Formule = formule(client)
    
    P1 = client.green1.position # Coordonnée du robot 1
    P2 = client.green2.position # Coordonnée du robot 2

    D1 = Formule.distance_ball(client.green1) # Distance balle-robot1
    D2 = Formule.distance_ball(client.green2) # Distance balle-robot2

    if D1 > D2 :
        Formule.Pass_objectif(client.green2,(1,0))

    else :
        Formule.Pass_objectif(client.green1,(1,0))