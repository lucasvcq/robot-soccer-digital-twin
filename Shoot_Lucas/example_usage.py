"""
Exemples d'utilisation de l'API simple_shooter
Différents cas d'usage selon vos besoins
"""

import time
import rsk
from simple_shooter import SimpleShooter, shoot_at_goal, shoot_at_target
import config

# ============================================================================
# EXEMPLE 1 : Usage le plus simple possible (fonction standalone)
# ============================================================================

def exemple_1_ultra_simple():
    """Utilisation la plus simple : une seule ligne !"""
    print("=== EXEMPLE 1 : Ultra Simple ===\n")
    
    with rsk.Client() as client:
        # Attend que la balle soit disponible
        while client.ball is None:
            time.sleep(0.1)
        
        # UNE SEULE LIGNE : tire au but !
        shoot_at_goal(client.green1, client.ball)
        
        print("✅ Tir effectué !")


# ============================================================================
# EXEMPLE 2 : Classe SimpleShooter (pour plus de contrôle)
# ============================================================================

def exemple_2_avec_classe():
    """Utilisation avec la classe pour plus de flexibilité"""
    print("=== EXEMPLE 2 : Avec Classe ===\n")
    
    with rsk.Client() as client:
        # Créer un shooter
        shooter = SimpleShooter(client.green1)
        
        while client.ball is None:
            time.sleep(0.1)
        
        # Configurer la puissance
        shooter.set_power(0.8)  # 80% de puissance
        
        # Tirer (bloquant)
        shooter.shoot_at_goal(client.ball)
        
        print("✅ Tir effectué avec 80% de puissance !")


# ============================================================================
# EXEMPLE 3 : Tir vers une cible personnalisée
# ============================================================================

def exemple_3_cible_personnalisee():
    """Tirer vers un point spécifique (pas forcément les cages)"""
    print("=== EXEMPLE 3 : Cible Personnalisée ===\n")
    
    with rsk.Client() as client:
        shooter = SimpleShooter(client.green1)
        
        while client.ball is None:
            time.sleep(0.1)
        
        # Viser un point précis (ex: faire une passe)
        cible = (0.5, 0.3)  # Point à (x=0.5m, y=0.3m)
        shooter.shoot_at(client.ball, target=cible, power=0.6)
        
        print(f"✅ Passe effectuée vers {cible} !")


# ============================================================================
# EXEMPLE 4 : Mode non-bloquant (intégration dans votre propre boucle)
# ============================================================================

def exemple_4_non_bloquant():
    """Mode non-bloquant : vous gardez le contrôle de la boucle"""
    print("=== EXEMPLE 4 : Mode Non-Bloquant ===\n")
    
    with rsk.Client() as client:
        shooter = SimpleShooter(client.green1)
        
        iteration = 0
        kick_done = False
        
        while not kick_done:
            iteration += 1
            
            if client.ball is None:
                time.sleep(0.1)
                continue
            
            # Appel non-bloquant : retourne False si pas encore tiré
            kick_done = shooter.shoot_at_goal(
                client.ball, 
                wait_for_kick=False  # ← MODE NON-BLOQUANT
            )
            
            # Vous pouvez faire autre chose ici !
            print(f"Itération {iteration} - Tir en cours...", end='\r')
            
            time.sleep(config.LOOP_DT)
        
        print(f"\n✅ Tir effectué après {iteration} itérations !")


# ============================================================================
# EXEMPLE 5 : Utilisation dans une stratégie existante
# ============================================================================

def exemple_5_integration_strategie():
    """Intégrer le shooter dans votre propre code de stratégie"""
    print("=== EXEMPLE 5 : Intégration Stratégie ===\n")
    
    with rsk.Client() as client:
        # Créer deux shooters (un par robot)
        shooter1 = SimpleShooter(client.green1)
        shooter2 = SimpleShooter(client.green2)
        
        tirs_effectues = 0
        
        try:
            while tirs_effectues < 3:  # Exemple : 3 tirs
                if client.ball is None:
                    time.sleep(0.1)
                    continue
                
                # Déterminer quel robot est le plus proche
                d1 = ((client.green1.position[0] - client.ball[0])**2 + 
                      (client.green1.position[1] - client.ball[1])**2)**0.5
                d2 = ((client.green2.position[0] - client.ball[0])**2 + 
                      (client.green2.position[1] - client.ball[1])**2)**0.5
                
                if d1 < d2:
                    # Robot 1 tire
                    print(f"Robot 1 attaque (distance: {d1:.2f}m)")
                    shooter1.shoot_at_goal(client.ball)
                else:
                    # Robot 2 tire
                    print(f"Robot 2 attaque (distance: {d2:.2f}m)")
                    shooter2.shoot_at_goal(client.ball)
                
                tirs_effectues += 1
                print(f"✅ Tir {tirs_effectues}/3 effectué !\n")
                
                time.sleep(1)  # Pause entre les tirs
        
        except KeyboardInterrupt:
            print("\nArrêt manuel")
        
        print(f"Fin : {tirs_effectues} tirs effectués")


