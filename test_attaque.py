import rsk
from test_remi import remi

with rsk.Client() as client:
    Remi = remi(client)
    robot = client.green1
    ball = client.ball
    objectif_shoot = (-0.9, 0)
    offset = 0.3

    while True:
        try:
            Remi.attaque(robot, ball, objectif_shoot, offset, seuil=0.03)
        except Exception as e:
            print("Erreur:", e)
