def Placement_vers_objectif(self, robot, Angle_robot, Objectif): 
        B = self.client.ball

        points = []
        rayon = [0.15,0.2,0.2,0.2,0.15]
        steps = 4

        Angle_robot_norm = self.normalize_angle(Angle_robot)
        Objectif_norm = self.normalize_angle(Objectif)
        d = Objectif_norm - Angle_robot_norm        
        delta_angle = self.normalize_angle(d)
        
        for i in range(steps + 1):  
            AB = Angle_robot_norm + (i / steps) * delta_angle 
            x = B[0] + rayon[i] * math.cos(AB)
            y = B[1] + rayon[i] * math.sin(AB)
            points.append((x, y))

        index = 0
        fin_x, fin_y = points[-1]

        while True:
            x_robot, y_robot = robot.position
            theta_robot = robot.orientation
            dx = points[0][0] - x_robot
            dy = points[0][1] - y_robot

            distance = self.distance_objectif_objectif(robot.position,points[0])
            print(distance)

            if distance < 0.1 :
                break

            # 3. La formule magique (Rotation de repère)
            # On transforme le vecteur global (dx, dy) en vecteur robot (vx, vy)
            # C'est de la trigonométrie : on tourne le vecteur de l'angle -theta
            vx_local = dx * cos(theta_robot) + dy * sin(theta_robot)
            vy_local = -dx * sin(theta_robot) + dy * cos(theta_robot)

            # --- 4. Vitesse Maximale Constante ---
            VITESSE_CIBLE = 0.5  # Vitesse désirée en m/s (ex: 1.0 c'est très rapide)

            # On calcule la norme (la longueur) du vecteur local
            norme_vecteur = sqrt(vx_local**2 + vy_local**2)

            if norme_vecteur > 0:
                # On "normalise" le vecteur (on le ramène à une longueur de 1)
                # Puis on multiplie par la vitesse cible pour forcer l'allure
                vitesse_x = (vx_local / norme_vecteur) * VITESSE_CIBLE
                vitesse_y = (vy_local / norme_vecteur) * VITESSE_CIBLE
            else:
                vitesse_x = 0
                vitesse_y = 0

            # 5. Envoyer la commande
            robot.control(vitesse_x, vitesse_y, 0)
            
            time.sleep(0.05)

        while index < steps - 1:
            a = robot.position
            b = points[index+1]

            distance = self.distance_objectif_objectif(a, b)
            Seuil_atteinte_point = 0.4
            
            index += 1

            ox = points[index][0]
            oy = points[index][1]

            robot.goto((ox, oy, Objectif-pi), wait = False)
            time.sleep(0.25)

        robot.goto((fin_x, fin_y, Objectif-pi))



import rsk
from REMI import remi
from Jules_Execute import action
from Jules import formule
import time

