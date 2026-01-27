"""
🎮 STRATÉGIE COMPLÈTE - Robot Soccer
Orchestre attaque et défense selon les situations de jeu

RÈGLES :
- 0-30s : Tir direct au but (1er poteau), gardien
- 30s+ : Stratégie adaptive selon position et score
- Dernière minute : Pression si perdant/égalité
- Gestion des pénalités adverses et nôtres
"""
import time
import rsk
from rsk.client import ClientError
from typing import Tuple, Optional
from enum import Enum

# Imports des modules existants
from field_utils import FieldUtils
from game_state import GameState
from referee_manager import RefereeManager
from defense_corrected import DefenseCorrected  # MODIFIÉ : Utilise la version corrigée
from team_controller import TeamController
import config


class GamePhase(Enum):
    """Phases du jeu"""
    EARLY_GAME = "early"      # 0-30s : Tir direct
    MID_GAME = "mid"          # 30s-dernière minute
    LATE_GAME = "late"        # Dernière minute
    

class GameMode(Enum):
    """Modes de jeu"""
    DEFENSE = "defense"       # Défense passive
    ATTACK_SHOOT = "attack_shoot"  # Attaque : tir direct
    ATTACK_PASS = "attack_pass"    # Attaque : passe puis tir
    PRESSURE = "pressure"     # Pression (dernière minute)


