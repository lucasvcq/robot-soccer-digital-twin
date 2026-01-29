"""
🎮 STRATÉGIE INTELLIGENTE ET ADAPTATIVE - Robot Soccer

VERSION CORRIGÉE - Corrections ciblées:
1. En 1v2 → TOUJOURS défense front (jamais attaque)
2. Correction de l'assignation des rôles en 1v2
3. Implémentation basique de la passe

FONCTIONNALITÉS :
1. Tir PREMIER POTEAU (Y=±0.25 selon position du robot)
2. Détection immobilité balle (3s → attaque) - SEULEMENT en 2v2
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
from decision import DecisionEngine
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
        
        # Moteur de décision (pour les passes)
        self.decision_engine = DecisionEngine(self.opponent_goal)
        
        # Défense et arbitre
        self.defense = Defense(client)
        self.referee = RefereeManager(client, team_color=team_manager.team_color)
        
        # État partagé (thread-safe)
        self.lock = threading.Lock()
        self.game_running = True
        self.game_start_time = None
        
        # Mi-temps
        self.last_halftime_state = None
        
        # Détection immobilité balle
        self.ball_last_pos = None
        self.ball_static_timer = 0.0
        self.ball_is_static = False
        
        # Gestion du score et stratégie adaptative
        self.our_score = 0
        self.opponent_score = 0
        self.total_shots = 0
        self.total_passes = 0
        self.shots_without_goal = 0
        
        # Stratégie d'attaque (adaptatif)
        self.attack_strategy = AttackStrategy.DIRECT_SHOOT
        self.last_strategy_change_time = 0
        
        # Config
        self.vitesse_defense = 4
    
    def _update_ball_static_detection(self, ball: Tuple[float, float], dt: float = 0.05):
        """Détecte si la balle est immobile pendant 3s"""
        if self.ball_last_pos is None:
            self.ball_last_pos = ball
            return
        
        movement = sqrt(
            (ball[0] - self.ball_last_pos[0])**2 + 
            (ball[1] - self.ball_last_pos[1])**2
        )
        
        if movement < 0.01:
            self.ball_static_timer += dt
            if self.ball_static_timer >= 3.0:
                if not self.ball_is_static:
                    self.ball_is_static = True
                    print("⏸️  BALLE IMMOBILE détectée (3s)")
        else:
            self.ball_static_timer = 0.0
            self.ball_is_static = False
        
        self.ball_last_pos = ball
    
    def _get_game_phase(self) -> str:
        """Retourne "early" (0-30s) ou "mid" (30s+)"""
        if self.game_start_time is None:
            return "early"
        elapsed = time.time() - self.game_start_time
        return "early" if elapsed < 30 else "mid"
    
    def _should_adapt_strategy(self) -> bool:
        """Décide si on doit changer de stratégie d'attaque"""
        phase = self._get_game_phase()
        current_time = time.time()
        
        if phase == "early":
            return False
        
        time_since_last_change = current_time - self.last_strategy_change_time
        if time_since_last_change < 30:
            return False
        
        if self.attack_strategy == AttackStrategy.DIRECT_SHOOT:
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
            if self.our_score > self.opponent_score and self.shots_without_goal < 5:
                print("\n" + "="*60)
                print("🔄 CHANGEMENT DE STRATÉGIE : PASSE → DIRECT")
                print(f"   Raison : On mène {self.our_score}-{self.opponent_score}")
                print("="*60 + "\n")
                self.attack_strategy = AttackStrategy.DIRECT_SHOOT
                self.last_strategy_change_time = current_time
                return True
        
        return False
    
    def _compute_first_post_target(self, robot_pos: Tuple[float, float]) -> Tuple[float, float]:
        """Calcule la cible PREMIER POTEAU selon position du robot"""
        with self.lock:
            goal_x = self.opponent_goal[0]
        
        if robot_pos[1] > 0.15:
            target_y = 0.25
        elif robot_pos[1] < -0.15:
            target_y = -0.25
        else:
            target_y = 0.0
        
        return (goal_x, target_y)
    
    def _get_current_mode_and_roles(self):
        """
        Détermine le mode et les rôles (thread-safe)
        
        CORRECTIONS:
        1. En 1v2 → TOUJOURS défense front (peu importe si balle bouge ou pas)
        2. Assignation correcte des rôles selon quel robot est actif
        
        Returns:
            (mode, role1, role2, attack_strategy)
        """
        with self.lock:
            our_goal = self.our_goal
            opponent_goal = self.opponent_goal
        
        state = GameState.from_client(self.client, opponent_goal)
        if not state.is_valid():
            return None, None, None, None
        
        self._update_ball_static_detection(state.ball)
        
        # Compter robots actifs
        r1_active = self.referee.can_control_robot("1")
        r2_active = self.referee.can_control_robot("2")
        our_active = int(r1_active) + int(r2_active)
        
        # Déterminer si la balle est dans notre camp
        ball_x = state.ball[0]
        attacking_left = opponent_goal[0] < 0
        
        if attacking_left:
            ball_in_our_half = ball_x > 0
        else:
            ball_in_our_half = ball_x < 0
        
        # Adaptation stratégique (seulement si 2 robots)
        if our_active == 2:
            self._should_adapt_strategy()
        
        closest_id = state.closest_robot
        
        # ================================================================
        # CAS 0 : AUCUN ROBOT ACTIF
        # ================================================================
        if our_active == 0:
            return None, None, None, None
        
        # ================================================================
        # CAS 1 : UN SEUL ROBOT ACTIF (1v2)
        # → Le robot seul doit être GARDIEN (back) proche de son but
        # ================================================================
        if our_active == 1:
            if r1_active and not r2_active:
                # Robot 1 actif seul → défense BACK (gardien)
                return "defense", "back", "inactive", self.attack_strategy
            elif r2_active and not r1_active:
                # Robot 2 actif seul → défense BACK (gardien)
                return "defense", "inactive", "back", self.attack_strategy
        
        # ================================================================
        # CAS 2 : DEUX ROBOTS ACTIFS (2v2)
        # ================================================================
        
        # Règle spéciale : Si on MÈNE LARGEMENT (2+ buts d'avance)
        if self.our_score >= self.opponent_score + 2:
            import random
            if random.random() < 0.5 or ball_in_our_half:
                return "defense", "front", "back", self.attack_strategy
        
        # Balle dans notre camp
        if ball_in_our_half:
            if not self.ball_is_static:
                # Balle bouge dans notre camp → Défense
                return "defense", "front", "back", self.attack_strategy
            else:
                # Balle immobile 3s dans notre camp → Attaque (selon ta stratégie)
                if closest_id == 1:
                    return "attack", "attacker", "keeper", self.attack_strategy
                else:
                    return "attack", "keeper", "attacker", self.attack_strategy
        
        # Balle dans le camp adverse → Attaque
        if closest_id == 1:
            return "attack", "attacker", "keeper", self.attack_strategy
        else:
            return "attack", "keeper", "attacker", self.attack_strategy
    
    def _check_and_handle_halftime(self):
        """Vérifie et gère le changement de mi-temps"""
        try:
            referee = self.client.referee
            halftime_running = referee.get("halftime_is_running", False)
            game_running = referee.get("game_is_running", False)
            
            if self.last_halftime_state is None:
                self.last_halftime_state = halftime_running
                return False
            
            # Détection transition: mi-temps terminée
            if self.last_halftime_state and not halftime_running and game_running:
                if not self.team_manager.is_second_half:
                    self.team_manager.is_second_half = True
                    
                    with self.lock:
                        old_our = self.our_goal
                        old_opp = self.opponent_goal
                        self.our_goal, self.opponent_goal = self.team_manager.get_current_goals()
                        
                        self.agent1.set_target(self.opponent_goal)
                        self.agent2.set_target(self.opponent_goal)
                        self.decision_engine.goal = self.opponent_goal
                        self.decision_engine.sens_jeu = 1 if self.opponent_goal[0] > 0 else -1
                    
                    print("\n" + "🔴"*30)
                    print("🔴 MI-TEMPS - CHANGEMENT DE CÔTÉ")
                    print(f"🛡️  Défendre: {old_our} → {self.our_goal}")
                    print(f"🎯 Attaquer: {old_opp} → {self.opponent_goal}")
                    print("🔴"*30 + "\n")
                    return True
            
            self.last_halftime_state = halftime_running
            return False
        except:
            return False
    
    def _monitor_halftime(self):
        """Thread de surveillance mi-temps"""
        while self.game_running:
            try:
                self._check_and_handle_halftime()
                time.sleep(0.1)
            except:
                time.sleep(0.5)
    
    def _control_robot1(self):
        """Thread de contrôle du robot 1"""
        last_debug = 0
        
        while self.game_running:
            try:
                if not self.referee.is_game_running():
                    time.sleep(0.1)
                    continue
                
                mode, role1, role2, strategy = self._get_current_mode_and_roles()
                
                if mode is None or role1 == "inactive":
                    time.sleep(0.05)
                    continue
                
                with self.lock:
                    current_opponent_goal = self.opponent_goal
                    current_our_goal = self.our_goal
                
                # Debug toutes les 3 secondes
                if time.time() - last_debug > 3.0:
                    print(f"[R1] Mode={mode}, Rôle={role1}, Strat={strategy.value}")
                    last_debug = time.time()
                
                state = GameState.from_client(self.client, current_opponent_goal)
                if not state.is_valid():
                    time.sleep(0.05)
                    continue
                
                # Sécurité zone adverse
                if FieldUtils.is_in_penalty_area(state.robot1_pos, current_opponent_goal[0]):
                    safe_pos = FieldUtils.get_safe_position_outside_penalty(state.robot1_pos, current_opponent_goal[0])
                    angle = FieldUtils.angle(state.robot1_pos, safe_pos)
                    try:
                        self.robot1.goto((safe_pos[0], safe_pos[1], angle), wait=False)
                    except:
                        pass
                    time.sleep(0.05)
                    continue
                
                # ========== EXÉCUTION DU RÔLE ==========
                if role1 == "front":
                    try:
                        self.defense.defense_front_harasser(
                            self.robot1, state.ball, current_our_goal, self.vitesse_defense
                        )
                    except:
                        pass
                
                elif role1 == "back":
                    try:
                        self.defense.defense_back_goalkeeper(
                            self.robot1, state.ball, current_our_goal, self.vitesse_defense
                        )
                    except:
                        pass
                
                elif role1 == "attacker":
                    try:
                        phase = self._get_game_phase()
                        
                        # 0-30s OU stratégie directe → Tir direct
                        if phase == "early" or strategy == AttackStrategy.DIRECT_SHOOT:
                            first_post = self._compute_first_post_target(state.robot1_pos)
                            self.agent1.set_target(first_post)
                            kick = self.agent1.update_state(state.ball)
                            
                            if kick:
                                with self.lock:
                                    self.total_shots += 1
                                    self.shots_without_goal += 1
                                print(f"⚽ R1 TIR DIRECT Y={first_post[1]:+.2f}")
                        
                        # Après 30s ET stratégie passe → Passe OU tir selon distance
                        elif strategy == AttackStrategy.PASS_AND_SHOOT:
                            # Distance au but adverse
                            dist_to_goal = FieldUtils.dist(state.robot1_pos, current_opponent_goal)
                            
                            # Si assez proche du but → TIR DIRECT
                            if dist_to_goal < config.DIST_SHOOT_LIMIT:
                                first_post = self._compute_first_post_target(state.robot1_pos)
                                self.agent1.set_target(first_post)
                                self.agent1.set_kick_power(config.POWER_SHOOT)
                                kick = self.agent1.update_state(state.ball)
                                
                                if kick:
                                    with self.lock:
                                        self.total_shots += 1
                                        self.shots_without_goal += 1
                                    print(f"⚽ R1 TIR (proche du but) Y={first_post[1]:+.2f}")
                            
                            # Sinon → PASSE au coéquipier
                            else:
                                pass_target = self.decision_engine.compute_pass_target(
                                    state.robot2_pos, state.ball
                                )
                                
                                self.agent1.set_target(pass_target)
                                power = FieldUtils.compute_pass_power(
                                    FieldUtils.dist(state.robot1_pos, pass_target)
                                )
                                self.agent1.set_kick_power(power)
                                
                                kick = self.agent1.update_state(state.ball)
                                
                                if kick:
                                    with self.lock:
                                        self.total_passes += 1
                                        self.shots_without_goal += 1
                                    print(f"🎯 R1 PASSE vers ({pass_target[0]:.2f}, {pass_target[1]:.2f})")
                    except:
                        pass
                
                elif role1 == "keeper":
                    try:
                        self.defense.defense_back_goalkeeper(
                            self.robot1, state.ball, current_our_goal, self.vitesse_defense
                        )
                    except:
                        pass
                
                time.sleep(0.05)
            
            except Exception as e:
                if config.DEBUG_VERBOSE:
                    print(f"Erreur R1: {e}")
                time.sleep(0.1)
    
    def _control_robot2(self):
        """Thread de contrôle du robot 2"""
        while self.game_running:
            try:
                if not self.referee.is_game_running():
                    time.sleep(0.1)
                    continue
                
                mode, role1, role2, strategy = self._get_current_mode_and_roles()
                
                if mode is None or role2 == "inactive":
                    time.sleep(0.05)
                    continue
                
                with self.lock:
                    current_opponent_goal = self.opponent_goal
                    current_our_goal = self.our_goal
                
                state = GameState.from_client(self.client, current_opponent_goal)
                if not state.is_valid():
                    time.sleep(0.05)
                    continue
                
                # Sécurité zone adverse
                if FieldUtils.is_in_penalty_area(state.robot2_pos, current_opponent_goal[0]):
                    safe_pos = FieldUtils.get_safe_position_outside_penalty(state.robot2_pos, current_opponent_goal[0])
                    angle = FieldUtils.angle(state.robot2_pos, safe_pos)
                    try:
                        self.robot2.goto((safe_pos[0], safe_pos[1], angle), wait=False)
                    except:
                        pass
                    time.sleep(0.05)
                    continue
                
                # ========== EXÉCUTION DU RÔLE ==========
                if role2 == "front":
                    try:
                        self.defense.defense_front_harasser(
                            self.robot2, state.ball, current_our_goal, self.vitesse_defense
                        )
                    except:
                        pass
                
                elif role2 == "back":
                    try:
                        self.defense.defense_back_goalkeeper(
                            self.robot2, state.ball, current_our_goal, self.vitesse_defense
                        )
                    except:
                        pass
                
                elif role2 == "attacker":
                    try:
                        phase = self._get_game_phase()
                        
                        if phase == "early" or strategy == AttackStrategy.DIRECT_SHOOT:
                            first_post = self._compute_first_post_target(state.robot2_pos)
                            self.agent2.set_target(first_post)
                            kick = self.agent2.update_state(state.ball)
                            
                            if kick:
                                with self.lock:
                                    self.total_shots += 1
                                    self.shots_without_goal += 1
                                print(f"⚽ R2 TIR DIRECT Y={first_post[1]:+.2f}")
                        
                        elif strategy == AttackStrategy.PASS_AND_SHOOT:
                            # Distance au but adverse
                            dist_to_goal = FieldUtils.dist(state.robot2_pos, current_opponent_goal)
                            
                            # Si assez proche du but → TIR DIRECT
                            if dist_to_goal < config.DIST_SHOOT_LIMIT:
                                first_post = self._compute_first_post_target(state.robot2_pos)
                                self.agent2.set_target(first_post)
                                self.agent2.set_kick_power(config.POWER_SHOOT)
                                kick = self.agent2.update_state(state.ball)
                                
                                if kick:
                                    with self.lock:
                                        self.total_shots += 1
                                        self.shots_without_goal += 1
                                    print(f"⚽ R2 TIR (proche du but) Y={first_post[1]:+.2f}")
                            
                            # Sinon → PASSE au coéquipier
                            else:
                                pass_target = self.decision_engine.compute_pass_target(
                                    state.robot1_pos, state.ball
                                )
                                
                                self.agent2.set_target(pass_target)
                                power = FieldUtils.compute_pass_power(
                                    FieldUtils.dist(state.robot2_pos, pass_target)
                                )
                                self.agent2.set_kick_power(power)
                                
                                kick = self.agent2.update_state(state.ball)
                                
                                if kick:
                                    with self.lock:
                                        self.total_passes += 1
                                        self.shots_without_goal += 1
                                    print(f"🎯 R2 PASSE vers ({pass_target[0]:.2f}, {pass_target[1]:.2f})")
                    except:
                        pass
                
                elif role2 == "keeper":
                    try:
                        # En mode PASS_AND_SHOOT après 30s, le keeper se positionne
                        # pour recevoir la passe au lieu de juste garder
                        phase = self._get_game_phase()
                        
                        if phase != "early" and strategy == AttackStrategy.PASS_AND_SHOOT:
                            # Se positionner pour recevoir
                            pass_target = self.decision_engine.compute_pass_target(
                                state.robot2_pos, state.ball
                            )
                            angle_to_ball = FieldUtils.angle(pass_target, state.ball)
                            self.agent2.goto_position(pass_target, angle_to_ball)
                        else:
                            # Gardien classique
                            self.defense.defense_back_goalkeeper(
                                self.robot2, state.ball, current_our_goal, self.vitesse_defense
                            )
                    except:
                        pass
                
                time.sleep(0.05)
            
            except Exception as e:
                if config.DEBUG_VERBOSE:
                    print(f"Erreur R2: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Démarre les threads"""
        while not self.referee.is_game_running():
            time.sleep(0.1)
        
        self.game_start_time = time.time()
        print("\n" + "="*70)
        print("🎮 MATCH DÉMARRÉ")
        print("="*70)
        print("📋 CORRECTIONS APPLIQUÉES:")
        print("   ✅ 1v2 → Toujours défense front")
        print("   ✅ Stratégie passe implémentée")
        print("📋 PHASES:")
        print("   0-30s: Tir direct premier poteau")
        print("   30s+: Passe (si 10 tirs ratés)")
        print("="*70 + "\n")
        
        t_half = threading.Thread(target=self._monitor_halftime, daemon=True)
        t1 = threading.Thread(target=self._control_robot1, daemon=True)
        t2 = threading.Thread(target=self._control_robot2, daemon=True)
        
        t_half.start()
        t1.start()
        t2.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ ARRÊT")
            self.game_running = False
            time.sleep(0.2)
    
    def print_stats(self):
        """Affiche les stats"""
        elapsed = time.time() - self.game_start_time if self.game_start_time else 0
        print(f"\n{'='*50}")
        print(f"📊 STATS - {self.team_manager.team_color.upper()}")
        print(f"{'='*50}")
        print(f"⏱️  Temps: {elapsed:.0f}s")
        print(f"⚽ Tirs: {self.total_shots}")
        print(f"🎯 Passes: {self.total_passes}")
        print(f"📈 Stratégie: {self.attack_strategy.value}")
        print(f"{'='*50}\n")


def main():
    print("="*70)
    print("🎮 ROBOT SOCCER - VERSION CORRIGÉE")
    print("="*70)
    
    team_color = choose_team_interactive()
    team_manager = TeamManager(team_color)
    team_manager.print_status()
    
    try:
        with rsk.Client() as client:
            controller = SmartStrategyController(client, team_manager)
            print("✅ Connexion OK")
            print("⏳ Attente match...\n")
            controller.start()
            controller.print_stats()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Fin\n")


if __name__ == "__main__":
    main()