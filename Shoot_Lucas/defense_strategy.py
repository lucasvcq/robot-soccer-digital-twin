"""
Stratégie défensive
Calcule les positions défensives optimales pour protéger le but
"""
import math
from typing import Tuple
from field_utils import FieldUtils
import config

class DefenseStrategy:
    """
    Stratégie de positionnement défensif
    Calcule les positions pour intercepter la balle et protéger le but
    """
    
    # Dimensions du robot et du but pour calculs géométriques
    ROBOT_SIZE = 0.08  # 8cm de diamètre
    GOAL_WIDTH = 0.60  # 60cm de largeur du but
    
    @staticmethod
    def compute_defensive_position(ball: Tuple[float, float],
                                   own_goal: Tuple[float, float],
                                   role: str = "front",
                                   margin: float = 0.30) -> Tuple[float, float]:
        """
        Calcule la position défensive optimale entre la balle et le but
        Correspond à la fonction position_defense() de l'ancien REMI.py
        
        Stratégie :
        - Se positionner sur la ligne balle-but
        - Distance adaptée selon le rôle (front/back)
        - Front : plus agressif (marge plus petite), plus loin du but
        - Back : plus prudent (marge plus grande), plus proche du but
        
        ZONES INTERDITES :
        - Notre zone défensive : AUTORISÉE (règle 5 - max 1 robot)
        - Zone adverse : INTERDITE (règle 6 - pénalité 5s)
        
        Args:
            ball: Position (x, y) de la balle
            own_goal: Position (x, y) de NOTRE but à défendre
            role: "front" (défenseur avancé) ou "back" (défenseur reculé)
            margin: Distance par rapport au but (défaut: 0.30m pour front, 0.20 pour back)
            
        Returns:
            Tuple (x, y): Position défensive
        """
        # Distance balle-but
        dist_ball_goal = FieldUtils.dist(ball, own_goal)
        
        # Calcul de la distance de sécurité basée sur la géométrie
        # (même formule que l'ancien code : taille_robot * dist / taille_but)
        safety_distance = DefenseStrategy._compute_safety_distance(dist_ball_goal)
        
        # Calcul du point intermédiaire sur la ligne balle-but
        # (équivalent à point_intermediaire() de l'ancien code)
        if dist_ball_goal < 0.01:
            # Balle sur le but, position par défaut
            defensive_pos = (
                own_goal[0] + 0.30 if own_goal[0] < 0 else own_goal[0] - 0.30,
                own_goal[1]
            )
        else:
            # Vecteur unitaire but → balle
            direction = FieldUtils.unit_vector(own_goal, ball)
            
            # Position = but + direction * (safety_distance + margin)
            defensive_pos = (
                own_goal[0] + direction[0] * (safety_distance + margin),
                own_goal[1] + direction[1] * (safety_distance + margin)
            )
        
        # Clamp aux limites du terrain (mais PAS de vérification de notre zone défensive)
        # On peut entrer dans NOTRE zone (règle 5), seule la zone ADVERSE est interdite
        defensive_pos = FieldUtils.clamp(defensive_pos, margin=0.02)
        
        return defensive_pos
    
    @staticmethod
    def _compute_safety_distance(ball_goal_distance: float) -> float:
        """
        Calcule la distance de sécurité basée sur la géométrie du jeu
        
        Utilise la relation : robot_size / goal_width = safety_dist / ball_goal_dist
        Plus la balle est proche, plus on doit être proche pour couvrir l'angle
        
        Args:
            ball_goal_distance: Distance entre la balle et le but
            
        Returns:
            float: Distance de sécurité recommandée
        """
        if ball_goal_distance < 0.01:
            return 0.15  # Minimum si balle très proche
        
        # Calcul géométrique
        safety = (DefenseStrategy.ROBOT_SIZE * ball_goal_distance) / DefenseStrategy.GOAL_WIDTH
        
        # Limiter entre 0.15m et 0.50m
        return max(0.15, min(0.50, safety))
    
    @staticmethod
    def _apply_minimum_margin(position: Tuple[float, float],
                             goal: Tuple[float, float],
                             margin: float) -> Tuple[float, float]:
        """
        S'assure que la position est à une distance minimum du but
        
        Args:
            position: Position candidate
            goal: Position du but
            margin: Marge minimale (m)
            
        Returns:
            Tuple (x, y): Position corrigée
        """
        dist_to_goal = FieldUtils.dist(position, goal)
        
        if dist_to_goal < margin:
            # Trop proche, reculer sur la ligne position-but
            direction = FieldUtils.unit_vector(goal, position)
            position = (
                goal[0] + direction[0] * margin,
                goal[1] + direction[1] * margin
            )
        
        return position
    
    @staticmethod
    def should_attack_ball(robot_pos: Tuple[float, float],
                          ball: Tuple[float, float],
                          own_goal: Tuple[float, float],
                          role: str,
                          attack_threshold: float = 0.50,
                          side_threshold: float = 0.50) -> bool:
        """
        Détermine si le défenseur devrait attaquer la balle
        
        Critères d'attaque :
        - Balle dans notre moitié de terrain
        - Balle proche (< attack_threshold)
        - Pour "front" : aussi si balle sur le côté
        
        Args:
            robot_pos: Position du robot
            ball: Position de la balle
            own_goal: Position de notre but
            role: "front" ou "back"
            attack_threshold: Distance max pour attaquer (défaut: 0.50m)
            side_threshold: Seuil X pour "front" (défaut: 0.50m)
            
        Returns:
            bool: True si le robot devrait attaquer la balle
        """
        dist_to_ball = FieldUtils.dist(robot_pos, ball)
        
        # La balle doit être relativement proche
        if dist_to_ball > attack_threshold:
            return False
        
        # Déterminer si la balle est dans notre moitié
        goal_sign = 1 if own_goal[0] > 0 else -1
        ball_in_our_half = (ball[0] * goal_sign) > 0
        
        if role == "front":
            # Défenseur avancé : attaque si proche OU si dans une zone dangereuse
            dangerous_zone = abs(ball[0]) < side_threshold and abs(ball[1]) < 0.45
            return ball_in_our_half or dangerous_zone
        
        else:  # "back"
            # Défenseur reculé : attaque seulement si vraiment dans notre zone
            in_critical_zone = (
                ball_in_our_half and 
                abs(ball[1]) < 0.45  # Dans l'axe du but
            )
            return in_critical_zone
    
    @staticmethod
    def compute_intercept_point(ball: Tuple[float, float],
                               own_goal: Tuple[float, float],
                               offset: float = 0.15) -> Tuple[float, float]:
        """
        Calcule le point d'interception derrière la balle
        pour préparer une frappe de dégagement
        GARANTIT que le point est hors de la zone interdite
        
        Args:
            ball: Position de la balle
            own_goal: Notre but
            offset: Distance derrière la balle (défaut: 0.15m)
            
        Returns:
            Tuple (x, y): Point d'interception (garanti hors zone)
        """
        # Vecteur du but vers la balle (direction de dégagement)
        direction = FieldUtils.unit_vector(own_goal, ball)
        
        # Point derrière la balle dans cette direction
        intercept = (
            ball[0] + direction[0] * offset,
            ball[1] + direction[1] * offset
        )
        
        # Vérifier et corriger si dans la zone interdite
        intercept = FieldUtils.safe_clamp(intercept, own_goal[0], margin=0.05)
        
        return intercept
    
    @staticmethod
    def compute_clearance_target(ball: Tuple[float, float],
                                own_goal: Tuple[float, float],
                                opponent_goal: Tuple[float, float]) -> Tuple[float, float]:
        """
        Calcule la cible optimale pour un dégagement défensif
        
        Stratégie :
        - Si balle sur les côtés : dégager vers le centre adverse
        - Si balle au centre : dégager vers les côtés adverses
        
        Args:
            ball: Position de la balle
            own_goal: Notre but
            opponent_goal: But adverse
            
        Returns:
            Tuple (x, y): Point cible pour le dégagement
        """
        # Déterminer si la balle est sur les côtés
        is_on_side = abs(ball[1]) > 0.30
        
        if is_on_side:
            # Dégager vers le centre adverse
            target = (opponent_goal[0], 0.0)
        else:
            # Dégager vers le côté adverse (côté opposé à la balle)
            side_y = -0.40 if ball[1] >= 0 else 0.40
            target = (opponent_goal[0] * 0.7, side_y)
        
        return target
    
    @staticmethod
    def compute_goalkeeper_position(ball: Tuple[float, float],
                                   own_goal: Tuple[float, float],
                                   max_distance: float = 0.25) -> Tuple[float, float]:
        """
        Calcule la position optimale pour un gardien de but
        GARANTIT que la position est hors de la zone interdite
        
        Le gardien reste proche du but et se déplace latéralement
        pour bloquer la ligne balle-but
        
        Args:
            ball: Position de la balle
            own_goal: Position de notre but
            max_distance: Distance maximale du but (défaut: 0.25m)
            
        Returns:
            Tuple (x, y): Position du gardien (garantie hors zone)
        """
        # Direction de la balle vers le but
        ball_to_goal = FieldUtils.unit_vector(ball, own_goal)
        
        # Position légèrement devant le but
        goalkeeper_pos = (
            own_goal[0] - ball_to_goal[0] * max_distance,
            own_goal[1] - ball_to_goal[1] * max_distance * 0.5  # Moins de mouvement en Y
        )
        
        # Limiter le mouvement latéral pour rester devant le but
        goalkeeper_pos = (
            goalkeeper_pos[0],
            max(-0.25, min(0.25, goalkeeper_pos[1]))  # Rester dans ±25cm en Y
        )
        
        # CRITIQUE : Vérifier la zone interdite
        goalkeeper_pos = FieldUtils.safe_clamp(goalkeeper_pos, own_goal[0], margin=0.05)
        
        return goalkeeper_pos
