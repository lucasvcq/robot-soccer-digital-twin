import rsk
from avoid import avoid
import time

with rsk.Client() as client:
    avoid = avoid(client)
    vitesse_max = 1.0       # vitesse maximale
    seuil_ball = 0.2   # s'arrêter si le robot est à moins de 0.2 unités de la balle
    seuil_player = 0.25
    while True:
        # distance et vecteur vers la balle
        distance_ball = avoid.distance_ball(client.green2)
        distance_players = avoid.distance_players()
        if distance_ball <= seuil_ball:
            # on s'arrête
            client.green2.control(0, 0, 0)
            print(f"Arrêt : distance {round(dist,2)} < seuil {distance_seuil}")
            break  # sortir de la boucle


        if distance_players[0] or distance_players[1] or distance_players[3] <= seuil_player


        # vecteur dans le repère du robot
        vx, vy = avoid.vecteur_robot(client.green2)

        # arrondir pour plus de stabilité
        vx = round(vx, 2)*vitesse_max
        vy = round(vy, 2)*vitesse_max

        # envoyer la commande au robot
        client.green2.control(vx, vy, 0)
        # affichage pour debug
        print(f"Distance: {round(dist,2)} | Vitesse: ({vx},{vy})")

        # petite pause pour ne pas surcharger le CPU
        time.sleep(0.01)
