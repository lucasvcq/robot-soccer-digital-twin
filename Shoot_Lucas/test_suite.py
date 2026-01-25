"""
Suite de tests pour valider le code
Exécutez avec: python3 test_suite.py
"""

import sys
import math

# Import des modules à tester
from field_utils import FieldUtils
import config

def test_field_utils():
    """Tests des utilitaires géométriques"""
    print("\n🧪 Test: FieldUtils")
    
    # Test 1: Distance
    p1 = (0, 0)
    p2 = (3, 4)
    dist = FieldUtils.dist(p1, p2)
    assert abs(dist - 5.0) < 0.001, f"Distance incorrecte: {dist}"
    print("  ✅ dist() OK")
    
    # Test 2: Angle
    angle = FieldUtils.angle((0, 0), (1, 0))
    assert abs(angle - 0) < 0.001, f"Angle incorrect: {angle}"
    print("  ✅ angle() OK")
    
    # Test 3: Unit vector
    uv = FieldUtils.unit_vector((0, 0), (3, 4))
    expected = (0.6, 0.8)
    assert abs(uv[0] - expected[0]) < 0.001, f"Unit vector incorrect: {uv}"
    print("  ✅ unit_vector() OK")
    
    # Test 4: Wrap angle
    wrapped = FieldUtils.wrap(math.pi + 0.1)
    assert -math.pi < wrapped <= math.pi, f"Wrap incorrect: {wrapped}"
    print("  ✅ wrap() OK")
    
    # Test 5: Zone interdite
    # Point clairement dans la zone
    in_zone = FieldUtils.is_in_penalty_area((-0.85, 0.0), -0.92)
    assert in_zone, "Point devrait être dans la zone"
    
    # Point clairement hors zone
    out_zone = FieldUtils.is_in_penalty_area((0.0, 0.0), -0.92)
    assert not out_zone, "Point ne devrait pas être dans la zone"
    print("  ✅ is_in_penalty_area() OK")
    
    # Test 6: Puissance de passe
    power_min = FieldUtils.compute_pass_power(0.30)
    power_max = FieldUtils.compute_pass_power(1.50)
    power_mid = FieldUtils.compute_pass_power(0.90)
    
    assert abs(power_min - config.POWER_PASS_MIN) < 0.01, f"Power min incorrecte: {power_min}"
    assert abs(power_max - config.POWER_PASS_MAX) < 0.01, f"Power max incorrecte: {power_max}"
    assert config.POWER_PASS_MIN < power_mid < config.POWER_PASS_MAX, f"Power mid incorrecte: {power_mid}"
    print("  ✅ compute_pass_power() OK")

def test_config():
    """Tests de la configuration"""
    print("\n🧪 Test: Configuration")
    
    # Vérifier que toutes les constantes critiques existent
    required_constants = [
        'ALIGN_DISTANCE', 'CAPTURE_DISTANCE', 'ANGLE_TOL',
        'FAST_MODE', 'FAST_CAPTURE_DISTANCE', 'FAST_ANGLE_TOL',
        'PENALTY_AREA_DEPTH', 'PENALTY_AREA_WIDTH', 'PENALTY_AREA_MARGIN',
        'POWER_SHOOT', 'POWER_PASS_MIN', 'POWER_PASS_MAX',
        'PASS_DISTANCE_MIN', 'PASS_DISTANCE_MAX',
        'GOAL_POSITION'
    ]
    
    for const in required_constants:
        assert hasattr(config, const), f"Constante manquante: {const}"
    
    print(f"  ✅ Toutes les constantes présentes ({len(required_constants)})")
    
    # Vérifier la cohérence
    assert config.POWER_PASS_MIN < config.POWER_PASS_MAX, "POWER_PASS_MIN doit être < POWER_PASS_MAX"
    assert config.PASS_DISTANCE_MIN < config.PASS_DISTANCE_MAX, "PASS_DISTANCE_MIN doit être < PASS_DISTANCE_MAX"
    assert config.FAST_CAPTURE_DISTANCE > config.CAPTURE_DISTANCE, "FAST_CAPTURE doit être > CAPTURE"
    print("  ✅ Cohérence des valeurs OK")

def test_zones():
    """Tests des zones interdites"""
    print("\n🧪 Test: Zones Interdites")
    
    goal_x = -0.92
    
    # Points de test (ajustés pour la vraie zone)
    tests = [
        # (point, devrait_être_dans_zone, description)
        ((-0.90, 0.0), True, "Centre de la zone"),
        ((-0.85, 0.0), True, "Dans la zone (X et Y OK)"),
        ((-0.50, 0.0), False, "Hors de la zone (X trop loin)"),
        ((-0.85, 0.55), False, "Hors de la zone (Y trop haut)"),
        ((0.0, 0.0), False, "Centre terrain"),
        ((-0.60, 0.0), False, "Hors de la zone (X limite)"),
    ]
    
    passed = 0
    for point, should_be_in, desc in tests:
        is_in = FieldUtils.is_in_penalty_area(point, goal_x)
        if is_in == should_be_in:
            passed += 1
        else:
            print(f"  ⚠️  {desc}: attendu={should_be_in}, obtenu={is_in} pour {point}")
    
    assert passed == len(tests), f"Seulement {passed}/{len(tests)} tests réussis"
    print(f"  ✅ {len(tests)} tests de zones OK")
    
    # Test de correction
    dangerous_point = (-0.88, 0.0)
    safe_point = FieldUtils.get_safe_position_outside_penalty(dangerous_point, goal_x)
    
    # Le point corrigé ne doit PAS être dans la zone
    is_safe = not FieldUtils.is_in_penalty_area(safe_point, goal_x)
    assert is_safe, f"Point corrigé encore dans la zone: {safe_point}"
    print("  ✅ Correction de position OK")

def test_imports():
    """Vérifie que tous les modules s'importent correctement"""
    print("\n🧪 Test: Imports")
    
    try:
        import config
        print("  ✅ config")
        
        from field_utils import FieldUtils
        print("  ✅ field_utils")
        
        from game_state import GameState
        print("  ✅ game_state")
        
        from decision import DecisionEngine, Action
        print("  ✅ decision")
        
        from around_planner import AroundPlanner
        print("  ✅ around_planner")
        
        from navigation import AvoidanceState, aller_derriere_balle
        print("  ✅ navigation")
        
        from robot_agent import RobotAgent
        print("  ✅ robot_agent")
        
        from team_controller import TeamController
        print("  ✅ team_controller")
        
        from referee_manager import RefereeManager
        print("  ✅ referee_manager")
        
    except Exception as e:
        print(f"  ❌ Erreur d'import: {e}")
        return False
    
    return True

def main():
    """Exécute tous les tests"""
    print("="*60)
    print("🧪 SUITE DE TESTS")
    print("="*60)
    
    try:
        # Tests d'imports (bloquant si échec)
        if not test_imports():
            print("\n❌ ÉCHEC: Problème d'imports")
            return 1
        
        # Tests unitaires
        test_config()
        test_field_utils()
        test_zones()
        
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