class StrategyController:
    """Contrôleur de stratégie complète"""
    
    def __init__(self, client, our_goal: Tuple[float, float], opponent_goal: Tuple[float, float]):
        """
        Args:
            client: Client RSK
            our_goal: Notre but (à défendre)
            opponent_goal: But adverse (à attaquer)
        """
        self.client = client
        self.our_goal = our_goal
        self.opponent_goal = opponent_goal
        
        # Contrôleurs spécialisés
        self.defense = DefenseCorrected(client)  # MODIFIÉ : Version corrigée
        self.attack = TeamController(client, opponent_goal)
        self.referee = RefereeManager(client, team_color="green")
        
        # État du jeu
        self.game_start_time = None
        self.ball_static_start = None
        self.ball_last_pos = None
        self.current_mode = GameMode.DEFENSE
        self.our_score = 0
        self.opponent_score = 0
        
        # Paramètres défense
        self.defense_config = {
            'vitesse': 4,
            'zone_defense': our_goal,
            'erreur_placement': 0.04,
            'marge_front': 0.3,
            'marge_back': 0.2,
            'seuil_ball': 0.2
        }
        
        # Statistiques
        self.stats = {
            'shots': 0,
            'passes': 0,
            'clearances': 0,
            'mode_changes': 0
        }
    
    def update(self) -> bool:
        """
        Mise à jour principale - appelée à chaque frame
        
        Returns:
            bool: True si une action importante a été effectuée
        """
        # Vérifier si le jeu tourne
        if not self.referee.is_game_running():
            return False
        
        # Initialiser le temps de début
        if self.game_start_time is None:
            self.game_start_time = time.time()
            print("🎮 Match démarré - Stratégie activée !")
        
        # Créer l'état du jeu
        state = GameState.from_client(self.client, self.opponent_goal)
        if not state.is_valid():
            return False
        
        # Vérifications d'urgence
        self._check_penalty_areas(state)
        self._check_referee_rules(state)
        
        # Déterminer la phase et le mode
        phase = self._get_game_phase()
        penalties = self._get_penalty_situation()
        
        # Décider du mode selon la stratégie
        new_mode = self._decide_mode(state, phase, penalties)
        
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.stats['mode_changes'] += 1
            print(f"\n🔄 Changement mode : {new_mode.value}")
        
        # Exécuter le mode
        action_done = self._execute_mode(state, phase, penalties)
        
        return action_done
    
    def _get_game_phase(self) -> GamePhase:
        """Détermine la phase du jeu"""
        if self.game_start_time is None:
            return GamePhase.EARLY_GAME
        
        elapsed = time.time() - self.game_start_time
        
        # Durée d'une mi-temps (à ajuster selon votre config)
        HALF_TIME = 300  # 5 minutes par défaut
        LATE_GAME_THRESHOLD = HALF_TIME - 60  # Dernière minute
        
        if elapsed < 30:
            return GamePhase.EARLY_GAME
        elif elapsed > LATE_GAME_THRESHOLD:
            return GamePhase.LATE_GAME
        else:
            return GamePhase.MID_GAME
    
    def _get_penalty_situation(self) -> dict:
        """Analyse la situation des pénalités"""
        try:
            ref = self.client.referee
            
            # Nos pénalités
            our_r1_pen = ref["teams"]["green"]["robots"]["1"]["penalized"]
            our_r2_pen = ref["teams"]["green"]["robots"]["2"]["penalized"]
            our_penalties = sum([our_r1_pen, our_r2_pen])
            
            # Pénalités adverses
            opp_r1_pen = ref["teams"]["blue"]["robots"]["1"]["penalized"]
            opp_r2_pen = ref["teams"]["blue"]["robots"]["2"]["penalized"]
            opp_penalties = sum([opp_r1_pen, opp_r2_pen])
            
            return {
                'our_penalties': our_penalties,
                'opp_penalties': opp_penalties,
                'our_r1_penalized': our_r1_pen,
                'our_r2_penalized': our_r2_pen
            }
        except:
            return {
                'our_penalties': 0,
                'opp_penalties': 0,
                'our_r1_penalized': False,
                'our_r2_penalized': False
            }
    
    def _is_ball_in_our_half(self, ball: Tuple[float, float]) -> bool:
        """Vérifie si la balle est dans notre moitié"""
        return (ball[0] * self.our_goal[0]) > 0
    
    def _is_ball_static(self, ball: Tuple[float, float], threshold: float = 3.0) -> bool:
        """
        Vérifie si la balle est immobile depuis 3 secondes
        
        Args:
            ball: Position actuelle de la balle
            threshold: Temps en secondes (défaut: 3.0)
        """
        MOVEMENT_THRESHOLD = 0.05  # 5cm
        
        # Première fois
        if self.ball_last_pos is None:
            self.ball_last_pos = ball
            self.ball_static_start = time.time()
            return False
        
        # Calculer le mouvement
        movement = FieldUtils.dist(ball, self.ball_last_pos)
        
        if movement < MOVEMENT_THRESHOLD:
            # Balle immobile
            if self.ball_static_start is None:
                self.ball_static_start = time.time()
            
            # Vérifier le temps
            static_time = time.time() - self.ball_static_start
            if static_time >= threshold:
                return True
        else:
            # Balle a bougé, reset
            self.ball_static_start = None
        
        self.ball_last_pos = ball
        return False
    
    def _decide_mode(self, state: GameState, phase: GamePhase, penalties: dict) -> GameMode:
        """
        Décide du mode de jeu selon la stratégie
        
        Logique :
        1. Gestion des pénalités (prioritaire)
        2. Phase du jeu (early/mid/late)
        3. Position de la balle
        4. Score
        """
        ball = state.ball
        ball_in_our_half = self._is_ball_in_our_half(ball)
        
        # ========== GESTION DES PÉNALITÉS ==========
        
        # Pénalité adverse ET aucune pour nous
        if penalties['opp_penalties'] > 0 and penalties['our_penalties'] == 0:
            if ball_in_our_half:
                # Défense : passe puis tir
                return GameMode.ATTACK_PASS
            else:
                # Attaque : tir direct
                return GameMode.ATTACK_SHOOT
        
        # Pénalité adverse ET pénalité pour nous
        if penalties['opp_penalties'] > 0 and penalties['our_penalties'] > 0:
            # Le plus proche tire, sinon défense
            closest = state.closest_robot
            can_control = self.referee.can_control_robot(str(closest))
            
            if can_control:
                return GameMode.ATTACK_SHOOT
            else:
                return GameMode.DEFENSE
        
        # Aucune pénalité adverse ET 1 pénalité pour nous
        if penalties['opp_penalties'] == 0 and penalties['our_penalties'] >= 1:
            return GameMode.DEFENSE
        
        # ========== PAS DE PÉNALITÉS : STRATÉGIE NORMALE ==========
        
        # PHASE EARLY GAME (0-30s)
        if phase == GamePhase.EARLY_GAME:
            if ball_in_our_half:
                return GameMode.DEFENSE
            else:
                return GameMode.ATTACK_SHOOT  # Tir direct premier poteau
        
        # PHASE LATE GAME (dernière minute)
        if phase == GamePhase.LATE_GAME:
            # Si on perd ou égalité : pression
            if self.our_score <= self.opponent_score:
                return GameMode.PRESSURE
            else:
                # On gagne : défense
                return GameMode.DEFENSE
        
        # PHASE MID GAME (30s - dernière minute)
        if ball_in_our_half:
            # Balle dans notre camp
            ball_static = self._is_ball_static(ball, threshold=3.0)
            
            if ball_static:
                # Balle immobile 3s : passer en attaque
                return GameMode.ATTACK_PASS
            else:
                # Défense normale
                return GameMode.DEFENSE
        else:
            # Balle dans leur camp
            if self.our_score == 0:
                # Pas de but : passe puis tir
                return GameMode.ATTACK_PASS
            else:
                # On a marqué : défense tactique
                return GameMode.DEFENSE
        
        # Défaut : défense
        return GameMode.DEFENSE
    
    def _execute_mode(self, state: GameState, phase: GamePhase, penalties: dict) -> bool:
        """
        Exécute le mode de jeu sélectionné
        
        Returns:
            bool: True si une action importante a été effectuée
        """
        if self.current_mode == GameMode.DEFENSE:
            return self._execute_defense(state)
        
        elif self.current_mode == GameMode.ATTACK_SHOOT:
            return self._execute_attack_shoot(state, phase)
        
        elif self.current_mode == GameMode.ATTACK_PASS:
            return self._execute_attack_pass(state)
        
        elif self.current_mode == GameMode.PRESSURE:
            return self._execute_pressure(state)
        
        return False
    
    def _execute_defense(self, state: GameState) -> bool:
        """Mode défense passive"""
        cfg = self.defense_config
        
        # Robot 1 (front) - Défenseur avant
        if self.referee.can_control_robot("1"):
            try:
                self.defense.defense_front_harasser(
                    self.client.green1, state.ball, cfg['zone_defense'],
                    cfg['vitesse']
                )
            except:
                pass
        
        # Robot 2 (back) - Gardien
        if self.referee.can_control_robot("2"):
            try:
                self.defense.defense_back_goalkeeper(
                    self.client.green2, state.ball, cfg['zone_defense'],
                    cfg['vitesse']
                )
            except:
                pass
        
        return False
    
    def _execute_attack_shoot(self, state: GameState, phase: GamePhase) -> bool:
        """Mode attaque : tir direct au but"""
        
        # Durant EARLY_GAME : 1 attaquant tire, 1 gardien
        if phase == GamePhase.EARLY_GAME:
            attacker_id = state.closest_robot
            defender_id = 2 if attacker_id == 1 else 1
            
            # Attaquant tire
            if self.referee.can_control_robot(str(attacker_id)):
                kick = self.attack.agent1.update_state(state.ball) if attacker_id == 1 else \
                       self.attack.agent2.update_state(state.ball)
                
                if kick:
                    self.stats['shots'] += 1
                    print("⚽ TIR AU BUT (early game) !")
                    return True
            
            # Défenseur reste en gardien
            if self.referee.can_control_robot(str(defender_id)):
                cfg = self.defense_config
                robot = self.client.green1 if defender_id == 1 else self.client.green2
                try:
                    # Utiliser le gardien (back) pour le défenseur en early game
                    self.defense.defense_back_goalkeeper(
                        robot, state.ball, cfg['zone_defense'],
                        cfg['vitesse']
                    )
                except:
                    pass
        else:
            # Utiliser l'attaque normale du TeamController
            kick = self.attack.update()
            if kick:
                self.stats['shots'] += 1
                return True
        
        return False
    
    def _execute_attack_pass(self, state: GameState) -> bool:
        """Mode attaque : passe puis tir"""
        # Utiliser le système de passe du TeamController
        kick = self.attack.update()
        
        if kick:
            self.stats['passes'] += 1
            print("🤝 PASSE RÉALISÉE !")
            return True
        
        return False
    
    def _execute_pressure(self, state: GameState) -> bool:
        """Mode pression (dernière minute si perdant)"""
        # Robot le plus proche bloque/harcèle
        closest_id = state.closest_robot
        other_id = 2 if closest_id == 1 else 1
        
        closest_robot = self.client.green1 if closest_id == 1 else self.client.green2
        other_robot = self.client.green2 if closest_id == 1 else self.client.green1
        
        # Robot proche : défense agressive (front)
        if self.referee.can_control_robot(str(closest_id)):
            cfg = self.defense_config
            try:
                # Utiliser le défenseur front pour le harcèlement
                self.defense.defense_front_harasser(
                    closest_robot, state.ball, cfg['zone_defense'],
                    cfg['vitesse']
                )
            except:
                pass
        
        # Autre robot : se rapprocher à 3cm (opportuniste)
        if self.referee.can_control_robot(str(other_id)):
            dist_to_ball = FieldUtils.dist(other_robot.position, state.ball)
            
            # Minimum 3cm pour éviter pénalité
            if dist_to_ball > 0.03:
                # Se rapprocher
                angle_to_ball = FieldUtils.angle(other_robot.position, state.ball)
                try:
                    other_robot.goto(
                        (state.ball[0], state.ball[1], angle_to_ball),
                        wait=False
                    )
                except:
                    pass
            else:
                # Assez proche : tenter le tir si opportunité
                angle_to_goal = FieldUtils.angle(other_robot.position, self.opponent_goal)
                ang_err = abs(FieldUtils.wrap(angle_to_goal - other_robot.orientation))
                
                if ang_err < config.FAST_ANGLE_TOL and dist_to_ball < 0.15:
                    try:
                        other_robot.kick(power=1.0)
                        print("⚽ TIR D'OPPORTUNITÉ !")
                        self.stats['shots'] += 1
                        return True
                    except:
                        pass
        
        return False
    
    def _check_penalty_areas(self, state: GameState):
        """Vérifie et corrige les violations de zones"""
        # Robot 1
        if FieldUtils.is_in_penalty_area(state.robot1_pos, self.opponent_goal[0]):
            safe_pos = FieldUtils.get_safe_position_outside_penalty(
                state.robot1_pos, self.opponent_goal[0]
            )
            angle = FieldUtils.angle(state.robot1_pos, safe_pos)
            print(f"⚠️  R1 sortie zone adverse !")
            try:
                self.client.green1.goto((safe_pos[0], safe_pos[1], angle), wait=False)
            except:
                pass
        
        # Robot 2
        if FieldUtils.is_in_penalty_area(state.robot2_pos, self.opponent_goal[0]):
            safe_pos = FieldUtils.get_safe_position_outside_penalty(
                state.robot2_pos, self.opponent_goal[0]
            )
            angle = FieldUtils.angle(state.robot2_pos, safe_pos)
            print(f"⚠️  R2 sortie zone adverse !")
            try:
                self.client.green2.goto((safe_pos[0], safe_pos[1], angle), wait=False)
            except:
                pass
    
    def _check_referee_rules(self, state: GameState):
        """Vérifie les règles de l'arbitre (abus de balle)"""
        # Robot 1
        if self.referee.check_ball_abuse("1", state.robot1_pos, state.ball):
            if self.referee.should_retreat_from_ball("1", state.robot1_pos, state.ball):
                retreat = self.referee.get_retreat_position(state.robot1_pos, state.ball)
                try:
                    self.client.green1.goto(
                        (retreat[0], retreat[1], state.robot1_theta),
                        wait=False
                    )
                except:
                    pass
        
        # Robot 2
        if self.referee.check_ball_abuse("2", state.robot2_pos, state.ball):
            if self.referee.should_retreat_from_ball("2", state.robot2_pos, state.ball):
                retreat = self.referee.get_retreat_position(state.robot2_pos, state.ball)
                try:
                    self.client.green2.goto(
                        (retreat[0], retreat[1], state.robot2_theta),
                        wait=False
                    )
                except:
                    pass
    
    def print_stats(self):
        """Affiche les statistiques"""
        print(f"\n{'='*60}")
        print("📊 STATISTIQUES DU MATCH")
        print(f"{'='*60}")
        print(f"⚽ Tirs        : {self.stats['shots']}")
        print(f"🤝 Passes      : {self.stats['passes']}")
        print(f"🔄 Changements : {self.stats['mode_changes']}")
        print(f"🎮 Mode actuel : {self.current_mode.value}")
        
        if self.game_start_time:
            elapsed = time.time() - self.game_start_time
            print(f"⏱️  Temps écoulé: {elapsed:.1f}s")
        
        print(f"{'='*60}\n")


