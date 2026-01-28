"""
🛡️ DEFENSE CORRIGÉE V2 - Avec AroundPlanner pour évitement

STRATÉGIE :
- Robot BACK (gardien) : Reste dans NOTRE zone défensive, suit la balle
- Robot FRONT : Se maintient à ~25cm de la balle (évite pénalité abus)
                Si ne peut plus respecter 25cm → fonce et dégage

CORRECTION V2 :
- Utilise AroundPlanner pour contourner la balle intelligemment
- Évite de passer à travers la balle en reculant

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
from around_planner import AroundPlanner
from referee_manager import RefereeManager
import config

class Defense:
    """Défense corrigée V2 avec AroundPlanner"""
    
    # Constantes importantes
    BALL_SAFE_DISTANCE = 0.25  # 25cm de la balle (règle 7)
    BALL_CLEARANCE_THRESHOLD = 0.28  # Si < 28cm et dans zone → dégager
    
    def __init__(self, client):
        self.client = client
        self.referee = RefereeManager(client, team_color="green")
        
        # NOUVEAU : État de contournement pour éviter la balle
        self.avoid_ball_side = {}  # robot_id -> side (-1 ou +1)
    
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
        """
        dx = our_goal[0] - ball[0]
        dy = our_goal[1] - ball[1]
        dist = sqrt(dx**2 + dy**2)
        
        if dist < 0.01:
            return our_goal
        
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
        """
        dx = our_goal[0] - ball[0]
        dy = our_goal[1] - ball[1]
        dist = sqrt(dx**2 + dy**2)
        
        if dist < 0.01:
            side_offset = 0.30
            return FieldUtils.clamp((ball[0], ball[1] + side_offset), margin=0.02)
        
        ux, uy = dx / dist, dy / dist
        
        # Position : 25cm derrière la balle (côté de notre but)
        front_x = ball[0] + ux * self.BALL_SAFE_DISTANCE
        front_y = ball[1] + uy * self.BALL_SAFE_DISTANCE
        
        # Ne pas entrer dans NOTRE zone défensive
        penalty_limit = config.PENALTY_AREA_DEPTH + 0.05
        
        if our_goal[0] < 0:
            if front_x < (FieldUtils.MIN_X + penalty_limit):
                front_x = FieldUtils.MIN_X + penalty_limit
        else:
            if front_x > (FieldUtils.MAX_X - penalty_limit):
                front_x = FieldUtils.MAX_X - penalty_limit
        
        # Ne pas entrer dans la zone ADVERSE
        opponent_goal_x = -our_goal[0]
        temp_pos = (front_x, front_y)
        
        if FieldUtils.is_in_penalty_area(temp_pos, opponent_goal_x):
            safe_margin = config.PENALTY_AREA_DEPTH + config.PENALTY_AREA_MARGIN + 0.05
            
            if opponent_goal_x < 0:
                front_x = max(front_x, FieldUtils.MIN_X + safe_margin)
            else:
                front_x = min(front_x, FieldUtils.MAX_X - safe_margin)
        
        return FieldUtils.clamp((front_x, front_y), margin=0.02)
    
    def _compute_avoid_waypoint(self, robot_pos: Tuple[float, float], 
                                 ball: Tuple[float, float],
                                 target: Tuple[float, float],
                                 robot_id: str) -> Tuple[float, float]:
        """
        NOUVEAU : Calcule un waypoint pour contourner la balle avec AroundPlanner
        
        Args:
            robot_pos: Position actuelle du robot
            ball: Position de la balle
            target: Position cible (où on veut aller)
            robot_id: ID du robot pour mémoriser le côté
            
        Returns:
            Tuple (x, y): Waypoint de contournement
        """
        # Choisir le côté si pas encore fait
        if robot_id not in self.avoid_ball_side:
            # Utiliser AroundPlanner pour choisir le meilleur côté
            self.avoid_ball_side[robot_id] = AroundPlanner.choose_side(robot_pos, ball, target)
        
        side = self.avoid_ball_side[robot_id]
        
        # Calculer le waypoint de contournement
        waypoint = AroundPlanner.compute_around_waypoint(ball, target, side=side)
        
        return waypoint
    
    def _reset_avoid_side(self, robot_id: str):
        """Réinitialise le côté de contournement"""
        if robot_id in self.avoid_ball_side:
            del self.avoid_ball_side[robot_id]
    
    def should_front_clear_ball(self, robot_pos: Tuple[float, float],
                               ball: Tuple[float, float],
                               our_goal: Tuple[float, float]) -> bool:
        """
        Détermine si le front doit foncer dégager la balle
        """
        dist_to_ball = FieldUtils.dist(robot_pos, ball)
        
        if dist_to_ball < self.BALL_CLEARANCE_THRESHOLD:
            dist_ball_goal = FieldUtils.dist(ball, our_goal)
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
        
        CORRECTION V2 : Utilise AroundPlanner pour contourner la balle
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
        
        # Obtenir un ID unique pour ce robot (basé sur sa position initiale)
        robot_id = f"front_{id(robot)}"
        
        # DÉCISION : Dégager ou suivre ?
        should_clear = self.should_front_clear_ball(robot_pos, ball, our_goal)
        
        if should_clear:
            # MODE DÉGAGEMENT : Foncer vers la balle et taper
            self._reset_avoid_side(robot_id)
            
            opponent_goal = (-our_goal[0], 0.0)
            
            # Si la balle est dans la zone adverse, NE PAS y aller !
            if FieldUtils.is_in_penalty_area(ball, opponent_goal[0]):
                safe_distance_pos = self.front_defender_position(ball, our_goal)
                vx, vy = self.vecteur_robot(robot, safe_distance_pos)
                robot.control(vx * vitesse * 0.5, vy * vitesse * 0.5, 0)
                if config.DEBUG_VERBOSE:
                    print(f"[FRONT] ⚠️  Balle dans zone adverse, maintien distance")
            elif dist_to_ball < 0.15:
                # Assez proche pour tirer
                angle_to_opp_goal = atan2(
                    opponent_goal[1] - robot_pos[1],
                    opponent_goal[0] - robot_pos[0]
                )
                
                angle_to_our_goal = atan2(
                    our_goal[1] - robot_pos[1],
                    our_goal[0] - robot_pos[0]
                )
                
                angle_diff = abs(FieldUtils.wrap(angle_to_opp_goal - angle_to_our_goal))
                
                if angle_diff < 1.57:
                    if robot_pos[1] > 0:
                        angle_to_clear = atan2(1.0, 0.0)
                    else:
                        angle_to_clear = atan2(-1.0, 0.0)
                else:
                    angle_to_clear = angle_to_opp_goal
                
                try:
                    robot.goto((ball[0], ball[1], angle_to_clear), wait=False)
                    robot.kick(power=0.95)
                    if config.DEBUG_VERBOSE:
                        print(f"[FRONT] 🥾 DÉGAGEMENT SÉCURISÉ !")
                except:
                    pass
            else:
                # Foncer vers la balle
                vx, vy = self.vecteur_robot(robot, ball)
                robot.control(vx * vitesse * 1.2, vy * vitesse * 1.2, 0)
        else:
            # MODE SUIVI : Maintenir ~25cm de la balle
            target_pos = self.front_defender_position(ball, our_goal)
            
            # Angle pour regarder la balle
            angle_to_ball = atan2(ball[1] - robot_pos[1], 
                                 ball[0] - robot_pos[0])
            
            # Distance à la position cible
            dist_to_target = FieldUtils.dist(robot_pos, target_pos)
            
            # ============================================================
            # CORRECTION V2 : Utiliser AroundPlanner si trop proche
            # ============================================================
            if dist_to_ball < 0.22:
                # TROP PROCHE ! Utiliser AroundPlanner pour contourner
                # On veut aller vers target_pos en évitant la balle
                
                waypoint = self._compute_avoid_waypoint(robot_pos, ball, target_pos, robot_id)
                
                # Aller vers le waypoint
                vx, vy = self.vecteur_robot(robot, waypoint)
                robot.control(vx * vitesse * 0.8, vy * vitesse * 0.8, 0)
                
                if config.DEBUG_VERBOSE:
                    print(f"[FRONT] 🔄 Contournement via AroundPlanner")
            
            elif dist_to_ball > 0.28:
                # TROP LOIN ! Se rapprocher
                self._reset_avoid_side(robot_id)  # Reset le côté de contournement
                
                if dist_to_target > 0.05:
                    vx, vy = self.vecteur_robot(robot, target_pos)
                    robot.control(vx * vitesse, vy * vitesse, 0)
                else:
                    theta_robot = robot.orientation
                    w = (angle_to_ball - theta_robot + pi) % (2 * pi) - pi
                    robot.control(0, 0, 4 * w)
            
            else:
                # BONNE DISTANCE (22-28cm) ! Juste suivre et orienter
                self._reset_avoid_side(robot_id)  # Reset le côté de contournement
                
                if dist_to_target > 0.08:
                    vx, vy = self.vecteur_robot(robot, target_pos)
                    robot.control(vx * vitesse * 0.7, vy * vitesse * 0.7, 0)
                else:
                    theta_robot = robot.orientation
                    w = (angle_to_ball - theta_robot + pi) % (2 * pi) - pi
                    robot.control(0, 0, 4 * w)
    
    def can_move(self, team: str, robot_id: str) -> bool:
        """Vérifie si on peut contrôler un robot"""
        return self.referee.can_control_robot(robot_id)


def main():
    """Lance la défense corrigée"""
    print("="*60)
    print("🛡️  DÉFENSE CORRIGÉE V2")
    print("="*60)
    print("Stratégie:")
    print("  🥅 BACK  : Gardien dans notre zone")
    print("  🛡️  FRONT : Suit à 25cm, contourne avec AroundPlanner")
    print("="*60 + "\n")
    
    with rsk.Client() as client:
        defense = Defense(client)
        
        # CONFIGURATION (depuis config.py)
        our_goal = config.OUR_GOAL_POSITION
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