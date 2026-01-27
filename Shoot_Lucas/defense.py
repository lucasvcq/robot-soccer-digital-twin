"""
🛡️ DEFENSE CORRIGÉE - Version finale avec logique clarifiée

STRATÉGIE :
- Robot BACK (gardien) : Reste dans NOTRE zone défensive, suit la balle
- Robot FRONT : Se maintient à ~25cm de la balle (évite pénalité abus)
                 Si ne peut plus respecter 25cm → fonce et dégage

RÈGLES :
✅ Notre zone défensive : AUTORISÉE (règle 5 - max 1 robot)
❌ Zone adverse : INTERDITE (règle 6 - pénalité 5s)
⏱️  Abus de balle : Max 3s à moins de 25cm (règle 7)
"""
import time
import rsk
from typing import Tuple
from math import atan2, pi, sqrt, cos, sin
from field_utils import FieldUtils
from referee_manager import RefereeManager
import config

class Defense:
    """Défense corrigée selon vos spécifications exactes"""
    
    # Constantes importantes
    BALL_SAFE_DISTANCE = 0.25  # 25cm de la balle (règle 7)
    BALL_CLEARANCE_THRESHOLD = 0.28  # Si < 28cm et dans zone → dégager
    
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
    
    def goalkeeper_position(self, ball: Tuple[float, float], 
                           our_goal: Tuple[float, float]) -> Tuple[float, float]:
        """
        Calcule la position du gardien DANS notre zone défensive
        
        Le gardien doit :
        1. Rester DANS notre zone (pas juste à la limite)
        2. Se positionner sur la ligne balle-but
        3. Bouger latéralement pour bloquer
        """
        # Direction balle → but
        dx = our_goal[0] - ball[0]
        dy = our_goal[1] - ball[1]
        dist = sqrt(dx**2 + dy**2)
        
        if dist < 0.01:
            # Balle sur le but
            return our_goal
        
        # Vecteur unitaire
        ux, uy = dx / dist, dy / dist
        
        # Position : 20cm devant le but (DANS la zone de 30cm)
        keeper_x = our_goal[0] - ux * 0.20
        keeper_y = our_goal[1] - uy * 0.20
        
        # Limiter le mouvement latéral
        keeper_y = max(-0.35, min(0.35, keeper_y))
        
        return FieldUtils.clamp((keeper_x, keeper_y), margin=0.02)
    
    def front_defender_position(self, ball: Tuple[float, float],
                               our_goal: Tuple[float, float]) -> Tuple[float, float]:
        """
        Calcule la position du défenseur avant à ~25cm de la balle
        
        Le défenseur doit :
        1. Rester à environ 25cm de la balle (éviter abus)
        2. Se positionner entre la balle et notre but
        3. Ne JAMAIS entrer dans notre zone (laisse ça au gardien)
        """
        # Direction balle → but
        dx = our_goal[0] - ball[0]
        dy = our_goal[1] - ball[1]
        dist = sqrt(dx**2 + dy**2)
        
        if dist < 0.01:
            # Balle sur le but, se mettre sur le côté
            side_offset = 0.30
            return FieldUtils.clamp((ball[0], ball[1] + side_offset), margin=0.02)
        
        # Vecteur unitaire balle → but
        ux, uy = dx / dist, dy / dist
        
        # Position : 25cm derrière la balle (côté de notre but)
        front_x = ball[0] + ux * self.BALL_SAFE_DISTANCE
        front_y = ball[1] + uy * self.BALL_SAFE_DISTANCE
        
        # IMPORTANT : Ne pas entrer dans NOTRE zone défensive
        # Vérifier et corriger si trop proche de notre zone
        penalty_limit = config.PENALTY_AREA_DEPTH + 0.05  # Marge de sécurité
        
        if our_goal[0] < 0:  # Notre but à gauche
            if front_x < (FieldUtils.MIN_X + penalty_limit):
                front_x = FieldUtils.MIN_X + penalty_limit
        else:  # Notre but à droite
            if front_x > (FieldUtils.MAX_X - penalty_limit):
                front_x = FieldUtils.MAX_X - penalty_limit
        
        return FieldUtils.clamp((front_x, front_y), margin=0.02)
    
    def should_front_clear_ball(self, robot_pos: Tuple[float, float],
                               ball: Tuple[float, float],
                               our_goal: Tuple[float, float]) -> bool:
        """
        Détermine si le front doit foncer dégager la balle
        
        Critères :
        - La balle est proche de notre zone ET
        - Le front ne peut plus respecter les 25cm
        """
        dist_to_ball = FieldUtils.dist(robot_pos, ball)
        
        # Si déjà très proche de la balle (< 28cm) ET la balle est dangereuse
        if dist_to_ball < self.BALL_CLEARANCE_THRESHOLD:
            # Vérifier si la balle est dans une zone dangereuse
            dist_ball_goal = FieldUtils.dist(ball, our_goal)
            
            # Si balle à moins de 60cm de notre but → danger
            if dist_ball_goal < 0.60:
                return True
        
        return False
    
    def defense_back_goalkeeper(self, robot, ball: Tuple[float, float],
                               our_goal: Tuple[float, float],
                               vitesse: float = 4):
        """
        Comportement du GARDIEN (robot BACK)
        Reste dans notre zone, suit la balle
        """
        if ball is None:
            robot.control(0, 0, 0)
            return
        
        # RÈGLE 6 : Sortir si dans zone ADVERSE (normalement impossible pour gardien)
        opponent_goal = (-our_goal[0], 0.0)
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
        
        # Position cible du gardien (DANS notre zone)
        target_pos = self.goalkeeper_position(ball, our_goal)
        
        # Angle pour regarder la balle
        angle_to_ball = atan2(ball[1] - robot.position[1], 
                             ball[0] - robot.position[0])
        
        # Distance à la position cible
        dist_to_target = FieldUtils.dist(robot.position, target_pos)
        
        # Si loin de la position → se déplacer
        if dist_to_target > 0.05:
            vx, vy = self.vecteur_robot(robot, target_pos)
            robot.control(vx * vitesse, vy * vitesse, 0)
        else:
            # En position → juste s'orienter vers la balle
            theta_robot = robot.orientation
            w = (angle_to_ball - theta_robot + pi) % (2 * pi) - pi
            robot.control(0, 0, 4 * w)
    
    def defense_front_harasser(self, robot, ball: Tuple[float, float],
                              our_goal: Tuple[float, float],
                              vitesse: float = 4):
        """
        Comportement du DÉFENSEUR AVANT (robot FRONT)
        Suit la balle à ~25cm, dégage si nécessaire
        """
        if ball is None:
            robot.control(0, 0, 0)
            return
        
        # RÈGLE 6 : Sortir si dans zone ADVERSE
        opponent_goal = (-our_goal[0], 0.0)
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
        
        robot_pos = robot.position
        dist_to_ball = FieldUtils.dist(robot_pos, ball)
        
        # DÉCISION : Dégager ou suivre ?
        should_clear = self.should_front_clear_ball(robot_pos, ball, our_goal)
        
        if should_clear:
            # MODE DÉGAGEMENT : Foncer vers la balle et taper
            if dist_to_ball < 0.15:
                # Assez proche pour tirer
                angle_to_clear = atan2(
                    opponent_goal[1] - robot_pos[1],
                    opponent_goal[0] - robot_pos[0]
                )
                try:
                    robot.goto((ball[0], ball[1], angle_to_clear), wait=False)
                    robot.kick(power=0.95)
                    if config.DEBUG_VERBOSE:
                        print(f"[FRONT] 🥾 DÉGAGEMENT !")
                except:
                    pass
            else:
                # Foncer vers la balle
                vx, vy = self.vecteur_robot(robot, ball)
                robot.control(vx * vitesse * 1.2, vy * vitesse * 1.2, 0)  # Plus rapide
        else:
            # MODE SUIVI : Maintenir ~25cm de la balle
            target_pos = self.front_defender_position(ball, our_goal)
            
            # Angle pour regarder la balle
            angle_to_ball = atan2(ball[1] - robot_pos[1], 
                                 ball[0] - robot_pos[0])
            
            # Distance à la position cible
            dist_to_target = FieldUtils.dist(robot_pos, target_pos)
            
            # Contrôle de distance par rapport à la balle
            if dist_to_ball < 0.23:
                # TROP PROCHE ! Reculer légèrement
                # Direction : s'éloigner de la balle
                away_x = robot_pos[0] - ball[0]
                away_y = robot_pos[1] - ball[1]
                away_dist = sqrt(away_x**2 + away_y**2)
                if away_dist > 0:
                    away_x /= away_dist
                    away_y /= away_dist
                    vx, vy = self.vecteur_robot(robot, (robot_pos[0] + away_x * 0.1, 
                                                         robot_pos[1] + away_y * 0.1))
                    robot.control(vx * vitesse * 0.5, vy * vitesse * 0.5, 0)
                else:
                    robot.control(0, 0, 0)
            
            elif dist_to_ball > 0.27:
                # TROP LOIN ! Se rapprocher
                if dist_to_target > 0.05:
                    vx, vy = self.vecteur_robot(robot, target_pos)
                    robot.control(vx * vitesse, vy * vitesse, 0)
                else:
                    # En position, juste orienter
                    theta_robot = robot.orientation
                    w = (angle_to_ball - theta_robot + pi) % (2 * pi) - pi
                    robot.control(0, 0, 4 * w)
            
            else:
                # BONNE DISTANCE (23-27cm) ! Juste suivre et orienter
                if dist_to_target > 0.08:
                    # Petits ajustements
                    vx, vy = self.vecteur_robot(robot, target_pos)
                    robot.control(vx * vitesse * 0.7, vy * vitesse * 0.7, 0)
                else:
                    # Juste s'orienter vers la balle
                    theta_robot = robot.orientation
                    w = (angle_to_ball - theta_robot + pi) % (2 * pi) - pi
                    robot.control(0, 0, 4 * w)
    
    def can_move(self, team: str, robot_id: str) -> bool:
        """Vérifie si on peut contrôler un robot"""
        return self.referee.can_control_robot(robot_id)


