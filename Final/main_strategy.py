"""
🎮 STRATÉGIE INTELLIGENTE ET ADAPTATIVE - Robot Soccer

FONCTIONNALITÉS :
1. Tir PREMIER POTEAU (Y=±0.25 selon position du robot)
2. Détection immobilité balle (3s → attaque)
3. Phases temporelles ADAPTATIVES :
   - 0-30s : Tirs directs simples
   - 30s+ : Passe puis tir SI score = 0 (sinon continue direct)
4. Gestion du SCORE :
   - Si on mène en tirant direct → on continue direct
   - Si on ne marque pas → on passe à la stratégie passe
   - Si on mène bien → on renforce la défense (mais on attaque quand même)
"""
import time
import threading
import rsk
from rsk.client import ClientError
from typing import Tuple, Optional
from enum import Enum
from math import sqrt

from field_utils import FieldUtils
from game_state import GameState
from referee_manager import RefereeManager
from defense import Defense
from robot_agent import RobotAgent
from team_manager import TeamManager, choose_team_interactive
import config


class AttackStrategy(Enum):
    """Stratégies d'attaque"""
    DIRECT_SHOOT = "direct"      # Tir direct (premier poteau)
    PASS_AND_SHOOT = "pass"      # Passe puis tir


class SmartStrategyController:
    """Contrôleur INTELLIGENT avec stratégie adaptative"""
    
    def __init__(self, client, team_manager: TeamManager):
        self.client = client
        self.team_manager = team_manager
        
        # Buts et robots
        self.our_goal, self.opponent_goal = team_manager.get_current_goals()
        self.robot1, self.robot2 = team_manager.get_robots(client)
        
        # DEBUG : Afficher la configuration des buts
        print("\n" + "="*70)
        print(f"🔧 CONFIGURATION INITIALE - {team_manager.team_color.upper()}")
        print("="*70)
        print(f"🛡️  Notre but à DÉFENDRE  : {self.our_goal}")
        print(f"🎯 But adverse à ATTAQUER : {self.opponent_goal}")
        print(f"🤖 Robot 1 : {self.robot1}")
        print(f"🤖 Robot 2 : {self.robot2}")
        print("="*70 + "\n")
        
        # Agents
        self.agent1 = RobotAgent(self.robot1, self.opponent_goal, f"{team_manager.team_color.capitalize()}1")
        self.agent2 = RobotAgent(self.robot2, self.opponent_goal, f"{team_manager.team_color.capitalize()}2")
        
        # Défense et arbitre
        self.defense = Defense(client)
        self.referee = RefereeManager(client, team_color=team_manager.team_color)
        
        # État partagé (thread-safe)
        self.lock = threading.Lock()
        self.game_running = True
        self.game_start_time = None
        
        # NOUVEAU : Détection immobilité balle
        self.ball_last_pos = None
        self.ball_static_timer = 0.0
        self.ball_is_static = False
        
        # NOUVEAU : Gestion du score et stratégie adaptative
        self.our_score = 0
        self.opponent_score = 0
        self.total_shots = 0
        self.shots_without_goal = 0  # Tirs sans but depuis dernier changement stratégie
        
        # NOUVEAU : Stratégie d'attaque (adaptatif)
        self.attack_strategy = AttackStrategy.DIRECT_SHOOT  # Commence simple
        self.last_strategy_change_time = 0
        
        # Config
        self.vitesse_defense = 4
    
    def _update_ball_static_detection(self, ball: Tuple[float, float], dt: float = 0.05):
        """
        Détecte si la balle est immobile pendant 3s
        
        Args:
            ball: Position actuelle de la balle
            dt: Temps écoulé depuis dernière vérification
        """
        if self.ball_last_pos is None:
            self.ball_last_pos = ball
            return
        
        # Distance parcourue
        movement = sqrt(
            (ball[0] - self.ball_last_pos[0])**2 + 
            (ball[1] - self.ball_last_pos[1])**2
        )
        
        if movement < 0.01:  # Moins de 1cm = immobile
            self.ball_static_timer += dt
            if self.ball_static_timer >= 3.0:
                if not self.ball_is_static:
                    self.ball_is_static = True
                    print("⏸️  BALLE IMMOBILE détectée (3s) → ATTAQUE FORCÉE")
        else:
            self.ball_static_timer = 0.0
            self.ball_is_static = False
        
        self.ball_last_pos = ball
    
    def _get_game_phase(self) -> str:
        """
        Retourne la phase de jeu
        
        Returns:
            "early" (0-30s) ou "mid" (30s+)
        """
        if self.game_start_time is None:
            return "early"
        
        elapsed = time.time() - self.game_start_time
        
        if elapsed < 30:
            return "early"
        else:
            return "mid"
    
    def _should_adapt_strategy(self) -> bool:
        """
        Décide si on doit changer de stratégie d'attaque
        
        Logique INTELLIGENTE :
        1. < 30s : TOUJOURS tir direct (phase apprentissage)
        2. 30s+ ET aucun but marqué avec tirs directs → PASSER aux passes
        3. Si on a marqué en direct → CONTINUER en direct
        4. Changement max 1 fois par 30s (éviter oscillations)
        
        Returns:
            bool: True si changement de stratégie nécessaire
        """
        phase = self._get_game_phase()
        current_time = time.time()
        
        # Règle 1 : < 30s → Toujours direct
        if phase == "early":
            return False
        
        # Règle 2 : Pas de changement trop fréquent
        time_since_last_change = current_time - self.last_strategy_change_time
        if time_since_last_change < 30:
            return False
        
        # Règle 3 : Adaptation selon résultats
        if self.attack_strategy == AttackStrategy.DIRECT_SHOOT:
            # On est en tir direct, doit-on changer ?
            # Si on a tiré 10+ fois sans marquer → essayer les passes
            if self.shots_without_goal >= 10:
                print("\n" + "="*60)
                print("🔄 CHANGEMENT DE STRATÉGIE : DIRECT → PASSE")
                print(f"   Raison : {self.shots_without_goal} tirs sans but")
                print("="*60 + "\n")
                self.attack_strategy = AttackStrategy.PASS_AND_SHOOT
                self.last_strategy_change_time = current_time
                self.shots_without_goal = 0
                return True
        
        elif self.attack_strategy == AttackStrategy.PASS_AND_SHOOT:
            # On est en passe, doit-on revenir au direct ?
            # Si on a marqué récemment → revenir au direct (plus simple)
            if self.our_score > self.opponent_score and self.shots_without_goal < 5:
                print("\n" + "="*60)
                print("🔄 CHANGEMENT DE STRATÉGIE : PASSE → DIRECT")
                print(f"   Raison : On mène {self.our_score}-{self.opponent_score}")
                print("="*60 + "\n")
                self.attack_strategy = AttackStrategy.DIRECT_SHOOT
                self.last_strategy_change_time = current_time
                return True
        
        return False
    
    def _update_score_estimation(self):
        """
        Estime le score (approximatif, pas d'API directe)
        
        Note : Pas d'accès direct au score dans l'API
        On estime en comptant nos tirs qui "semblent" marquer
        """
        # TODO : Si l'API referee expose le score, utiliser :
        # self.our_score = self.client.referee["teams"][team_color]["score"]
        # Pour l'instant, on laisse une estimation approximative
        pass
    
    def _compute_first_post_target(self, robot_pos: Tuple[float, float]) -> Tuple[float, float]:
        """
        Calcule la cible PREMIER POTEAU selon position du robot
        
        Logique :
        - Robot en haut (Y > 0) → viser poteau haut (Y = +0.25)
        - Robot en bas (Y < 0) → viser poteau bas (Y = -0.25)
        - Robot au centre → viser centre (Y = 0)
        
        Args:
            robot_pos: Position (x, y) du robot
            
        Returns:
            (x, y): Cible du premier poteau
        """
        goal_x = self.opponent_goal[0]
        
        if robot_pos[1] > 0.15:
            # Robot en HAUT → viser poteau HAUT
            target_y = 0.25
        elif robot_pos[1] < -0.15:
            # Robot en BAS → viser poteau BAS
            target_y = -0.25
        else:
            # Robot au CENTRE → viser centre
            target_y = 0.0
        
        return (goal_x, target_y)
    
    def _get_current_mode_and_roles(self):
        """
        Détermine le mode et les rôles (thread-safe)
        
        Returns:
            (mode, role1, role2, attack_strategy)
        """
        state = GameState.from_client(self.client, self.opponent_goal)
        if not state.is_valid():
            return None, None, None, None
        
        # Mise à jour détection balle immobile
        self._update_ball_static_detection(state.ball)
        
        # Vérifier mi-temps
        if self.team_manager.check_halftime(self.client):
            with self.lock:
                old_opponent_goal = self.opponent_goal
                self.our_goal, self.opponent_goal = self.team_manager.get_current_goals()
                self.agent1.set_target(self.opponent_goal)
                self.agent2.set_target(self.opponent_goal)
                print("\n" + "="*70)
                print("🔄 MI-TEMPS TERMINÉE - CHANGEMENT DE CÔTÉ")
                print("="*70)
                print(f"🛡️  Nouveau but à défendre : {self.our_goal}")
                print(f"🎯 Nouveau but à attaquer  : {self.opponent_goal}")
                print(f"   (Avant : {old_opponent_goal} → Après : {self.opponent_goal})")
                print("="*70 + "\n")
        
        # Compter robots actifs
        r1_active = self.referee.can_control_robot("1")
        r2_active = self.referee.can_control_robot("2")
        our_active = int(r1_active) + int(r2_active)
        
        # CORRECTION : Position de la balle APRÈS mise à jour mi-temps
        ball_x = state.ball[0]
        attacking_left = self.opponent_goal[0] < 0  # Utilise le but MIS À JOUR
        
        if attacking_left:
            ball_in_our_half = ball_x > 0
        else:
            ball_in_our_half = ball_x < 0
        
        # Adaptation stratégique
        self._should_adapt_strategy()
        
        # DÉCISION selon score et balle
        closest_id = state.closest_robot
        
        # Règle spéciale : Si on MÈNE LARGEMENT (2+ buts d'avance) → Défense renforcée
        if self.our_score >= self.opponent_score + 2:
            # On mène bien → 50% temps en défense même si balle dans leur camp
            import random
            if random.random() < 0.5 or ball_in_our_half:
                return "defense", "front", "back", self.attack_strategy
        
        # Mode DEFENSE : Balle dans notre camp (sauf si immobile 3s ET on a 2 robots)
        # CORRECTION : Si 1 seul robot actif (pénalité) → TOUJOURS défendre même si balle immobile
        if ball_in_our_half:
            if our_active == 1:
                # Infériorité numérique → TOUJOURS défendre (ignore balle immobile)
                if self.ball_is_static and config.DEBUG_VERBOSE:
                    print("[Stratégie] Balle immobile MAIS infériorité numérique → DÉFENSE")
                return "defense", "front", "back", self.attack_strategy
            elif not self.ball_is_static:
                # 2 robots actifs → Défendre sauf si balle immobile
                return "defense", "front", "back", self.attack_strategy
        
        # Mode ATTACK
        if our_active == 2:
            if closest_id == 1:
                return "attack", "attacker", "keeper", self.attack_strategy
            else:
                return "attack", "keeper", "attacker", self.attack_strategy
        
        # 1 seul robot actif
        if r1_active and not r2_active:
            return "attack", "attacker", "inactive", self.attack_strategy
        if r2_active and not r1_active:
            return "attack", "inactive", "attacker", self.attack_strategy
        
        return None, None, None, None
    
    def _control_robot1(self):
        """Thread de contrôle du robot 1"""
        while self.game_running:
            try:
                if not self.referee.is_game_running():
                    time.sleep(0.1)
                    continue
                
                # Récupérer mode et rôle
                mode, role1, role2, strategy = self._get_current_mode_and_roles()
                
                if mode is None or role1 == "inactive":
                    time.sleep(0.05)
                    continue
                
                state = GameState.from_client(self.client, self.opponent_goal)
                if not state.is_valid():
                    time.sleep(0.05)
                    continue
                
                # Vérification sécurité
                if FieldUtils.is_in_penalty_area(state.robot1_pos, self.opponent_goal[0]):
                    safe_pos = FieldUtils.get_safe_position_outside_penalty(state.robot1_pos, self.opponent_goal[0])
                    angle = FieldUtils.angle(state.robot1_pos, safe_pos)
                    try:
                        self.robot1.goto((safe_pos[0], safe_pos[1], angle), wait=False)
                    except:
                        pass
                    time.sleep(0.05)
                    continue
                
                # Exécution selon le rôle
                if role1 == "front":
                    try:
                        self.defense.defense_front_harasser(
                            self.robot1, state.ball, self.our_goal, self.vitesse_defense
                        )
                    except:
                        pass
                
                elif role1 == "back":
                    try:
                        self.defense.defense_back_goalkeeper(
                            self.robot1, state.ball, self.our_goal, self.vitesse_defense
                        )
                    except:
                        pass
                
                elif role1 == "attacker":
                    # ATTAQUE avec stratégie adaptative
                    try:
                        if strategy == AttackStrategy.DIRECT_SHOOT or self._get_game_phase() == "early":
                            # TIR DIRECT au PREMIER POTEAU
                            first_post = self._compute_first_post_target(state.robot1_pos)
                            self.agent1.set_target(first_post)
                            kick = self.agent1.update_state(state.ball)
                            
                            if kick:
                                with self.lock:
                                    self.total_shots += 1
                                    self.shots_without_goal += 1
                                print(f"⚽ Robot 1 TIR PREMIER POTEAU Y={first_post[1]:+.2f} ! (Total: {self.total_shots})")
                        
                        else:
                            # Stratégie PASSE (TODO : implémenter si besoin)
                            # Pour l'instant, tir direct quand même
                            first_post = self._compute_first_post_target(state.robot1_pos)
                            self.agent1.set_target(first_post)
                            kick = self.agent1.update_state(state.ball)
                            
                            if kick:
                                with self.lock:
                                    self.total_shots += 1
                                    self.shots_without_goal += 1
                                print(f"⚽ Robot 1 TIR ! (Total: {self.total_shots})")
                    except:
                        pass
                
                elif role1 == "keeper":
                    try:
                        self.defense.defense_back_goalkeeper(
                            self.robot1, state.ball, self.our_goal, self.vitesse_defense
                        )
                    except:
                        pass
                
                time.sleep(0.05)
            
            except Exception as e:
                if config.DEBUG_VERBOSE:
                    print(f"Erreur robot 1: {e}")
                time.sleep(0.1)
    
    def _control_robot2(self):
        """Thread de contrôle du robot 2"""
        while self.game_running:
            try:
                if not self.referee.is_game_running():
                    time.sleep(0.1)
                    continue
                
                # Récupérer mode et rôle
                mode, role1, role2, strategy = self._get_current_mode_and_roles()
                
                if mode is None or role2 == "inactive":
                    time.sleep(0.05)
                    continue
                
                state = GameState.from_client(self.client, self.opponent_goal)
                if not state.is_valid():
                    time.sleep(0.05)
                    continue
                
                # Vérification sécurité
                if FieldUtils.is_in_penalty_area(state.robot2_pos, self.opponent_goal[0]):
                    safe_pos = FieldUtils.get_safe_position_outside_penalty(state.robot2_pos, self.opponent_goal[0])
                    angle = FieldUtils.angle(state.robot2_pos, safe_pos)
                    try:
                        self.robot2.goto((safe_pos[0], safe_pos[1], angle), wait=False)
                    except:
                        pass
                    time.sleep(0.05)
                    continue
                
                # Exécution selon le rôle
                if role2 == "front":
                    try:
                        self.defense.defense_front_harasser(
                            self.robot2, state.ball, self.our_goal, self.vitesse_defense
                        )
                    except:
                        pass
                
                elif role2 == "back":
                    try:
                        # DEBUG : Vérifier le but passé
                        if config.DEBUG_VERBOSE:
                            print(f"[Robot2 BACK] Défend le but : {self.our_goal}")
                        
                        self.defense.defense_back_goalkeeper(
                            self.robot2, state.ball, self.our_goal, self.vitesse_defense
                        )
                    except:
                        pass
                
                elif role2 == "attacker":
                    # ATTAQUE avec stratégie adaptative
                    try:
                        if strategy == AttackStrategy.DIRECT_SHOOT or self._get_game_phase() == "early":
                            # TIR DIRECT au PREMIER POTEAU
                            first_post = self._compute_first_post_target(state.robot2_pos)
                            self.agent2.set_target(first_post)
                            kick = self.agent2.update_state(state.ball)
                            
                            if kick:
                                with self.lock:
                                    self.total_shots += 1
                                    self.shots_without_goal += 1
                                print(f"⚽ Robot 2 TIR PREMIER POTEAU Y={first_post[1]:+.2f} ! (Total: {self.total_shots})")
                        
                        else:
                            # Stratégie PASSE (TODO)
                            first_post = self._compute_first_post_target(state.robot2_pos)
                            self.agent2.set_target(first_post)
                            kick = self.agent2.update_state(state.ball)
                            
                            if kick:
                                with self.lock:
                                    self.total_shots += 1
                                    self.shots_without_goal += 1
                                print(f"⚽ Robot 2 TIR ! (Total: {self.total_shots})")
                    except:
                        pass
                
                elif role2 == "keeper":
                    try:
                        self.defense.defense_back_goalkeeper(
                            self.robot2, state.ball, self.our_goal, self.vitesse_defense
                        )
                    except:
                        pass
                
                time.sleep(0.05)
            
            except Exception as e:
                if config.DEBUG_VERBOSE:
                    print(f"Erreur robot 2: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Démarre les threads de contrôle"""
        # Attendre que le jeu démarre
        while not self.referee.is_game_running():
            time.sleep(0.1)
        
        self.game_start_time = time.time()
        print("\n" + "="*70)
        print("🎮 MATCH DÉMARRÉ - Stratégie INTELLIGENTE activée")
        print("="*70)
        print("📋 PHASES :")
        print("   0-30s  : Tirs directs (apprentissage)")
        print("   30s+   : Adaptation selon résultats")
        print("🎯 LOGIQUE :")
        print("   • Si on marque en direct → on continue")
        print("   • Si 10 tirs sans but → on passe aux passes")
        print("   • Si on mène bien → défense renforcée")
        print("⚽ PREMIER POTEAU : Y=±0.25 selon position")
        print("⏸️  BALLE IMMOBILE : 3s → attaque forcée")
        print("="*70 + "\n")
        
        # Lancer les threads
        t1 = threading.Thread(target=self._control_robot1, daemon=True)
        t2 = threading.Thread(target=self._control_robot2, daemon=True)
        
        t1.start()
        t2.start()
        
        # Boucle principale
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ ARRÊT MANUEL")
            self.game_running = False
            time.sleep(0.2)
    
    def print_stats(self):
        """Affiche les statistiques"""
        elapsed = time.time() - self.game_start_time if self.game_start_time else 0
        print(f"\n{'='*70}")
        print(f"📊 STATISTIQUES - {self.team_manager.team_color.upper()}")
        print(f"{'='*70}")
        print(f"⏱️  Temps écoulé        : {elapsed:.0f}s")
        print(f"⚽ Tirs totaux         : {self.total_shots}")
        print(f"🎯 Stratégie finale    : {self.attack_strategy.value}")
        print(f"📈 Score estimé        : {self.our_score}-{self.opponent_score}")
        print(f"{'='*70}\n")


def main():
    """Point d'entrée"""
    print("="*70)
    print("🎮 STRATÉGIE INTELLIGENTE ET ADAPTATIVE - Robot Soccer")
    print("="*70)
    
    # Choix d'équipe
    team_color = choose_team_interactive()
    team_manager = TeamManager(team_color)
    team_manager.print_status()
    
    print("="*70 + "\n")
    
    try:
        with rsk.Client() as client:
            controller = SmartStrategyController(client, team_manager)
            
            print("✅ Connexion établie")
            print("⏳ En attente du match...\n")
            
            # Démarrer
            controller.start()
            
            # Stats à la fin
            controller.print_stats()
    
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n👋 Programme terminé\n")


if __name__ == "__main__":
    main()