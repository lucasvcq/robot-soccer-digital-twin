import rsk
from test_remi import remi

with rsk.Client() as client:
    Remi = remi(client)
    robot = client.green1
    ball = client.ball
    objectif_shoot = (-0.9, 0)
    offset = 0.1

    while True:
        try:
            Remi.attaque(robot, ball, objectif_shoot, offset)
        except Exception as e:
            print("Erreur:", e)
