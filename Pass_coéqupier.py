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
        t1 = threading.Thread(
        target = Formule.Pass,
        args=(client.green1, client.green2) # En 1er robot_reçeveur puis en 2ème robot_passeur
        )
        t2 = threading.Thread(
        target = Formule.rapprochement_passeur,
        args=(client.green1, 0.5) # Robot_reçeveur, distance à laquelle on veut le rapprocher de la balle
        )

        t1.start()
        t2.start()

        t1.join()
        t2.join()

    else :
        t1 = threading.Thread(
        target = Formule.Pass,
        args=(client.green2, client.green1)
        )
        t2 = threading.Thread(
        target = Formule.rapprochement_passeur,
        args=(client.green2, 0.5)
        )

        t1.start()
        t2.start()

        t1.join()
        t2.join()
        


   
 