# ============================================================================
# EXEMPLE 6 : Combiner avec votre propre logique de navigation
# ============================================================================

def exemple_6_navigation_personnalisee():
    """Utiliser uniquement la partie tir, navigation custom"""
    print("=== EXEMPLE 6 : Navigation Personnalisée ===\n")
    
    with rsk.Client() as client:
        shooter = SimpleShooter(client.green1)
        
        while client.ball is None:
            time.sleep(0.1)
        
        # 1. Votre propre navigation (exemple : aller directement à la balle)
        print("1️⃣ Navigation personnalisée vers la balle...")
        client.green1.goto(client.ball, wait=True)
        
        # 2. Puis utiliser le shooter pour la partie tir
        print("2️⃣ Utilisation du shooter pour tirer...")
        shooter.shoot_at_goal(client.ball)
        
        print("✅ Terminé !")


# ============================================================================
# EXEMPLE 7 : Réutilisation d'un shooter (plusieurs tirs)
# ============================================================================

def exemple_7_plusieurs_tirs():
    """Un même shooter pour plusieurs tirs successifs"""
    print("=== EXEMPLE 7 : Plusieurs Tirs ===\n")
    
    with rsk.Client() as client:
        shooter = SimpleShooter(client.green1)
        
        for i in range(3):
            print(f"\n🎯 Tir {i+1}/3")
            
            while client.ball is None:
                time.sleep(0.1)
            
            # Puissance variable
            puissance = 0.6 + (i * 0.2)  # 0.6, 0.8, 1.0
            shooter.set_power(puissance)
            
            shooter.shoot_at_goal(client.ball)
            print(f"✅ Tir effectué avec puissance {puissance:.1f}")
            
            time.sleep(2)  # Attendre que la balle revienne
        
        print("\n🏆 Tous les tirs effectués !")


# ============================================================================
# EXEMPLE 8 : Utilisation dans un match complet
# ============================================================================

def exemple_8_match_complet():
    """Exemple d'utilisation dans un vrai match"""
    print("=== EXEMPLE 8 : Match Complet ===\n")
    
    with rsk.Client() as client:
        # Configuration
        shooter1 = SimpleShooter(client.green1)
        shooter2 = SimpleShooter(client.green2)
        
        buts_marques = 0
        objectif_buts = 5
        
        print(f"🎯 Objectif : {objectif_buts} buts\n")
        
        try:
            while buts_marques < objectif_buts:
                if client.ball is None:
                    time.sleep(0.1)
                    continue
                
                # Logique simple : le plus proche attaque
                from field_utils import FieldUtils
                d1 = FieldUtils.dist(client.green1.position, client.ball)
                d2 = FieldUtils.dist(client.green2.position, client.ball)
                
                if d1 < d2:
                    shooter_actif = shooter1
                    nom = "Green 1"
                else:
                    shooter_actif = shooter2
                    nom = "Green 2"
                
                print(f"⚡ {nom} attaque...")
                shooter_actif.shoot_at_goal(client.ball)
                
                buts_marques += 1
                print(f"⚽ BUT ! ({buts_marques}/{objectif_buts})\n")
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Match arrêté")
        
        print(f"\n📊 Score final : {buts_marques} buts")


# ============================================================================
# MAIN : Choisissez l'exemple à exécuter
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("🤖 EXEMPLES D'UTILISATION DE SIMPLE_SHOOTER")
    print("="*60 + "\n")
    
    # Décommentez l'exemple que vous voulez tester :
    
    #exemple_1_ultra_simple()
    #exemple_2_avec_classe()
    exemple_3_cible_personnalisee()
    #exemple_4_non_bloquant()
    #exemple_5_integration_strategie()
    #exemple_6_navigation_personnalisee()
    #exemple_7_plusieurs_tirs()
    #exemple_8_match_complet()