print("1")
import rsk
from math import sqrt
import time
import threading
from test_remi import remi
print("3")
from Jules_Execute import action
print("4")
from Jules import formule
print("5")
class Game:
    def __init__(self, client, color):
        self.client = client
        self.color = color
        self.opponent_color = 'blue' if color == 'green' else 'green'
        self.start_time = time.time()  # Initialisation du chrono

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
            self.target_def = (0.91, 0)
            self.target_att = (-0.91, 0)
            self.sens_but = -1 
            self.terrain = "droit"
        else:
            # On est à Gauche (-), on défend à Gauche, on attaque à Droite (+)
            self.target_def = (-0.91, 0)
            self.target_att = (0.91, 0)
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
    

    def executer_strategie(self, robot, zone_def, cote, ball, role, ball_last_pos, ball_stop_timer):
        # 1. On met à jour les données (le "cerveau" scanne le terrain)
        self.update_info()
        params = {
            "vitesse": 3.0,
            "err": 0.05,
            "seuil_ball": 0.15,
            "start_time": time.time()
        }
        # 2. Prise de décision basée sur les variables self déjà calculées
        if self.nb_nos_actifs == 2:
            if self.nb_adv_actifs == 2:
                print(">>> 2 vs 2 : Match classique")
                
                elapsed = time.time() - start_time
                print(elapsed)
                # --- 1. DETECTION IMMOBILITÉ BALLE (3 SECONDES) ---
                is_ball_stuck = False
                if ball_last_pos is not None:
                    dist_mouv = sqrt((ball[0]-ball_last_pos[0])**2 + (ball[1]-ball_last_pos[1])**2)
                    if dist_mouv < 0.01: # Si elle bouge de moins d'1cm
                        ball_stop_timer += 0.1
                    else:
                        ball_stop_timer = 0
                    if ball_stop_timer >= 3.0:
                        is_ball_stuck = True
                ball_last_pos = ball

                # --- 2. LOGIQUE STRATÉGIQUE ---

                # Condition : La balle est dans notre camp ?
                # (Si cote=1, notre camp est x > 0. Si cote=-1, notre camp est x < 0)
                ball_dans_notre_camp = (-ball[0] * cote > 0)
                x,y = robot.position
                if y>0:
                    yposition=1
                else:
                    yposition=-1

                # A. MODE DEFENSE (Balle dans notre camp)
                if ball_dans_notre_camp and not is_ball_stuck:
                    print(">>> MODE DEFENSE")
                    Remi.defense_passive(robot, ball, zone_def, params["err"],params["vitesse"], 0.3, params["seuil_ball"], role, -cote, 0.2)

                # B. MODE ATTAQUE (Balle immobile OU Hors de notre camp)
                else:
                    if elapsed < 30:
                        print(">>> MODE ATTAQUE 30")
                        # Les 30 premières secondes
                        if role == "front":
                            # Tir premier poteau (y = 0.3 ou -0.3 selon le côté)
                            but_adv = (-0.9 * cote, 0.25 * yposition) 
                            ##########################remi_obj.attaque(robot, ball, but_adv, offset=0.1)
                        else:
                            # Le deuxième reste aux buts

                            Remi.defense_passive(robot, ball, zone_def, params["err"], params["vitesse"], 0.2, params["seuil_ball"], "back", -cote, 0.2)

                    elif elapsed > 30 and elapsed < 240:
                        print(">>> MODE ATTAQUE 100")
                        # Après 30 secondes : Attaque normale
                        if role == "front":
                            # Tir premier poteau (y = 0.3 ou -0.3 selon le côté)
                            but_adv = (-0.9 * cote, 0.25 * yposition) 
                            #########################remi_obj.attaque(robot, ball, but_adv, offset=0.1)
                        else:
                            # Le deuxième reste aux buts
                            Remi.defense_passive(robot, ball, zone_def, params["err"], params["vitesse"], 0.2, params["seuil_ball"], "back", -cote, 0.2)
                    else:
                        print(">>> MODE ATTAQUE 240")

            if role == "back":
                return
            elif self.nb_adv_actifs == 1:
                try :
                    print(">>> Supériorité numérique")
                    Action.supériorité_numérique(self.nos_actifs[0],self.nos_actifs[1],self.adv_penalises[0],self.terrain,self.target_def)
                except Exception as e:
                    print(f"Erreur robot: {e}")

            elif self.nb_adv_actifs == 0:
                print(">>> Aucun adversaire sur le terrain")
                Action.Aucun_adversaire(self.nos_actifs[0],self.nos_actifs[1],self.terrain)
        elif role == "back":
            return  
        elif self.nb_nos_actifs == 1:
            if self.nb_adv_actifs == 2:
                try :
                    print(">>> 1 vs 2 : Infériorité numérique")
                    N_robot = self.nos_actifs[0]
                    Remi.defense_passive(N_robot,self.client.ball, self.target_def, 0.05,3.0,0.3,0.15,"front",time.time(),0.2)
                except Exception as e:
                    print(f"Erreur robot: {e}")

            elif self.nb_adv_actifs == 1:
                try :
                    print(">>> 1 vs 1 : Match réduit")
                    N_robot = self.nos_actifs[0]
                    A_robot = self.adv_actifs[0]
                    N = Formule.distance_ball(N_robot) # Notre robot
                    A = Formule.distance_ball(A_robot) # Robot adverse
                    if A > N : 
                        Action.Tire_vers_le_but(N_robot,self.terrain)
                    else : 
                        Remi.defense_passive(N_robot,self.client.ball, self.target_def, 0.05,3.0,0.3,0.15,"front",time.time(),0.2)
                except Exception as e:
                    print(f"Erreur robot: {e}")

            elif self.nb_adv_actifs == 0:
                try :  
                    print(">>> Aucun adversaire sur le terrain")
                    N_robot = self.nos_actifs[0] 
                    Action.Tire_vers_le_but(N_robot, self.terrain)
                except Exception as e:
                    print(f"Erreur robot: {e}")

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
        game = Game(client, N_couleur)
        Remi = remi(client)
        Action = action(client)
        Formule = formule(client)

        print(f"--- DÉBUT DU MATCH ({N_couleur.upper()}) ---")
        start_time = time.time()
        ball_last_pos = None
        ball_stop_timer = 0
        game.update_info()
        r1=game.nos_actifs[0]
        r2=game.nos_actifs[1]

        # Fonction que chaque thread va exécuter en boucle

        while True:
            try:
                game.update_info()
                t1 = threading.Thread(target=game.executer_strategie, args=(r1, game.target_def, game.sens_but, client.ball, "front", ball_last_pos, ball_stop_timer), daemon=True)
                t2 = threading.Thread(target=game.executer_strategie, args=(r2, game.target_def, game.sens_but, client.ball, "back", ball_last_pos, ball_stop_timer), daemon=True)

                t1.start()
                t2.start()
                time.sleep(0.05) # Fréquence de rafraîchissement
            except Exception as e:
                print(f"Erreur sur {client.green1}: {e}")
                break

