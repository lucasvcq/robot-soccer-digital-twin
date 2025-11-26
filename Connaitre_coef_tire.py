import threading
import rsk 
from Jules import formule

with rsk.Client() as client: 
    Formule = formule(client)
    P = Formule.calcul_coefficient(client.green1)
    print(f"La distance pour un kick(1) est {P}")