"""
État centralisé du jeu
Centralise toutes les informations sur les robots, la balle et le terrain
pour éviter les calculs redondants
"""
from dataclasses import dataclass
from typing import Tuple, Optional
from field_utils import FieldUtils

@dataclass
class GameState:
    """
    État complet du jeu à un instant donné
    Calculé une seule fois par boucle, réutilisé partout
    """
    
    # Positions brutes
    ball: Tuple[float, float]
    robot1_pos: Tuple[float, float]
    robot2_pos: Tuple[float, float]
    robot1_theta: float
    robot2_theta: float
    goal: Tuple[float, float]
    
    # Cache des calculs (calculés une seule fois)
    _dist_r1_ball: Optional[float] = None
    _dist_r2_ball: Optional[float] = None
    _dist_r1_goal: Optional[float] = None
    _dist_r2_goal: Optional[float] = None
    _closest_robot: Optional[int] = None
    
    @property
    def dist_r1_ball(self) -> float:
        """Distance entre robot 1 et la balle (cachée)"""
        if self._dist_r1_ball is None:
            self._dist_r1_ball = FieldUtils.dist(self.robot1_pos, self.ball)
        return self._dist_r1_ball
    
    @property
    def dist_r2_ball(self) -> float:
        """Distance entre robot 2 et la balle (cachée)"""
        if self._dist_r2_ball is None:
            self._dist_r2_ball = FieldUtils.dist(self.robot2_pos, self.ball)
        return self._dist_r2_ball
    
    @property
    def dist_r1_goal(self) -> float:
        """Distance entre robot 1 et le but (cachée)"""
        if self._dist_r1_goal is None:
            self._dist_r1_goal = FieldUtils.dist(self.robot1_pos, self.goal)
        return self._dist_r1_goal
    
    @property
    def dist_r2_goal(self) -> float:
        """Distance entre robot 2 et le but (cachée)"""
        if self._dist_r2_goal is None:
            self._dist_r2_goal = FieldUtils.dist(self.robot2_pos, self.goal)
        return self._dist_r2_goal
    
    @property
    def closest_robot(self) -> int:
        """
        Retourne l'ID du robot le plus proche de la balle (1 ou 2)
        Résultat caché pour éviter les recalculs
        """
        if self._closest_robot is None:
            self._closest_robot = 1 if self.dist_r1_ball < self.dist_r2_ball else 2
        return self._closest_robot
    
    def get_robot_pos(self, robot_id: int) -> Tuple[float, float]:
        """
        Retourne la position du robot demandé
        
        Args:
            robot_id: 1 ou 2
            
        Returns:
            Tuple (x, y): Position du robot
        """
        return self.robot1_pos if robot_id == 1 else self.robot2_pos
    
    def get_robot_theta(self, robot_id: int) -> float:
        """
        Retourne l'orientation du robot demandé
        
        Args:
            robot_id: 1 ou 2
            
        Returns:
            float: Orientation en radians
        """
        return self.robot1_theta if robot_id == 1 else self.robot2_theta
    
    def get_dist_to_ball(self, robot_id: int) -> float:
        """
        Retourne la distance du robot à la balle
        
        Args:
            robot_id: 1 ou 2
            
        Returns:
            float: Distance en mètres
        """
        return self.dist_r1_ball if robot_id == 1 else self.dist_r2_ball
    
    def get_dist_to_goal(self, robot_id: int) -> float:
        """
        Retourne la distance du robot au but
        
        Args:
            robot_id: 1 ou 2
            
        Returns:
            float: Distance en mètres
        """
        return self.dist_r1_goal if robot_id == 1 else self.dist_r2_goal
    
    @classmethod
    def from_client(cls, client, goal: Tuple[float, float]):
        """
        Factory method pour créer un GameState depuis le client RSK
        
        Args:
            client: Instance du client RSK
            goal: Position (x, y) du but adverse
            
        Returns:
            GameState: Nouvel état du jeu
        """
        return cls(
            ball=client.ball,
            robot1_pos=client.green1.position,
            robot2_pos=client.green2.position,
            robot1_theta=client.green1.orientation,
            robot2_theta=client.green2.orientation,
            goal=goal
        )
    
    def is_valid(self) -> bool:
        """
        Vérifie si l'état est valide (pas de None)
        
        Returns:
            bool: True si toutes les données sont présentes
        """
        return all([
            self.ball is not None,
            self.robot1_pos is not None,
            self.robot2_pos is not None,
            self.robot1_theta is not None,
            self.robot2_theta is not None
        ])