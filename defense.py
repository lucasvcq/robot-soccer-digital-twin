import rsk
from REMI import defense
from rsk import constants
import time

with rsk.Client() as client:
    remi = defense(client)
    robot = client.green2
    zone_defense = (1.84/2,0)
    while True:
        ball = client.ball
        remi.defense_passive(robot, ball, zone_defense)
        