import sys, os
sys.path.append(os.path.dirname(__file__))
import math
import time
import rsk
from rsk import constants
from field_utils import FieldUtils
from robot_agent import RobotAgent
import config # Importe les constantes

class TwoRobotsShooter:

    def __init__(self):
        print("Initialisation de TwoRobotsShooter...")
        try:
            self.client = rsk.Client()
        except Exception as e:
            print(f"Erreur de connexion au client RSK: {e}")
            sys.exit(1)
            
        print("Client RSK connecté ✅")
        
        # Définir le but
        self.goal = (-constants.field_length/2.0, 0.0)
        
        # Créer les instances des agents
        self.agent1 = RobotAgent(self.client.green1, self.goal, "green1")
        self.agent2 = RobotAgent(self.client.green2, self.goal, "green2")
        
        # État du jeu
        self.active_agent = None
        self.passive_agent = None
        self.last_switch_time = 0.0
        
        print("Agents créés. Prêt à démarrer.")

    def choose_actor(self, ball):
        """Choisit l'agent actif basé sur la distance et l'hystérésis."""
        g1_pos = self.client.green1.position
        g2_pos = self.client.green2.position

        if ball is None or g1_pos is None or g2_pos is None:
            return False # Impossible de choisir

        d1 = FieldUtils.dist(g1_pos, ball)
        d2 = FieldUtils.dist(g2_pos, ball)

        now = time.time()
        actor_changed = False
        
        # Cas 1: Aucun acteur n'est défini
        if self.active_agent is None:
            if d1 <= d2:
                self.active_agent = self.agent1
                self.passive_agent = self.agent2
            else:
                self.active_agent = self.agent2
                self.passive_agent = self.agent1
            self.last_switch_time = now
            actor_changed = True

        # Cas 2: Changer si le temps minimum est écoulé ET la marge est dépassée
        elif now - self.last_switch_time > config.MIN_ACTOR_TIME:
            if self.active_agent == self.agent1 and d2 + config.SWITCH_MARGIN < d1:
                self.active_agent = self.agent2
                self.passive_agent = self.agent1
                self.last_switch_time = now
                actor_changed = True
            elif self.active_agent == self.agent2 and d1 + config.SWITCH_MARGIN < d2:
                self.active_agent = self.agent1
                self.passive_agent = self.agent2
                self.last_switch_time = now
                actor_changed = True
        
        if actor_changed:
            print(f"Nouvel acteur : {self.active_agent.name} (d1={d1:.2f}, d2={d2:.2f})")
            # Quand on change, on réinitialise l'état de contournement de l'ancien acteur
            if self.passive_agent:
                 self.passive_agent._stop_around("Perte du focus (devient passif)")
                 
        return True # Acteur choisi (ou gardé)

    def run(self):
        """Boucle principale du jeu."""
        print("Démarrage de la boucle principale...")
        while True:
            try:
                ball = self.client.ball
                
                # 1. Choisir l'acteur
                if not self.choose_actor(ball):
                    print("En attente de données (balle/robots)...")
                    time.sleep(config.LOOP_DT)
                    continue

                # 2. Mettre à jour l'agent actif (DÉLÉGATION)
                # La méthode update_state contient toute la logique de l'agent
                # et renvoie True si un tir a eu lieu.
                kick_happened = self.active_agent.update_state(ball)

                # 3. Gérer le post-tir
                if kick_happened:
                    print(f"Tir réussi par {self.active_agent.name}! Réinitialisation.")
                    # Forcer le changement d'acteur à la prochaine boucle
                    self.active_agent = None 
                    self.last_switch_time = time.time()
                    time.sleep(0.5) # Pause après le tir
                
                # 4. Gérer l'agent passif (exemple: aller en défense)
                if self.passive_agent:
                    # Mettez ici la logique passive, ex:
                    # self.passive_agent.robot.goto((-0.3, 0.0, 0.0), wait=False)
                    pass

                # 5. Attendre le prochain cycle
                time.sleep(config.LOOP_DT)
                
            except Exception as e:
                print(f"Erreur dans la boucle principale: {e}")
                # En cas d'erreur client, on peut essayer de recréer les agents
                if "client" in str(e).lower():
                    print("Tentative de reconnexion...")
                    self.client.close()
                    time.sleep(1)
                    self.__init__() # Ré-initialiser
                else:
                    time.sleep(1) # Attendre avant de réessayer

    def close(self):
        """Ferme la connexion client proprement."""
        if hasattr(self, 'client') and self.client:
            self.client.close()
            print("Client RSK déconnecté.")

# --- Point d'entrée du programme ---
if __name__ == "__main__":
    game = None
    try:
        # 1. On CRÉE l'objet "chef d'orchestre"
        game = TwoRobotsShooter()
        
        # 2. On LANCE sa boucle principale
        game.run()
        
    except KeyboardInterrupt:
        print("\nArrêt du programme (Ctrl+C).")
    except Exception as e:
        print(f"Une erreur fatale est survenue: {e}")
    finally:
        # 3. On s'assure de fermer proprement
        if game:
            game.close()