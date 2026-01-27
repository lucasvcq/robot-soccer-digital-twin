"""
Script de test pour vérifier les zones interdites (surfaces de réparation)
Affiche les dimensions et teste quelques points
"""

from field_utils import FieldUtils
import config

def test_penalty_areas():
    """Teste les zones interdites des deux côtés"""
    
    print("="*60)
    print("🚫 TEST DES ZONES INTERDITES (Surfaces de Réparation)")
    print("="*60)
    
    # Dimensions du terrain
    print(f"\n📏 Dimensions du terrain:")
    print(f"   Longueur: {FieldUtils.MAX_X * 2:.2f}m")
    print(f"   Largeur:  {FieldUtils.MAX_Y * 2:.2f}m")
    print(f"   X range: [{FieldUtils.MIN_X:.2f}, {FieldUtils.MAX_X:.2f}]")
    print(f"   Y range: [{FieldUtils.MIN_Y:.2f}, {FieldUtils.MAX_Y:.2f}]")
    
    # Dimensions de la zone interdite
    total_depth = config.PENALTY_AREA_DEPTH + config.PENALTY_AREA_MARGIN
    half_width = (config.PENALTY_AREA_WIDTH / 2.0) + config.PENALTY_AREA_MARGIN
    total_width = half_width * 2
    
    print(f"\n🚫 Dimensions de la zone interdite:")
    print(f"   Profondeur RÉGLEMENTAIRE: {config.PENALTY_AREA_DEPTH:.2f}m")
    print(f"   Largeur RÉGLEMENTAIRE:    {config.PENALTY_AREA_WIDTH:.2f}m")
    print(f"   Marge de SÉCURITÉ:        {config.PENALTY_AREA_MARGIN:.2f}m")
    print(f"   → Profondeur TOTALE:      {total_depth:.2f}m (avec marge)")
    print(f"   → Largeur TOTALE:         {total_width:.2f}m (avec marge)")
    
    # But à gauche (X négatif)
    goal_left = config.GOAL_POSITION[0]
    x_min_left = FieldUtils.MIN_X
    x_max_left = x_min_left + total_depth
    print(f"\n⬅️  Zone interdite BUT GAUCHE (X={goal_left:.2f}):")
    print(f"   X: [{x_min_left:.2f}, {x_max_left:.2f}] (profondeur: {x_max_left - x_min_left:.2f}m)")
    print(f"   Y: [{-half_width:.2f}, {half_width:.2f}] (largeur: {total_width:.2f}m)")
    
    # But à droite (X positif)
    goal_right = -goal_left
    x_max_right = FieldUtils.MAX_X
    x_min_right = x_max_right - total_depth
    print(f"\n➡️  Zone interdite BUT DROITE (X={goal_right:.2f}):")
    print(f"   X: [{x_min_right:.2f}, {x_max_right:.2f}] (profondeur: {x_max_right - x_min_right:.2f}m)")
    print(f"   Y: [{-half_width:.2f}, {half_width:.2f}] (largeur: {total_width:.2f}m)")
    
    # Test de points
    print(f"\n🧪 Test de points:")
    
    test_points = [
        (0.0, 0.0, "Centre du terrain", False),
        (-0.90, 0.0, "Très proche but gauche", True),
        (-0.85, 0.0, "Dans zone gauche", True),
        (-0.60, 0.0, "Hors zone gauche (X=0.32m du bord)", False),
        (-0.85, 0.50, "Coin haut zone gauche", True),
        (-0.85, -0.50, "Coin bas zone gauche", True),
        (-0.85, 0.55, "Hors zone gauche (Y trop haut)", False),
        (0.85, 0.0, "Dans zone droite", True),
        (0.60, 0.0, "Hors zone droite", False),
    ]
    
    all_passed = True
    for x, y, description, expected_in_zone in test_points:
        in_left = FieldUtils.is_in_penalty_area((x, y), goal_left)
        in_right = FieldUtils.is_in_penalty_area((x, y), goal_right)
        actual_in_zone = in_left or in_right
        
        if actual_in_zone == expected_in_zone:
            status = "✅"
        else:
            status = "❌"
            all_passed = False
        
        zone = ""
        if in_left:
            zone = " (Zone GAUCHE)"
        if in_right:
            zone = " (Zone DROITE)"
        
        print(f"   {status} ({x:+.2f}, {y:+.2f}) - {description}{zone}")
        if actual_in_zone != expected_in_zone:
            print(f"      ⚠️  Attendu: {'DANS' if expected_in_zone else 'HORS'} zone, Obtenu: {'DANS' if actual_in_zone else 'HORS'} zone")
    
    # Test de correction de position
    print(f"\n🔧 Test de correction de position:")
    
    dangerous_points = [
        (-0.88, 0.0, goal_left),
        (-0.85, 0.40, goal_left),
        (0.88, 0.0, goal_right),
    ]
    
    for x, y, goal in dangerous_points:
        in_zone = FieldUtils.is_in_penalty_area((x, y), goal)
        side = "GAUCHE" if goal < 0 else "DROITE"
        
        if in_zone:
            safe = FieldUtils.get_safe_position_outside_penalty((x, y), goal)
            still_in_zone = FieldUtils.is_in_penalty_area(safe, goal)
            status = "❌ TOUJOURS DANS ZONE!" if still_in_zone else "✅"
            print(f"   {status} ({x:+.2f}, {y:+.2f}) → ({safe[0]:+.2f}, {safe[1]:+.2f}) [Zone {side}]")
        else:
            print(f"   ✅ ({x:+.2f}, {y:+.2f}) → Déjà sûr [Zone {side}]")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ Tous les tests réussis !")
    else:
        print("❌ Certains tests ont échoué")
    print("="*60 + "\n")
    
    return all_passed

if __name__ == "__main__":
    test_penalty_areas()