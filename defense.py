import rsk
from REMI import Defense
from REMI import Mouvement
from rsk import constants
import time

with rsk.Client() as client:
    mouvement = Mouvement(client)
    defense = Defense(client)
    robot = client.green2
    vitesse = 2
    zone_defense = (1.84/2,0)
    erreur_placement = 0.04
    while True:
        ball = client.ball
        defense.defense_passive(robot, ball, zone_defense, erreur_placement, vitesse)
        