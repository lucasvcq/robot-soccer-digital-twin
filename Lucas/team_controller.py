"""
Contrôleur d'équipe - VERSION FLEXIBLE
Orchestre les deux robots et coordonne leurs actions
SUPPORT ÉQUIPES GREEN ET BLUE
"""
import time
from typing import Tuple
from field_utils import FieldUtils
from game_state import GameState
from decision import DecisionEngine, Action
from robot_agent import RobotAgent
from referee_manager import RefereeManager
import config

class TeamController:
    """
    Contrôleur principal pour l'équipe de robots
    Gère la coordination entre les deux robots
    VERSION FLEXIBLE : Supporte green ET blue
    """
    
    def __init__(self, client, goal: Tuple[float, float], team_color: str = "green"):
        """
        Args:
            client: Instance du client RSK
            goal: Position (x, y) du but adverse
            team_color: Couleur de l'équipe ("green" ou "blue")
        """
        self.client = client
        self.goal = goal
        self.team_color = team_color
        
        # Récupérer les robots selon la couleur
        if team_color == "green":
            self.robot1 = client.green1
            self.robot2 = client.green2
        else:  # blue
            self.robot1 = client.blue1
            self.robot2 = client.blue2
        
        # Création des agents
        self.agent1 = RobotAgent(self.robot1, goal, f"{team_color.capitalize()}1")
        self.agent2 = RobotAgent(self.robot2, goal, f"{team_color.capitalize()}2")
        
        # Moteur de décision
        self.engine = DecisionEngine(goal)
        
        # Gestionnaire d'arbitre
        self.referee = RefereeManager(client, team_color=team_color)
        
        # Statistiques
        self.total_shots = 0
        self.total_passes = 0
    
    def set_goal(self, new_goal: Tuple[float, float]):
        """
        Met à jour le but adverse (utile pour la mi-temps)
        
        Args:
            new_goal: Nouvelle position du but adverse
        """
        self.goal = new_goal
        self.agent1.set_target(new_goal)
        self.agent2.set_target(new_goal)
        self.engine.goal = new_goal
    
    def update(self) -> bool:
        """
        Mise à jour principale (appelée à chaque frame)
        
        Returns:
            bool: True si un tir a été effectué, False sinon
        """
        # Vérifier si le jeu tourne
        if not self.referee.is_game_running():
            return False
        
        # Création de l'état du jeu
        state = GameState.from_client(self.client, self.goal)
        
        # Vérification de validité
        if not state.is_valid():
            return False
        
        # Vérification des contrôles des robots
        can_control_r1 = self.referee.can_control_robot("1")
        can_control_r2 = self.referee.can_control_robot("2")
        
        if not can_control_r1 and not can_control_r2:
            return False
        
        # Vérification d'urgence des zones interdites
        self._check_penalty_area_violations(state)
        self._check_referee_rules(state)
        
        # Identification des rôles
        attacker_id = state.closest_robot
        receiver_id = 2 if attacker_id == 1 else 1
        
        # Si l'attaquant ne peut pas être contrôlé, inverser les rôles
        if (attacker_id == 1 and not can_control_r1) or (attacker_id == 2 and not can_control_r2):
            attacker_id, receiver_id = receiver_id, attacker_id
        
        attacker = self.agent1 if attacker_id == 1 else self.agent2
        receiver = self.agent2 if attacker_id == 1 else self.agent1
        
        # Décision tactique
        action = self.engine.decide(state, attacker_id)
        
        # Exécution de l'action
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
    
    def _check_referee_rules(self, state: GameState):
        """
        Vérifie les règles de l'arbitre et fait reculer les robots si nécessaire
        
        Args:
            state: État actuel du jeu
        """
        # Notre but (opposé au but adverse)
        our_goal_x = -self.goal[0]
        
        # Vérification Robot 1
        if self.referee.can_control_robot("1"):
            # Abus de balle
            if self.referee.check_ball_abuse("1", state.robot1_pos, state.ball):
                if self.referee.should_retreat_from_ball("1", state.robot1_pos, state.ball):
                    retreat_pos = self.referee.get_retreat_position(state.robot1_pos, state.ball)
                    current_angle = state.robot1_theta
                    
                    print(f"[Referee] Robot 1 recule pour éviter abus de balle (35cm)")
                    try:
                        self.robot1.goto((retreat_pos[0], retreat_pos[1], current_angle), wait=False)
                    except:
                        pass
                    self.agent1.reset_navigation()
            
            # Zone de défense (notre zone)
            if self.referee.check_defending_area_abuse(state.robot1_pos, our_goal_x):
                print(f"[Referee] ⚠️ Robot 1 dans SA zone de défense (risque pénalité)")
        
        # Vérification Robot 2
        if self.referee.can_control_robot("2"):
            # Abus de balle
            if self.referee.check_ball_abuse("2", state.robot2_pos, state.ball):
                if self.referee.should_retreat_from_ball("2", state.robot2_pos, state.ball):
                    retreat_pos = self.referee.get_retreat_position(state.robot2_pos, state.ball)
                    current_angle = state.robot2_theta
                    
                    print(f"[Referee] Robot 2 recule pour éviter abus de balle (35cm)")
                    try:
                        self.robot2.goto((retreat_pos[0], retreat_pos[1], current_angle), wait=False)
                    except:
                        pass
                    self.agent2.reset_navigation()
            
            # Zone de défense (notre zone)
            if self.referee.check_defending_area_abuse(state.robot2_pos, our_goal_x):
                print(f"[Referee] ⚠️ Robot 2 dans SA zone de défense (risque pénalité)")
    
    def _check_penalty_area_violations(self, state: GameState):
        """
        Vérifie si un robot est dans la zone interdite et le fait sortir immédiatement
        
        Args:
            state: État actuel du jeu
        """
        # Vérifier robot 1
        if FieldUtils.is_in_penalty_area(state.robot1_pos, self.goal[0]):
            safe_pos = FieldUtils.get_safe_position_outside_penalty(state.robot1_pos, self.goal[0])
            angle = FieldUtils.angle(state.robot1_pos, safe_pos)
            print(f"\n⚠️ [{self.team_color.capitalize()}1] SORTIE D'URGENCE de la zone interdite!")
            print(f"   Position actuelle: ({state.robot1_pos[0]:.3f}, {state.robot1_pos[1]:.3f})")
            print(f"   Position sûre: ({safe_pos[0]:.3f}, {safe_pos[1]:.3f})")
            self.robot1.goto((safe_pos[0], safe_pos[1], angle), wait=False)
            self.agent1.reset_navigation()
        
        # Vérifier robot 2
        if FieldUtils.is_in_penalty_area(state.robot2_pos, self.goal[0]):
            safe_pos = FieldUtils.get_safe_position_outside_penalty(state.robot2_pos, self.goal[0])
            angle = FieldUtils.angle(state.robot2_pos, safe_pos)
            print(f"\n⚠️ [{self.team_color.capitalize()}2] SORTIE D'URGENCE de la zone interdite!")
            print(f"   Position actuelle: ({state.robot2_pos[0]:.3f}, {state.robot2_pos[1]:.3f})")
            print(f"   Position sûre: ({safe_pos[0]:.3f}, {safe_pos[1]:.3f})")
            self.robot2.goto((safe_pos[0], safe_pos[1], angle), wait=False)
            self.agent2.reset_navigation()
    
    def _execute_pass(self, state: GameState, attacker: RobotAgent, 
                      receiver: RobotAgent) -> bool:
        """
        Exécute une passe avec puissance adaptée à la distance
        
        Args:
            state: État du jeu
            attacker: Agent attaquant
            receiver: Agent receveur
            
        Returns:
            bool: True si un kick a été effectué
        """
        # Calcul du point de passe (avec info de la balle pour décalage)
        pass_target = self.engine.compute_pass_target(
            receiver.robot.position, 
            state.ball
        )
        
        # Calcul de la puissance adaptée à la distance
        distance_to_receiver = FieldUtils.dist(attacker.robot.position, pass_target)
        pass_power = FieldUtils.compute_pass_power(distance_to_receiver)
        
        if config.DEBUG_VERBOSE:
            print(f"[Pass] Distance: {distance_to_receiver:.2f}m → Power: {pass_power:.2f}")
        
        # Configuration de l'attaquant
        attacker.set_target(pass_target)
        attacker.set_kick_power(pass_power)
        
        # Positionnement du receveur
        angle_to_ball = FieldUtils.angle(receiver.robot.position, state.ball)
        receiver.goto_position(pass_target, angle_to_ball)
        receiver.reset_navigation()
        
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
        print(f"📊 STATISTIQUES - {self.team_color.upper()}")
        print(f"{'='*50}")
        print(f"🎯 Tirs au but : {self.total_shots}")
        print(f"🤝 Passes      : {self.total_passes}")
        print(f"{'='*50}\n")