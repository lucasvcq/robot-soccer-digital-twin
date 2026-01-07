import rsk 
from Jules import formule
from test_remi import remi
import threading

# ====================================================== #
# ================== GAME MANAGER ====================== #
# ====================================================== #

class Game :
    def __init__(self, client):
        self.client = client
        self.couleur = None
        self.couleur_adverse = None

    def choisir_couleur(self):
        print("Choisis la couleur : 'green' ou 'blue'")
        self.couleur = input(">").strip().lower()
        
        if self.couleur == 'green' :
            self.couleur_adverse = 'blue'
        
        elif self.couleur == 'blue':
            self.couleur_adverse = 'green'

        print(f"Couleur choisie : {self.couleur}")
        print(f"Couleur adverse : {self.couleur_adverse}")

    def zone_defense(self, color):
        side = self.client.referee["teams"][color]["x_positive"]  # "left" ou "right"
        print(side)
        return (-0.9, 0) if side == False else (0.9, 0)

    def zone_attack(self, color):
        side = self.client.referee["teams"][color]["x_positive"]
        return (0.9, 0) if side == False else (-0.9, 0)

    def direction_goal(self, color):
        side = self.client.referee["teams"][color]["x_positive"]
        return 1 if side == True else -1

    def is_penalized(self, team, robot_id):
        return self.client.referee["teams"][team]["robots"][str(robot_id)]["penalized"]
    
# ====================================================== #
# ================= ROBOT Stratégie ==================== #
# ====================================================== #

    def stratégie(self) : 
    
        while True :

            notre_robots_penalises = []
            for i in range(1, 3) :
                penalite = self.is_penalized(self.couleur, i)
                notre_robots_penalises.append(penalite)

            adversaire_robots_penalises = []
            for i in range(1, 3) :
                penalite = self.is_penalized(self.couleur_adverse, i)
                adversaire_robots_penalises.append(penalite)

            nb_nos_penalises = sum(notre_robots_penalises)
            nb_adv_penalises = sum(adversaire_robots_penalises)

            # --- 1. CAS OÙ NOUS SOMMES AU COMPLET (2 robots sur le terrain) ---
            if nb_nos_penalises == 0:
                if nb_adv_penalises == 0:
                    print("SITUATION : 2 vs 2. Match classique.")

                elif nb_adv_penalises == 1:
                    print("SITUATION : 2 vs 1. Supériorité numérique, on attaque !")

                elif nb_adv_penalises == 2:
                    print("SITUATION : 2 vs 0. Champ libre, but obligatoire !")

            # --- 2. CAS OÙ NOUS AVONS UN ROBOT PÉNALISÉ (1 robot sur le terrain) ---
            elif nb_nos_penalises == 1:
                if nb_adv_penalises == 0:
                    print("SITUATION : 1 vs 2. Infériorité numérique, prudence.")

                elif nb_adv_penalises == 1:
                    print("SITUATION : 1 vs 1. Duel de capitaines.")

                elif nb_adv_penalises == 2:
                    print("SITUATION : 1 vs 0. On est seuls, on fonce au but.")
                
            # --- 3. CAS OÙ NOUS SOMMES TOUS PÉNALISÉS (0 robot sur le terrain) ---
            elif nb_nos_penalises == 2:
                if nb_adv_penalises == 0:
                    print("SITUATION : 0 vs 2. On attend que nos robots reviennent...")
                elif nb_adv_penalises == 1:
                    print("SITUATION : 0 vs 1. Danger, l'adversaire est seul sur le terrain.")
                elif nb_adv_penalises == 2:
                    print("SITUATION : 0 vs 0. Désert total, tout le monde est exclu.")








