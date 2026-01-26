"""
Suite de tests pour le module défensif
Vérifie que toutes les fonctionnalités fonctionnent correctement
"""
import sys
import math
from field_utils import FieldUtils
from defense_strategy import DefenseStrategy
import config

def test_defensive_positions():
    """Tests des calculs de positions défensives"""
    print("\n🧪 Test: Positions Défensives")
    
    our_goal = (-0.92, 0.0)
    ball = (0.5, 0.3)
    
    # Test 1: Position front
    pos_front = DefenseStrategy.compute_defensive_position(
        ball, our_goal, role="front", margin=0.30
    )
    
    # Vérifier que la position est sur la ligne balle-but
    dist_ball = FieldUtils.dist(pos_front, ball)
    dist_goal = FieldUtils.dist(pos_front, our_goal)
    print(f"  Position front: {pos_front}")
    print(f"    Distance balle: {dist_ball:.3f}m")
    print(f"    Distance but: {dist_goal:.3f}m")
    
    # Vérifier que ce n'est pas dans la zone interdite
    in_zone = FieldUtils.is_in_penalty_area(pos_front, our_goal[0])
    assert not in_zone, f"Position front dans la zone interdite: {pos_front}"
    print(f"  ✅ Position front hors zone interdite")
    
    # Test 2: Position back (plus prudente)
    pos_back = DefenseStrategy.compute_defensive_position(
        ball, our_goal, role="back", margin=0.30
    )
    
    dist_back_goal = FieldUtils.dist(pos_back, our_goal)
    print(f"  Position back: {pos_back}")
    print(f"    Distance but: {dist_back_goal:.3f}m")
    
    # Back doit être plus proche du but que front
    assert dist_back_goal < dist_ball, "Back devrait être plus proche du but"
    print(f"  ✅ Back plus proche du but que front")
    
    # Vérifier hors zone
    in_zone = FieldUtils.is_in_penalty_area(pos_back, our_goal[0])
    assert not in_zone, f"Position back dans la zone interdite: {pos_back}"
    print(f"  ✅ Position back hors zone interdite")

def test_attack_decision():
    """Tests de la décision d'attaque"""
    print("\n🧪 Test: Décision d'Attaque")
    
    our_goal = (-0.92, 0.0)
    
    # Test 1: Balle proche → attaquer
    robot_pos = (0.0, 0.0)
    ball_close = (0.15, 0.1)
    
    should_attack_front = DefenseStrategy.should_attack_ball(
        robot_pos, ball_close, our_goal, role="front"
    )
    should_attack_back = DefenseStrategy.should_attack_ball(
        robot_pos, ball_close, our_goal, role="back"
    )
    
    print(f"  Balle proche ({ball_close}):")
    print(f"    Front attaque: {should_attack_front}")
    print(f"    Back attaque: {should_attack_back}")
    assert should_attack_front, "Front devrait attaquer balle proche"
    print(f"  ✅ Front attaque balle proche")
    
    # Test 2: Balle loin → ne pas attaquer
    ball_far = (0.8, 0.5)
    
    should_attack_front = DefenseStrategy.should_attack_ball(
        robot_pos, ball_far, our_goal, role="front"
    )
    should_attack_back = DefenseStrategy.should_attack_ball(
        robot_pos, ball_far, our_goal, role="back"
    )
    
    print(f"  Balle loin ({ball_far}):")
    print(f"    Front attaque: {should_attack_front}")
    print(f"    Back attaque: {should_attack_back}")
    assert not should_attack_back, "Back ne devrait pas attaquer balle loin"
    print(f"  ✅ Back ne sort pas pour balle loin")

def test_intercept_points():
    """Tests des points d'interception"""
    print("\n🧪 Test: Points d'Interception")
    
    our_goal = (-0.92, 0.0)
    ball = (0.3, 0.2)
    
    # Point d'interception
    intercept = DefenseStrategy.compute_intercept_point(
        ball, our_goal, offset=0.15
    )
    
    print(f"  Balle: {ball}")
    print(f"  Interception: {intercept}")
    
    # Vérifier que le point est derrière la balle (plus loin du but)
    dist_ball_goal = FieldUtils.dist(ball, our_goal)
    dist_intercept_goal = FieldUtils.dist(intercept, our_goal)
    
    assert dist_intercept_goal > dist_ball_goal, "Point d'interception devrait être derrière la balle"
    print(f"  ✅ Point d'interception derrière la balle")
    
    # Vérifier hors zone
    in_zone = FieldUtils.is_in_penalty_area(intercept, our_goal[0])
    assert not in_zone, f"Point d'interception dans la zone interdite: {intercept}"
    print(f"  ✅ Point d'interception hors zone interdite")

