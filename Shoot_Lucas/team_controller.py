"""
Contrôleur d'équipe
Orchestre les deux robots et coordonne leurs actions
"""
import time
from typing import Tuple
from field_utils import FieldUtils
from game_state import GameState
from decision import DecisionEngine, Action
from robot_agent import RobotAgent
import config

class TeamController:
    """
    Contrôleur principal pour l'équipe de robots
    Gère la coordination entre les deux robots
    """
    
    def __init__(self, client, goal: Tuple[float, float]):
        """
        Args:
            client: Instance du client RSK
            goal: Position (x, y) du but adverse
        """
        self.client = client
        self.goal = goal
        
        # Création des agents
        self.agent1 = RobotAgent(client.green1, goal, "Green1")
        self.agent2 = RobotAgent(client.green2, goal, "Green2")
        
        # Moteur de décision
        self.engine = DecisionEngine(goal)
        
        # Statistiques
        self.total_shots = 0
        self.total_passes = 0
    
    def update(self) -> bool:
        """
        Mise à jour principale (appelée à chaque frame)
        
        Returns:
            bool: True si un tir a été effectué, False sinon
        """
        # 1. Création de l'état du jeu
        state = GameState.from_client(self.client, self.goal)
        
        # Vérification de validité
        if not state.is_valid():
            return False
        
        # 2. Identification des rôles
        attacker_id = state.closest_robot
        receiver_id = 2 if attacker_id == 1 else 1
        
        attacker = self.agent1 if attacker_id == 1 else self.agent2
        receiver = self.agent2 if attacker_id == 1 else self.agent1
        
        # 3. Décision tactique
        action = self.engine.decide(state, attacker_id)
        
        # 4. Exécution de l'action
        kick_happened = False
        
        if action == Action.PASS:
            kick_happened = self._execute_pass(state, attacker, receiver)
            if kick_happened:
                self.total_passes += 1
        
        elif action == Action.SHOOT:
            kick_happened = self._execute_shoot(state, attacker, receiver)
            if kick_happened:
                self.total_shots += 1
        
        return kick_happened
    
    def _execute_pass(self, state: GameState, attacker: RobotAgent, 
                      receiver: RobotAgent) -> bool:
        """
        Exécute une passe
        
        Args:
            state: État du jeu
            attacker: Agent attaquant
            receiver: Agent receveur
            
        Returns:
            bool: True si un kick a été effectué
        """
        # Calcul du point de passe
        pass_target = self.engine.compute_pass_target(receiver.robot.position)
        
        # Configuration de l'attaquant
        attacker.set_target(pass_target)
        attacker.set_kick_power(config.POWER_PASS)
        
        # Positionnement du receveur
        angle_to_ball = FieldUtils.angle(receiver.robot.position, state.ball)
        receiver.goto_position(pass_target, angle_to_ball)
        receiver.reset_navigation()  # Important : reset pour éviter les conflits
        
        # Mise à jour de l'attaquant
        return attacker.update_state(state.ball)
    
    def _execute_shoot(self, state: GameState, attacker: RobotAgent, 
                       receiver: RobotAgent) -> bool:
        """
        Exécute un tir au but
        
        Args:
            state: État du jeu
            attacker: Agent attaquant
            receiver: Agent receveur
            
        Returns:
            bool: True si un kick a été effectué
        """
        # Configuration de l'attaquant
        attacker.set_target(self.goal)
        attacker.set_kick_power(config.POWER_SHOOT)
        
        # Positionnement du receveur en soutien
        self._position_receiver_support(state, receiver)
        
        # Mise à jour de l'attaquant
        return attacker.update_state(state.ball)
    
    def _position_receiver_support(self, state: GameState, receiver: RobotAgent):
        """
        Positionne le receveur en position de soutien tactique
        
        Args:
            state: État du jeu
            receiver: Agent receveur
        """
        # Option 1 : Le receveur regarde la balle (attente)
        angle_to_ball = FieldUtils.angle(receiver.robot.position, state.ball)
        receiver.goto_position(receiver.robot.position, angle_to_ball)
        
        # Option 2 : Le receveur se positionne activement en soutien
        # (Décommentez pour activer)
        # support_pos = self.engine.compute_support_position(
        #     attacker.robot.position, state.ball
        # )
        # angle_to_ball = FieldUtils.angle(support_pos, state.ball)
        # receiver.goto_position(support_pos, angle_to_ball)
    
    def print_stats(self):
        """Affiche les statistiques du match"""
        print(f"\n{'='*50}")
        print(f"📊 STATISTIQUES")
        print(f"{'='*50}")
        print(f"🎯 Tirs au but : {self.total_shots}")
        print(f"🤝 Passes      : {self.total_passes}")
        print(f"{'='*50}\n")