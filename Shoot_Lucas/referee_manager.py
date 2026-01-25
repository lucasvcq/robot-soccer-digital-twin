"""
Gestion de l'arbitre et prévention des fautes
Analyse les règles et anticipe les actions de l'arbitre
"""
import time
from field_utils import FieldUtils
import config

class RefereeManager:
    """
    Gestionnaire de l'arbitre
    Surveille l'état de l'arbitre et prévient les fautes
    """
    
    def __init__(self, client, team_color="green"):
        """
        Args:
            client: Instance du client RSK
            team_color: "green" ou "blue"
        """
        self.client = client
        self.team_color = team_color
        self.last_ball_contact_time = {}  # robot_id -> temps du dernier contact
        self.ball_contact_start = {}  # robot_id -> début du contact continu
        
    def can_control_robot(self, robot_id):
        """
        Vérifie si on peut contrôler un robot
        
        Args:
            robot_id: "1" ou "2"
            
        Returns:
            bool: True si on peut contrôler le robot
        """
        try:
            referee = self.client.referee
            robot_info = referee["teams"][self.team_color]["robots"][robot_id]
            
            # Le robot est préempté si preempted = True
            if robot_info.get("preempted", False):
                reasons = robot_info.get("preemption_reasons", [])
                print(f"[Referee] Robot {robot_id} préempté: {', '.join(reasons)}")
                return False
            
            # Le robot est pénalisé
            if robot_info.get("penalized", False):
                reason = robot_info.get("penalized_reason", "unknown")
                remaining = robot_info.get("penalized_remaining", 0)
                print(f"[Referee] Robot {robot_id} pénalisé ({reason}): {remaining}s restantes")
                return False
            
            return True
            
        except (KeyError, TypeError) as e:
            # Si on ne peut pas accéder aux infos de l'arbitre, on assume qu'on peut contrôler
            return True
    
    def is_game_running(self):
        """
        Vérifie si le jeu est en cours
        
        Returns:
            bool: True si le jeu tourne
        """
        try:
            referee = self.client.referee
            return referee.get("game_is_running", False) and not referee.get("game_paused", True)
        except (KeyError, TypeError):
            return True
    
    def check_ball_abuse(self, robot_id, robot_pos, ball_pos):
        """
        Vérifie si le robot abuse de la balle (reste trop longtemps près d'elle)
        Règle: Plus de 3s dans un rayon de 25cm = pénalité 5s
        
        Args:
            robot_id: "1" ou "2"
            robot_pos: Position (x, y) du robot
            ball_pos: Position (x, y) de la balle
            
        Returns:
            bool: True si risque d'abus de balle
        """
        # Vérification de validité des positions
        if robot_pos is None or ball_pos is None:
            return False
        
        ABUSE_RADIUS = 0.25  # 25cm
        ABUSE_TIME = 3.0     # 3 secondes
        
        dist_to_ball = FieldUtils.dist(robot_pos, ball_pos)
        current_time = time.time()
        
        if dist_to_ball <= ABUSE_RADIUS:
            # Le robot est proche de la balle
            if robot_id not in self.ball_contact_start:
                # Début du contact
                self.ball_contact_start[robot_id] = current_time
                self.last_ball_contact_time[robot_id] = current_time
            else:
                # Contact continu
                elapsed = current_time - self.ball_contact_start[robot_id]
                
                # Avertissement à 2.5s
                if elapsed > 2.5 and elapsed < ABUSE_TIME:
                    if config.DEBUG_VERBOSE:
                        print(f"[Referee] ⚠️  Robot {robot_id} proche de la balle depuis {elapsed:.1f}s")
                    return True
                
                # Dépassement
                if elapsed >= ABUSE_TIME:
                    print(f"[Referee] 🚨 Robot {robot_id} ABUS DE BALLE ! {elapsed:.1f}s")
                    return True
        else:
            # Le robot s'est éloigné de la balle
            if robot_id in self.ball_contact_start:
                del self.ball_contact_start[robot_id]
        
        return False
    
    def check_defending_area_abuse(self, robot_pos, goal_x):
        """
        Vérifie si le robot est dans sa propre zone de défense
        Règle: Plus d'un robot de la même équipe dans la zone = pénalité
        
        IMPORTANT: On ne peut pas vérifier les autres robots facilement,
        donc on évite simplement d'y aller
        
        Args:
            robot_pos: Position (x, y) du robot
            goal_x: Position X de NOTRE but (pas le but adverse)
            
        Returns:
            bool: True si le robot est dans SA zone de défense
        """
        # Notre zone de défense est celle de NOTRE but
        # Si on attaque vers la gauche (goal_x < 0), notre zone est à droite (X > 0)
        # Si on attaque vers la droite (goal_x > 0), notre zone est à gauche (X < 0)
        
        our_goal_x = -goal_x  # Notre but est à l'opposé du but adverse
        
        return FieldUtils.is_in_penalty_area(robot_pos, our_goal_x)
    
    def check_attacking_area_abuse(self, robot_pos, goal_x):
        """
        Vérifie si le robot est dans la zone de défense adverse (faute)
        Règle: Entrer dans la zone adverse = pénalité 5s
        
        Args:
            robot_pos: Position (x, y) du robot
            goal_x: Position X du but adverse
            
        Returns:
            bool: True si le robot est dans la zone adverse (FAUTE)
        """
        return FieldUtils.is_in_penalty_area(robot_pos, goal_x)
    
    def should_retreat_from_ball(self, robot_id, robot_pos, ball_pos):
        """
        Détermine si le robot devrait s'éloigner de la balle
        pour éviter l'abus de balle
        AMÉLIORATION : Recule à 2.5s (au lieu de 2.7s) pour plus de marge
        
        Args:
            robot_id: "1" ou "2"
            robot_pos: Position du robot
            ball_pos: Position de la balle
            
        Returns:
            bool: True si le robot devrait reculer
        """
        if robot_id in self.ball_contact_start:
            elapsed = time.time() - self.ball_contact_start[robot_id]
            # S'éloigner à 2.5s (au lieu de 2.7s) pour plus de temps de réaction
            return elapsed > 2.5
        return False
    
    def get_retreat_position(self, robot_pos, ball_pos):
        """
        Calcule une position de recul pour éviter l'abus de balle
        AMÉLIORATION : Recule à 35cm (au lieu de 30cm) pour plus de sécurité
        
        Args:
            robot_pos: Position actuelle du robot
            ball_pos: Position de la balle
            
        Returns:
            Tuple (x, y): Position de recul (> 35cm de la balle)
        """
        # S'éloigner de 35cm de la balle (bien au-dessus des 25cm requis)
        RETREAT_DISTANCE = 0.35  # 35cm au lieu de 30cm
        
        direction = FieldUtils.unit_vector(ball_pos, robot_pos)
        retreat = (
            ball_pos[0] + direction[0] * RETREAT_DISTANCE,
            ball_pos[1] + direction[1] * RETREAT_DISTANCE
        )
        return FieldUtils.clamp(retreat)
    
    def print_status(self):
        """Affiche l'état actuel de l'arbitre (debug)"""
        try:
            referee = self.client.referee
            print("\n" + "="*60)
            print("📋 ÉTAT DE L'ARBITRE")
            print("="*60)
            print(f"Jeu en cours: {referee.get('game_is_running', '?')}")
            print(f"Jeu en pause: {referee.get('game_paused', '?')}")
            print(f"Mi-temps: {referee.get('halftime_is_running', '?')}")
            
            for robot_id in ["1", "2"]:
                robot_info = referee["teams"][self.team_color]["robots"][robot_id]
                print(f"\nRobot {robot_id}:")
                print(f"  Préempté: {robot_info.get('preempted', '?')}")
                print(f"  Pénalisé: {robot_info.get('penalized', '?')}")
                if robot_info.get('penalized'):
                    print(f"  Raison: {robot_info.get('penalized_reason', '?')}")
                    print(f"  Temps restant: {robot_info.get('penalized_remaining', '?')}s")
            
            print("="*60 + "\n")
        except Exception as e:
            print(f"[Referee] Impossible d'afficher le statut: {e}")