def main():
    """Lance la défense corrigée"""
    print("="*60)
    print("🛡️  DÉFENSE CORRIGÉE")
    print("="*60)
    print("Stratégie:")
    print("  🥅 BACK  : Gardien dans notre zone")
    print("  🛡️  FRONT : Suit à 25cm, dégage si danger")
    print("="*60 + "\n")
    
    with rsk.Client() as client:
        defense = Defense(client)
        
        # CONFIGURATION (depuis config.py)
        our_goal = config.OUR_GOAL_POSITION  # Notre but à défendre
        vitesse = 4
        
        print(f"🎯 Notre but : {our_goal}")
        print(f"⚙️  Vitesse   : {vitesse}\n")
        
        try:
            while True:
                # Robot 2 = GARDIEN (back)
                if defense.can_move("green", "2"):
                    try:
                        defense.defense_back_goalkeeper(
                            client.green2, client.ball, our_goal, vitesse
                        )
                    except:
                        pass
                
                # Robot 1 = DÉFENSEUR AVANT (front)
                if defense.can_move("green", "1"):
                    try:
                        defense.defense_front_harasser(
                            client.green1, client.ball, our_goal, vitesse
                        )
                    except:
                        pass
                
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\n⏹️  Arrêt")
        print("\n👋 Terminé\n")


if __name__ == "__main__":
    main()