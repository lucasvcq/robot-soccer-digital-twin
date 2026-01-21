import rsk
from REMI import remi
from Jules_Execute import action
from Jules import formule
import time

class Game:
    def __init__(self, client, color):
        self.client = client
        self.color = color
        self.opponent_color = 'blue' if color == 'green' else 'green'

    def update_info(self):
        # --- GESTION DU CÔTÉ ET DES CIBLES ---
        try:
            is_positive = self.client.referee["teams"][self.color]["x_positive"]
        except KeyError:
            # Sécurité si l'arbitre n'est pas encore prêt
            is_positive = False 

        # On définit les coordonnées en fonction du côté
        if is_positive:
            # On est à Droite (+), on défend à Droite, on attaque à Gauche (-)
            self.target_def = (0.9, 0)
            self.target_att = (-0.9, 0)
            self.sens_but = -1 
            self.terrain = "droit"
        else:
            # On est à Gauche (-), on défend à Gauche, on attaque à Droite (+)
            self.target_def = (-0.9, 0)
            self.target_att = (0.9, 0)
            self.sens_but = 1
            self.terrain = "gauche"

        # --- GESTION DES PÉNALITÉS ---
        self.nos_actifs = []
        self.nos_penalises = []
        
        self.adv_actifs = []
        self.adv_penalises = []

        # --- TRAITEMENT DE MON ÉQUIPE  ---
        for i in [1, 2]:
            # Vérif pénalité
            is_penalized = self.client.referee["teams"][self.color]["robots"][str(i)]["penalized"]
            
            nom_robot = f"{self.color}{i}"
            robot_obj = getattr(self.client, nom_robot)

            if is_penalized:
                self.nos_penalises.append(robot_obj)
            else:
                self.nos_actifs.append(robot_obj)

        # --- TRAITEMENT DE L'ÉQUIPE ADVERSE  ---
        for i in [1, 2]:
            # Vérif pénalité (Attention : on regarde dans couleur_adverse)
            is_penalized = self.client.referee["teams"][self.opponent_color]["robots"][str(i)]["penalized"]
            
            nom_robot = f"{self.opponent_color}{i}"
            robot_obj = getattr(self.client, nom_robot)

            if is_penalized:
                self.adv_penalises.append(robot_obj)
            else:
                self.adv_actifs.append(robot_obj)

        # Mises à jour des compteurs pour simplifier les conditions
        self.nb_nos_actifs = len(self.nos_actifs)
        self.nb_adv_actifs = len(self.adv_actifs)

    def executer_strategie(self):
        # 1. On met à jour les données (le "cerveau" scanne le terrain)
        self.update_info()

        # 2. Prise de décision basée sur les variables self déjà calculées
        if self.nb_nos_actifs == 2:
            if self.nb_adv_actifs == 2:
                print(">>> 2 vs 2 : Match classique")

            elif self.nb_adv_actifs == 1:
                print(">>> Supériorité numérique")
                Action.supériorité_numérique(self.nos_actifs[0],self.nos_actifs[1],self.adv_penalises[0],self.terrain,self.target_def)

            elif self.nb_adv_actifs == 0:
                print(">>> Aucun adversaire sur le terrain")
                Action.Aucun_adversaire(self.nos_actifs[0],self.nos_actifs[1],self.terrain)
                
        elif self.nb_nos_actifs == 1:
            if self.nb_adv_actifs == 2:
                print(">>> 1 vs 2 : Infériorité numérique")
                N_robot = self.nos_actifs[0]
                Remi.defense_passive(N_robot,self.client.ball, self.target_def, 0.05,3.0,0.3,0.15,"front",time.time(),0.2)

            elif self.nb_adv_actifs == 1:
                print(">>> 1 vs 1 : Match réduit")
                N_robot = self.nos_actifs[0]
                A_robot = self.adv_actifs[0]
                N = Formule.distance_ball(N_robot) # Notre robot
                A = Formule.distance_ball(A_robot) # Robot adverse
                if A > N : 
                    Action.Tire_vers_le_but(N_robot,self.terrain)
                else : 
                    Remi.defense_passive(N_robot,self.client.ball, self.target_def, 0.05,3.0,0.3,0.15,"front",time.time(),0.2)

            elif self.nb_adv_actifs == 0: 
                print(">>> Aucun adversaire sur le terrain")
                N_robot = self.nos_actifs[0] 
                Action.Tire_vers_le_but(N_robot, self.terrain)

def choisir_couleur():
    while True:
        try:
            print("\n--- CONFIGURATION DU MATCH ---")
            choix = input("Choisis ton équipe (green / blue) : ").strip().lower()
            if choix in ['green', 'blue']:
                return choix
            print(" Erreur : Ecris juste 'green' ou 'blue'.")
        except KeyboardInterrupt:
            print("\nAnnulation.")
            

if __name__ == "__main__":
    N_couleur = choisir_couleur()
    with rsk.Client() as client:
        game = Game(client,N_couleur) # On peut automatiser la couleur
        Remi = remi(client)
        Action = action(client)
        Formule = formule(client)

        print("--- DÉBUT DU MATCH ---")
        # C'est LA SEULE boucle while True du programme
        while True:
            # A chaque tour, on demande au cerveau de réfléchir et d'agir UNE fois
            try:
                game.executer_strategie()
                # Petite pause pour ne pas surchauffer le processeur inutilement
                # (optionnel selon la réactivité voulue)
            except KeyboardInterrupt:
                print("Arrêt du match demandé.")
                break