class Game:
    # On récupère les instances des modules ici pour les stocker dans 'self'
    def __init__(self, client, color, action_mod, remi_mod, formule_mod):
        self.client = client
        self.color = color
        self.opponent_color = 'blue' if color == 'green' else 'green'
        
        # Stockage des "Outils" dans le cerveau du jeu
        self.action = action_mod
        self.remi = remi_mod
        self.formule = formule_mod

    def update_info(self):
        # --- GESTION DU CÔTÉ ET DES CIBLES ---
        try:
            # Sécurité : vérifier si l'info est dispo
            if self.color not in self.client.referee["teams"]:
                return
            is_positive = self.client.referee["teams"][self.color]["x_positive"]
        except (KeyError, TypeError):
            is_positive = False 

        # On définit les coordonnées en fonction du côté
        if is_positive:
            self.target_def = (0.9, 0)
            self.target_att = (-0.9, 0)
            self.sens_but = -1 
            self.terrain = "droit"
        else:
            self.target_def = (-0.9, 0)
            self.target_att = (0.9, 0)
            self.sens_but = 1
            self.terrain = "gauche"

        # --- GESTION DES LISTES DE ROBOTS ---
        self.nos_actifs = []
        self.nos_penalises = []
        self.adv_actifs = []
        self.adv_penalises = []

        # --- TRAITEMENT DE MON ÉQUIPE ---
        for i in [1, 2]:
            try:
                is_penalized = self.client.referee["teams"][self.color]["robots"][str(i)]["penalized"]
                robot_obj = getattr(self.client, f"{self.color}{i}")

                if is_penalized:
                    self.nos_penalises.append(robot_obj)
                else:
                    self.nos_actifs.append(robot_obj)
            except: pass

        # --- TRAITEMENT DE L'ÉQUIPE ADVERSE ---
        for i in [1, 2]:
            try:
                is_penalized = self.client.referee["teams"][self.opponent_color]["robots"][str(i)]["penalized"]
                robot_obj = getattr(self.client, f"{self.opponent_color}{i}")

                if is_penalized:
                    self.adv_penalises.append(robot_obj)
                else:
                    self.adv_actifs.append(robot_obj)
            except: pass

        # Mises à jour des compteurs
        self.nb_nos_actifs = len(self.nos_actifs)
        self.nb_adv_actifs = len(self.adv_actifs)

    def executer_strategie(self):
        # 1. On scanne le terrain (Mise à jour des variables self.nb_...)
        self.update_info()

        # 2. Prise de décision
        
        # --- CAS : 2 JOUEURS DISPONIBLES ---
        if self.nb_nos_actifs == 2:
            r1 = self.nos_actifs[0]
            r2 = self.nos_actifs[1]

            if self.nb_adv_actifs == 2:
                print(">>> 2 vs 2")
                

            elif self.nb_adv_actifs == 1:
                # print(">>> Supériorité numérique")
                # CORRECTION IMPORTANTE : On passe l'adversaire ACTIF, pas le pénalisé
                adversaire = self.adv_actifs[0]
                self.action.supériorité_numérique(r1, r2, adversaire, self.terrain, self.target_def)
                
            elif self.nb_adv_actifs == 0:
                # print(">>> Aucun adversaire")
                self.action.Aucun_adversaire(r1, r2, self.terrain)
                
        # --- CAS : 1 SEUL JOUEUR (MODE SURVIE) ---
        elif self.nb_nos_actifs == 1:
            N_robot = self.nos_actifs[0]

            if self.nb_adv_actifs == 2:
                # print(">>> 1 vs 2 : Défense pure")
                self.remi.defense_passive(N_robot, self.client.ball, self.target_def, 0.05, 3.0, 0.3, 0.15, "front", time.time(), 0.2)

            elif self.nb_adv_actifs == 1:
                # print(">>> 1 vs 1 : Duel")
                # CORRECTION : Utilisation de self.formule
                N = self.formule.distance_ball(N_robot) 
                
                # On récupère la distance de l'adversaire s'il existe
                if len(self.adv_actifs) > 0:
                    A = self.formule.distance_ball(self.adv_actifs[0])
                else:
                    A = 999 # Loin

                # Si je suis plus proche que lui -> j'attaque
                if A > N : 
                    self.action.Tire_vers_le_but(N_robot, self.terrain)
                else : 
                    self.remi.defense_passive(N_robot, self.client.ball, self.target_def, 0.05, 3.0, 0.3, 0.15, "front", time.time(), 0.2)

            elif self.nb_adv_actifs == 0: 
                # print(">>> Seul sur le terrain")
                self.action.Tire_vers_le_but(N_robot, self.terrain)

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
            break

if __name__ == "__main__":
    N_couleur = choisir_couleur()
    
    with rsk.Client() as client:
        # 1. Instanciation des outils
        Remi_instance = remi(client)
        Action_instance = action(client)
        Formule_instance = formule(client)

        # 2. Création du cerveau du jeu avec les outils
        game = Game(client, N_couleur, Action_instance, Remi_instance, Formule_instance)

        print("--- DÉBUT DU MATCH ---")
        
        # 3. BOUCLE PRINCIPALE (Game Loop)
        while True:
            try:
                # Le cerveau réfléchit et donne des ordres (wait=False)
                game.executer_strategie()
                
                # Pas de gros sleep ici ! On veut que ça tourne vite.
                # time.sleep(0.01) # Optionnel : micro-pause pour le CPU
                
            except KeyboardInterrupt:
                print("Arrêt du match demandé.")
                break