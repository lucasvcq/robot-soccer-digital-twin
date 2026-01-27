"""
Contrôleur d'équipe défensive
Orchestre deux robots en défense (un front, un back)
"""
import time
from typing import Tuple
from field_utils import FieldUtils
from game_state import GameState
from defense_agent import DefenseAgent
from referee_manager import RefereeManager
import config

class DefensiveController:
    """
    Contrôleur pour une stratégie défensive à deux robots
    Similaire à TeamController mais spécialisé pour la défense
    """
    
    def __init__(self, client, own_goal: Tuple[float, float], 
                 opponent_goal: Tuple[float, float]):
        """
        Args:
            client: Instance du client RSK
            own_goal: Position (x, y) de NOTRE but à défendre
            opponent_goal: Position (x, y) du but adverse
        """
        self.client = client
        self.own_goal = own_goal
        self.opponent_goal = opponent_goal
        
        # Création des agents défensifs
        self.defender_front = DefenseAgent(
            client.green1, own_goal, opponent_goal, 
            role="front", name="Green1-Front"
        )
        self.defender_back = DefenseAgent(
            client.green2, own_goal, opponent_goal, 
            role="back", name="Green2-Back"
        )
        
        # Gestionnaire d'arbitre
        self.referee = RefereeManager(client, team_color="green")
        
        # Statistiques
        self.total_clearances = 0
        self.total_interceptions = 0
    
    def update(self) -> bool:
        """
        Mise à jour principale (appelée à chaque frame)
        
        Returns:
            bool: True si un dégagement a été effectué, False sinon
        """
        # Vérifier si le jeu est en cours
        if not self.referee.is_game_running():
            return False
        
        # Création de l'état du jeu
        state = GameState.from_client(self.client, self.opponent_goal)
        
        # Vérification de validité
        if not state.is_valid():
            return False
        
        # Vérification des contrôles des robots
        can_control_r1 = self.referee.can_control_robot("1")
        can_control_r2 = self.referee.can_control_robot("2")
        
        if not can_control_r1 and not can_control_r2:
            return False
        
        # Vérifications d'urgence
        self._check_penalty_area_violations(state)
        self._check_referee_rules(state)
        
        # Mise à jour des deux défenseurs
        clearance_happened = False
        
        if can_control_r1:
            if self.defender_front.update_state(state.ball):
                self.total_clearances += 1
                clearance_happened = True
                if config.DEBUG_VERBOSE:
                    print(f"[Defense] Front a dégagé ! Total: {self.total_clearances}")
        
        if can_control_r2:
            if self.defender_back.update_state(state.ball):
                self.total_clearances += 1
                clearance_happened = True
                if config.DEBUG_VERBOSE:
                    print(f"[Defense] Back a dégagé ! Total: {self.total_clearances}")
        
        return clearance_happened
    
    def _check_penalty_area_violations(self, state: GameState):
        """
        Vérifie si un robot est dans la zone interdite et le fait sortir
        
        Args:
            state: État actuel du jeu
        """
        # Vérifier robot 1 (Front)
        if FieldUtils.is_in_penalty_area(state.robot1_pos, self.own_goal[0]):
            safe_pos = FieldUtils.get_safe_position_outside_penalty(
                state.robot1_pos, self.own_goal[0]
            )
            angle = FieldUtils.angle(state.robot1_pos, safe_pos)
            
            print(f"\n⚠️  [Green1-Front] SORTIE D'URGENCE de la zone interdite!")
            print(f"   Position: ({state.robot1_pos[0]:.3f}, {state.robot1_pos[1]:.3f})")
            print(f"   → Sûre: ({safe_pos[0]:.3f}, {safe_pos[1]:.3f})")
            
            self.client.green1.goto((safe_pos[0], safe_pos[1], angle), wait=False)
            self.defender_front.reset()
        
        # Vérifier robot 2 (Back)
        if FieldUtils.is_in_penalty_area(state.robot2_pos, self.own_goal[0]):
            safe_pos = FieldUtils.get_safe_position_outside_penalty(
                state.robot2_pos, self.own_goal[0]
            )
            angle = FieldUtils.angle(state.robot2_pos, safe_pos)
            
            print(f"\n⚠️  [Green2-Back] SORTIE D'URGENCE de la zone interdite!")
            print(f"   Position: ({state.robot2_pos[0]:.3f}, {state.robot2_pos[1]:.3f})")
            print(f"   → Sûre: ({safe_pos[0]:.3f}, {safe_pos[1]:.3f})")
            
            self.client.green2.goto((safe_pos[0], safe_pos[1], angle), wait=False)
            self.defender_back.reset()
    
    def _check_referee_rules(self, state: GameState):
        """
        Vérifie les règles de l'arbitre et fait reculer les robots si nécessaire
        
        Args:
            state: État actuel du jeu
        """
        # Notre but (opposé au but adverse)
        our_goal_x = self.own_goal[0]
        
        # Vérification Robot 1
        if self.referee.can_control_robot("1"):
            # Abus de balle
            if self.referee.check_ball_abuse("1", state.robot1_pos, state.ball):
                if self.referee.should_retreat_from_ball("1", state.robot1_pos, state.ball):
                    retreat_pos = self.referee.get_retreat_position(
                        state.robot1_pos, state.ball
                    )
                    current_angle = state.robot1_theta
                    
                    print(f"[Referee] Robot 1 recule pour éviter abus de balle")
                    try:
                        self.client.green1.goto(
                            (retreat_pos[0], retreat_pos[1], current_angle), 
                            wait=False
                        )
                    except:
                        pass
                    self.defender_front.reset()
            
            # Zone de défense (vérifier qu'on ne rentre pas dans NOTRE zone)
            # Note : En défense, on défend notre propre zone, donc c'est normal d'être proche
            # On vérifie juste qu'on n'entre pas dedans
            pass
        
        # Vérification Robot 2
        if self.referee.can_control_robot("2"):
            # Abus de balle
            if self.referee.check_ball_abuse("2", state.robot2_pos, state.ball):
                if self.referee.should_retreat_from_ball("2", state.robot2_pos, state.ball):
                    retreat_pos = self.referee.get_retreat_position(
                        state.robot2_pos, state.ball
                    )
                    current_angle = state.robot2_theta
                    
                    print(f"[Referee] Robot 2 recule pour éviter abus de balle")
                    try:
                        self.client.green2.goto(
                            (retreat_pos[0], retreat_pos[1], current_angle), 
                            wait=False
                        )
                    except:
                        pass
                    self.defender_back.reset()
    
    def print_stats(self):
        """Affiche les statistiques de défense"""
        print(f"\n{'='*50}")
        print(f"🛡️  STATISTIQUES DÉFENSIVES")
        print(f"{'='*50}")
        print(f"🥾 Dégagements   : {self.total_clearances}")
        print(f"🚫 Interceptions : {self.total_interceptions}")
        print(f"{'='*50}\n")
    
    def switch_roles(self):
        """
        Inverse les rôles des deux défenseurs
        Utile pour s'adapter dynamiquement
        """
        old_front_role = self.defender_front.role
        old_back_role = self.defender_back.role
        
        self.defender_front.set_role(old_back_role)
        self.defender_back.set_role(old_front_role)
        
        if config.DEBUG_VERBOSE:
            print(f"[Defense] Rôles inversés : Front ↔ Back")
    
    def set_aggressiveness(self, level: str):
        """
        Ajuste l'agressivité de la défense
        
        Args:
            level: "passive" (0.30m), "normal" (0.20m), "aggressive" (0.15m)
        """
        thresholds = {
            "passive": 0.30,
            "normal": 0.20,
            "aggressive": 0.15
        }
        
        threshold = thresholds.get(level, 0.20)
        
        self.defender_front.set_attack_threshold(threshold)
        self.defender_back.set_attack_threshold(threshold)
        
        if config.DEBUG_VERBOSE:
            print(f"[Defense] Agressivité défensive : {level} ({threshold}m)")
