import rsk
from REMI import Defense
from REMI import Penalty
from rsk import constants
import time

with rsk.Client() as client:
    penalty = Penalty(client) 
    defense = Defense(client)
    robot = client.green2
    vitesse = 2
    zone_defense = (1.84/2,0)
    erreur_placement = 0.03
    marge = 0.35
    while True:
        try:
            ball = client.ball
            defense.defense_passive(robot, ball, zone_defense, erreur_placement, vitesse, marge)
        except:
            penalty.can_move("green", 2)
            time.sleep(1)