def test_clearance_targets():
    """Tests des cibles de dégagement"""
    print("\n🧪 Test: Cibles de Dégagement")
    
    our_goal = (-0.92, 0.0)
    opponent_goal = (0.92, 0.0)
    
    # Test 1: Balle sur le côté → dégager au centre
    ball_side = (0.3, 0.5)
    target = DefenseStrategy.compute_clearance_target(
        ball_side, our_goal, opponent_goal
    )
    
    print(f"  Balle sur côté ({ball_side}) → Cible: {target}")
    assert abs(target[1]) < 0.1, "Devrait dégager vers le centre"
    print(f"  ✅ Dégagement vers le centre")
    
    # Test 2: Balle au centre → dégager sur les côtés
    ball_center = (0.3, 0.0)
    target = DefenseStrategy.compute_clearance_target(
        ball_center, our_goal, opponent_goal
    )
    
    print(f"  Balle au centre ({ball_center}) → Cible: {target}")
    assert abs(target[1]) > 0.2, "Devrait dégager sur le côté"
    print(f"  ✅ Dégagement sur le côté")

def test_goalkeeper_position():
    """Tests de la position de gardien"""
    print("\n🧪 Test: Position Gardien")
    
    our_goal = (-0.92, 0.0)
    
    # Test avec différentes positions de balle
    test_cases = [
        ((0.5, 0.3), "Balle en haut à droite"),
        ((0.5, -0.3), "Balle en bas à droite"),
        ((0.0, 0.0), "Balle au centre"),
    ]
    
    for ball, description in test_cases:
        gk_pos = DefenseStrategy.compute_goalkeeper_position(
            ball, our_goal, max_distance=0.25
        )
        
        print(f"  {description} ({ball}):")
        print(f"    Position gardien: {gk_pos}")
        
        # Vérifier distance au but
        dist_to_goal = FieldUtils.dist(gk_pos, our_goal)
        assert dist_to_goal <= 0.30, f"Gardien trop loin du but: {dist_to_goal}m"
        
        # Vérifier hors zone
        in_zone = FieldUtils.is_in_penalty_area(gk_pos, our_goal[0])
        assert not in_zone, f"Gardien dans la zone interdite: {gk_pos}"
        
        print(f"    ✅ Distance: {dist_to_goal:.3f}m, hors zone")

def test_safety_distance():
    """Tests du calcul de distance de sécurité"""
    print("\n🧪 Test: Distance de Sécurité")
    
    # Plus la balle est proche, plus on doit être proche pour couvrir l'angle
    test_distances = [0.5, 1.0, 1.5, 2.0]
    
    for ball_dist in test_distances:
        safety = DefenseStrategy._compute_safety_distance(ball_dist)
        print(f"  Distance balle-but: {ball_dist:.2f}m → Sécurité: {safety:.3f}m")
        
        # Vérifier bornes
        assert 0.15 <= safety <= 0.50, f"Distance de sécurité hors bornes: {safety}"
    
    print(f"  ✅ Toutes les distances de sécurité dans les bornes")

def test_imports():
    """Vérifie que tous les modules s'importent correctement"""
    print("\n🧪 Test: Imports")
    
    try:
        from defense_strategy import DefenseStrategy
        print("  ✅ defense_strategy")
        
        from defense_agent import DefenseAgent
        print("  ✅ defense_agent")
        
        from defensive_controller import DefensiveController
        print("  ✅ defensive_controller")
        
    except Exception as e:
        print(f"  ❌ Erreur d'import: {e}")
        return False
    
    return True

def main():
    """Exécute tous les tests"""
    print("="*60)
    print("🧪 SUITE DE TESTS - MODULE DÉFENSIF")
    print("="*60)
    
    try:
        # Tests d'imports (bloquant si échec)
        if not test_imports():
            print("\n❌ ÉCHEC: Problème d'imports")
            return 1
        
        # Tests unitaires
        test_defensive_positions()
        test_attack_decision()
        test_intercept_points()
        test_clearance_targets()
        test_goalkeeper_position()
        test_safety_distance()
        
        print("\n" + "="*60)
        print("✅ TOUS LES TESTS RÉUSSIS")
        print("="*60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
