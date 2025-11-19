import threading
import time
import rsk
from REMI import remi

def controle_robot(remi_obj, robot, robot_id, zone_defense, vitesse, erreur_placement, marge, seuil_ball, role):
    while True:
        try:
            ball = remi_obj.client.ball
            if remi_obj.can_move("green", robot_id):
                remi_obj.defense_passive(
                    robot, ball, zone_defense, erreur_placement, vitesse, marge, seuil_ball, role
                )
            time.sleep(0.05)
        except Exception as e:
            print(f"Erreur robot {robot_id}:", e)
            time.sleep(0.1)

with rsk.Client() as client:
    Remi = remi(client)
    robot1 = client.green1
    robot2 = client.green2

    vitesse = 4
    zone_defense = (1.84/2, 0)
    erreur_placement = 0.04
    marge_front = 0.3
    marge_back = 0.2
    seuil_ball = 0.2

    # Threads pour chaque robot
    t1 = threading.Thread(
        target=controle_robot,
        args=(Remi, robot1, "1", zone_defense, vitesse, erreur_placement, marge_front, seuil_ball, "front")
    )
    t2 = threading.Thread(
        target=controle_robot,
        args=(Remi, robot2, "2", zone_defense, vitesse, erreur_placement, marge_back, seuil_ball, "back")
    )

    t1.start()
    t2.start()

    t1.join()
    t2.join()
