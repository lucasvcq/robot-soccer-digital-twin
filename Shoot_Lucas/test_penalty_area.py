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
    print(f"   Longueur: {config.constants.field_length:.2f}m")
    print(f"   Largeur:  {config.constants.field_width:.2f}m")
    print(f"   X range: [{FieldUtils.MIN_X:.2f}, {FieldUtils.MAX_X:.2f}]")
    print(f"   Y range: [{FieldUtils.MIN_Y:.2f}, {FieldUtils.MAX_Y:.2f}]")
    
    # Dimensions de la zone interdite
    print(f"\n🚫 Dimensions de la zone interdite:")
    print(f"   Profondeur RÉGLEMENTAIRE: {config.PENALTY_AREA_DEPTH:.2f}m")
    print(f"   Largeur RÉGLEMENTAIRE:    {config.PENALTY_AREA_WIDTH:.2f}m")
    print(f"   Marge de SÉCURITÉ:        {config.PENALTY_AREA_MARGIN:.2f}m")
    total_depth = config.PENALTY_AREA_DEPTH + config.PENALTY_AREA_MARGIN
    total_width = config.PENALTY_AREA_WIDTH + 2 * config.PENALTY_AREA_MARGIN
    print(f"   → Profondeur TOTALE:      {total_depth:.2f}m (avec marge)")
    print(f"   → Largeur TOTALE:         {total_width:.2f}m (avec marge)")
    
    # But à gauche (X négatif)
    goal_left = config.GOAL_POSITION[0]
    print(f"\n⬅️  Zone interdite BUT GAUCHE (X={goal_left:.2f}):")
    x_min_left = FieldUtils.MIN_X
    x_max_left = x_min_left + total_depth
    y_half = total_width / 2.0
    print(f"   X: [{x_min_left:.2f}, {x_max_left:.2f}] (profondeur: {x_max_left - x_min_left:.2f}m)")
    print(f"   Y: [{-y_half:.2f}, {y_half:.2f}] (largeur: {2*y_half:.2f}m)")
    
    # But à droite (X positif)
    goal_right = -goal_left
    print(f"\n➡️  Zone interdite BUT DROITE (X={goal_right:.2f}):")
    x_max_right = FieldUtils.MAX_X
    x_min_right = x_max_right - total_depth
    print(f"   X: [{x_min_right:.2f}, {x_max_right:.2f}] (profondeur: {x_max_right - x_min_right:.2f}m)")
    print(f"   Y: [{-y_half:.2f}, {y_half:.2f}] (largeur: {2*y_half:.2f}m)")
    
    # Test de points
    print(f"\n🧪 Test de points:")
    
    test_points = [
        (0.0, 0.0, "Centre du terrain"),
        (-0.9, 0.0, "Juste devant but gauche"),
        (-0.85, 0.0, "Dans zone gauche"),
        (-0.6, 0.0, "Hors zone gauche"),
        (-0.85, 0.5, "Coin haut zone gauche"),
        (-0.85, -0.5, "Coin bas zone gauche"),
        (0.85, 0.0, "Dans zone droite"),
        (0.6, 0.0, "Hors zone droite"),
    ]
    
    for x, y, description in test_points:
        in_left = FieldUtils.is_in_penalty_area((x, y), goal_left)
        in_right = FieldUtils.is_in_penalty_area((x, y), goal_right)
        
        status = "🚫" if (in_left or in_right) else "✅"
        zone = ""
        if in_left:
            zone = " (Zone GAUCHE)"
        if in_right:
            zone = " (Zone DROITE)"
        
        print(f"   {status} ({x:+.2f}, {y:+.2f}) - {description}{zone}")
    
    # Test de correction de position
    print(f"\n🔧 Test de correction de position:")
    
    dangerous_points = [
        (-0.88, 0.0),
        (-0.85, 0.4),
        (0.88, 0.0),
    ]
    
    for x, y in dangerous_points:
        in_left = FieldUtils.is_in_penalty_area((x, y), goal_left)
        in_right = FieldUtils.is_in_penalty_area((x, y), goal_right)
        
        if in_left:
            safe = FieldUtils.get_safe_position_outside_penalty((x, y), goal_left)
            print(f"   ({x:+.2f}, {y:+.2f}) → ({safe[0]:+.2f}, {safe[1]:+.2f}) [Zone GAUCHE]")
        elif in_right:
            safe = FieldUtils.get_safe_position_outside_penalty((x, y), goal_right)
            print(f"   ({x:+.2f}, {y:+.2f}) → ({safe[0]:+.2f}, {safe[1]:+.2f}) [Zone DROITE]")
        else:
            print(f"   ({x:+.2f}, {y:+.2f}) → Déjà sûr ✅")
    
    print("\n" + "="*60)
    print("✅ Tests terminés")
    print("="*60 + "\n")

if __name__ == "__main__":
    # Import de rsk.constants pour avoir les vraies dimensions
    try:
        from rsk import constants
        config.constants = constants
    except:
        # Valeurs par défaut si RSK n'est pas disponible
        class FakeConstants:
            field_length = 1.83
            field_width = 1.22
        config.constants = FakeConstants()
    
    test_penalty_areas()