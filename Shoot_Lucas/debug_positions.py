"""
Script de debug pour afficher les positions en temps réel
et vérifier si les robots entrent dans la zone interdite
"""

import time
import rsk
from field_utils import FieldUtils
import config

def debug_positions():
    """Affiche les positions des robots en temps réel avec détection de zone"""
    
    print("="*70)
    print("🔍 MODE DEBUG - Surveillance des Zones Interdites")
    print("="*70)
    print(f"Zone gauche : X ∈ [{FieldUtils.MIN_X:.2f}, {FieldUtils.MIN_X + 0.35:.2f}]")
    print(f"              Y ∈ [-0.50, +0.50]")
    print("="*70)
    print("Appuyez sur Ctrl+C pour arrêter\n")
    
    violations_count = 0
    
    try:
        with rsk.Client() as client:
            while True:
                # Positions
                r1_pos = client.green1.position
                r2_pos = client.green2.position
                ball = client.ball
                
                if r1_pos is None or r2_pos is None:
                    time.sleep(0.1)
                    continue
                
                # Vérifier les violations
                in_zone_r1 = FieldUtils.is_in_penalty_area(r1_pos, config.GOAL_X)
                in_zone_r2 = FieldUtils.is_in_penalty_area(r2_pos, config.GOAL_X)
                
                # Affichage
                status_r1 = "🚫 VIOLATION!" if in_zone_r1 else "✅"
                status_r2 = "🚫 VIOLATION!" if in_zone_r2 else "✅"
                
                if in_zone_r1 or in_zone_r2:
                    violations_count += 1
                    print("\n" + "⚠️ "*20)
                
                print(f"\r{status_r1} R1: ({r1_pos[0]:+.3f}, {r1_pos[1]:+.3f}) | "
                      f"{status_r2} R2: ({r2_pos[0]:+.3f}, {r2_pos[1]:+.3f}) | "
                      f"Ball: ({ball[0]:+.3f}, {ball[1]:+.3f}) | "
                      f"Violations: {violations_count}", end='')
                
                if in_zone_r1 or in_zone_r2:
                    print()  # Nouvelle ligne après violation
                
                time.sleep(0.05)
    
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print(f"📊 Total de violations détectées: {violations_count}")
        print("="*70)

if __name__ == "__main__":
    debug_positions()