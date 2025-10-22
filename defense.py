import rsk
from REMI import Defense
from REMI import Mouvement
from rsk import constants
import time

with rsk.Client() as client:
    mouvement = Mouvement(client)
    defense = Defense(client)
    robot = client.green2
    zone_defense = (1.84/2,0)
    while True:
        ball = client.ball
        remi.defense_passive(robot, ball, zone_defense)
        