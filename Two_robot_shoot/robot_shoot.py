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
        
        # On définit une cible par défaut (le but adverse)
        self.default_goal = (-constants.field_length/2.0, 0.0)
        
        # On initialise les agents avec cette cible par défaut
        self.agent1 = RobotAgent(self.client.green1, self.default_goal, "green1")
        self.agent2 = RobotAgent(self.client.green2, self.default_goal, "green2")
        
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

    def run(self, target=None, auto_loop=True):
        """
        Boucle principale du jeu.
        :param target: Tuple (x, y) indiquant où tirer. Si None, vise le but par défaut.
        :param auto_loop: Si True, continue à l'infini. Si False, s'arrête après un tir.
        """
        print(f"Démarrage run()... Cible: {'Par défaut' if target is None else target}, Boucle: {auto_loop}")

        # 1. Configuration de la cible pour les deux agents
        # Si un target est donné, on l'utilise, sinon on reprend le self.goal initial
        target_to_use = target if target is not None else self.goal
        
        # On met à jour la cible des agents (nécessite la méthode set_target dans RobotAgent)
        self.agent1.set_target(target_to_use)
        self.agent2.set_target(target_to_use)

        while True:
            try:
                ball = self.client.ball
                
                # 2. Choisir l'acteur
                if not self.choose_actor(ball):
                    # Pas assez d'infos pour choisir, on attend un peu
                    time.sleep(config.LOOP_DT)
                    continue

                # 3. Mettre à jour l'agent actif
                # update_state renvoie True si un kick a été effectué
                kick_happened = self.active_agent.update_state(ball)

                # 4. Gérer le post-tir
                if kick_happened:
                    print(f"Tir/Passe réussi par {self.active_agent.name} !")
                    
                    # --- LOGIQUE D'ARRÊT ---
                    if not auto_loop:
                        print("Mode 'one-shot' activé : Fin de l'exécution.")
                        return True  # On sort de la fonction run, ce qui rend la main au script appelant
                    
                    # Si on est en boucle, on réinitialise pour recommencer
                    self.active_agent = None 
                    self.last_switch_time = time.time()
                    time.sleep(0.5) # Pause tactique après tir
                
                # 5. Gérer l'agent passif (facultatif)
                if self.passive_agent:
                    pass

                # 6. Attendre le prochain cycle
                time.sleep(config.LOOP_DT)
                
            except KeyboardInterrupt:
                # Permet de sortir proprement si on fait Ctrl+C
                print("\nArrêt manuel (KeyboardInterrupt).")
                return False
                
            except Exception as e:
                print(f"Erreur dans la boucle principale: {e}")
                # Gestion basique de reconnexion ou d'attente
                if "client" in str(e).lower():
                    print("Erreur critique client, tentative de reconnexion impossible ici sans ré-init.")
                    time.sleep(2)
                else:
                    time.sleep(1)

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