def main():
    """Point d'entrée principal"""
    print("="*60)
    print("🎮 STRATÉGIE COMPLÈTE - Robot Soccer")
    print("="*60)
    
    # Configuration des buts (depuis config.py)
    opponent_goal = config.GOAL_POSITION       # But adverse (on attaque)
    our_goal = config.OUR_GOAL_POSITION        # Notre but (on défend)
    
    print(f"🛡️  Notre but    : {our_goal}")
    print(f"🎯 But adverse  : {opponent_goal}")
    print("="*60 + "\n")
    
    try:
        with rsk.Client() as client:
            controller = StrategyController(client, our_goal, opponent_goal)
            
            print("✅ Connexion établie")
            print("⏳ En attente du match...\n")
            
            try:
                while True:
                    try:
                        action = controller.update()
                        
                        if action and config.DEBUG_STRATEGY:
                            controller.print_stats()
                    
                    except ClientError as e:
                        if "preempted" not in str(e):
                            print(f"⚠️  Erreur: {e}")
                        time.sleep(0.1)
                    
                    time.sleep(config.LOOP_DT)
            
            except KeyboardInterrupt:
                print("\n⏹️  ARRÊT MANUEL")
                controller.print_stats()
    
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n👋 Programme terminé\n")


if __name__ == "__main__":
    main()