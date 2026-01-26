"""
🛡️ DEFENSE COMPATIBLE - Reproduction exacte de votre ancien code
avec les règles des zones CORRIGÉES

RÈGLES :
✅ Notre zone défensive : AUTORISÉE (règle 5 - max 1 robot)
❌ Zone adverse : INTERDITE (règle 6 - pénalité 5s)
⏱️  Abus de balle : Max 3s à 25cm (règle 7)

COMPORTEMENT : Identique à REMI.defense_passive()
"""
import time
import rsk
from typing import Tuple
from math import atan2, pi, sqrt, cos, sin
from field_utils import FieldUtils
from referee_manager import RefereeManager
import config

class DefenseCompatible:
    """Classe compatible avec l'ancien REMI.py"""
    
    def __init__(self, client):
        self.client = client
        self.referee = RefereeManager(client, team_color="green")
    
    def vecteur_robot(self, robot, objectif: Tuple[float, float]) -> Tuple[float, float]:
        """Vecteur vers l'objectif dans le repère du robot (normalisé)"""
        vx_terrain = objectif[0] - robot.position[0]
        vy_terrain = objectif[1] - robot.position[1]
        
        theta = robot.orientation
        vx = cos(theta) * vx_terrain + sin(theta) * vy_terrain
        vy = -sin(theta) * vx_terrain + cos(theta) * vy_terrain
        
        norme = sqrt(vx**2 + vy**2)
        return (vx / norme, vy / norme) if norme != 0 else (0.0, 0.0)
    
    def distance_securite(self, distance_ball_but: float) -> float:
        """Distance de sécurité basée sur la géométrie"""
        return (0.08 * distance_ball_but) / 0.6
    
    def position_defense(self, ball: Tuple[float, float], 
                        zone_defense: Tuple[float, float],
                        marge: float, role: str) -> Tuple[float, float]:
        """Calcule la position défensive sur la ligne balle-but"""
        x_ball, y_ball = ball
        x_defense, y_defense = zone_defense
        
        distance_ball_but = sqrt((x_defense - x_ball)**2 + (y_defense - y_ball)**2)
        
        if distance_ball_but < 0.01:
            return zone_defense
        
        distance = self.distance_securite(distance_ball_but)
        ratio = distance / distance_ball_but
        
        x = zone_defense[0] + (x_ball - zone_defense[0]) * ratio
        y = zone_defense[1] + (y_ball - zone_defense[1]) * ratio
        
        # Ajustement selon le rôle
        if role == "back":
            dx, dy = zone_defense[0] - x_ball, zone_defense[1] - y_ball
            norme = sqrt(dx**2 + dy**2)
            if norme != 0:
                x, y = x_ball + dx / norme * marge, y_ball + dy / norme * marge
        elif role == "front":
            dx, dy = x_ball - zone_defense[0], y_ball - zone_defense[1]
            norme = sqrt(dx**2 + dy**2)
            if norme != 0:
                x, y = zone_defense[0] + dx / norme * marge, zone_defense[1] + dy / norme * marge
        
        return FieldUtils.clamp((x, y), margin=0.02)
    
    def defense_passive(self, robot, ball: Tuple[float, float], 
                       zone_defense: Tuple[float, float],
                       erreur_placement: float, vitesse: float,
                       marge: float, seuil_ball: float, role: str):
        """Comportement défensif - Reproduction exacte de l'ancien code"""
        
        if ball is None:
            robot.control(0, 0, 0)
            return
        
        # RÈGLE 6 : Vérifier zone ADVERSE
        opponent_goal = (-zone_defense[0], 0.0)
        if FieldUtils.is_in_penalty_area(robot.position, opponent_goal[0]):
            safe_pos = FieldUtils.get_safe_position_outside_penalty(
                robot.position, opponent_goal[0]
            )
            angle = FieldUtils.angle(robot.position, safe_pos)
            try:
                robot.goto((safe_pos[0], safe_pos[1], angle), wait=False)
            except:
                pass
            return
        
        # Calculs
        delta_x, delta_y = ball[0] - zone_defense[0], ball[1] - zone_defense[1]
        theta = atan2(delta_y, delta_x)
        w = (theta - robot.orientation + pi) % (2 * pi) - pi
        
        x_def, y_def = self.position_defense(ball, zone_defense, marge, role)
        vx, vy = self.vecteur_robot(robot, (x_def, y_def))
        
        distance_to_def = FieldUtils.dist(robot.position, (x_def, y_def))
        distance_to_ball = FieldUtils.dist(robot.position, ball)
        
        # Décision d'attaque
        should_attack = False
        if role == "back":
            should_attack = abs(ball[1]) <= 0.45 and (ball[0] * zone_defense[0]) > 0
        elif role == "front":
            should_attack = (ball[0] * zone_defense[0]) > 0
        
        # Exécution
        if should_attack:
            if distance_to_ball <= seuil_ball:
                xs, ys = ball[0] - robot.position[0], ball[1] - robot.position[1]
                try:
                    robot.goto((ball[0], ball[1], atan2(ys, xs)), wait=False)
                    robot.kick(power=0.90)
                except:
                    pass
            else:
                vx_ball, vy_ball = self.vecteur_robot(robot, ball)
                robot.control(vx_ball * vitesse, vy_ball * vitesse, 0)
        else:
            if distance_to_def > erreur_placement:
                robot.control(vx * vitesse, vy * vitesse, 0)
            else:
                robot.control(0, 0, 4 * w)
    
    def can_move(self, team: str, robot_id: str) -> bool:
        """Vérifie si on peut contrôler un robot"""
        return self.referee.can_control_robot(robot_id)


def main():
    """Lance la défense avec configuration identique à l'ancien code"""
    print("="*60)
    print("🛡️  DÉFENSE COMPATIBLE (comportement identique)")
    print("="*60)
    
    with rsk.Client() as client:
        defense = DefenseCompatible(client)
        
        # CONFIGURATION IDENTIQUE À L'ANCIEN CODE
        vitesse = 4
        zone_defense = (1.84/2, 0)
        erreur_placement = 0.04
        marge_front = 0.3
        marge_back = 0.2
        seuil_ball = 0.2
        
        print(f"🎯 But : {zone_defense}")
        print(f"⚙️  vitesse={vitesse}, seuil={seuil_ball}\n")
        
        try:
            while True:
                if defense.can_move("green", "1"):
                    try:
                        defense.defense_passive(
                            client.green1, client.ball, zone_defense,
                            erreur_placement, vitesse, marge_front,
                            seuil_ball, "front"
                        )
                    except:
                        pass
                
                if defense.can_move("green", "2"):
                    try:
                        defense.defense_passive(
                            client.green2, client.ball, zone_defense,
                            erreur_placement, vitesse, marge_back,
                            seuil_ball, "back"
                        )
                    except:
                        pass
                
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\n⏹️  Arrêt")
        print("\n👋 Terminé\n")


if __name__ == "__main__":
    main()
