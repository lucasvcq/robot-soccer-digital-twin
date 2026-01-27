"""
Programme principal - Mode Défensif
Point d'entrée pour une stratégie défensive pure (deux défenseurs)
"""
import time
import rsk
from rsk.client import ClientError
from defensive_controller import DefensiveController
import config

def main_defense():
    """
    Fonction principale - Mode Défense
    Lance la boucle de jeu avec stratégie défensive
    """
    print("="*60)
    print("🛡️  ROBOT SOCCER KIT - STRATÉGIE DÉFENSIVE")
    print("="*60)
    print(f"🎯 Notre but    : {(-config.GOAL_POSITION[0], 0.0)}")
    print(f"🎯 But adverse  : {config.GOAL_POSITION}")
    print(f"⚙️  Mode debug   : {'Activé' if config.DEBUG_VERBOSE else 'Désactivé'}")
    print("="*60 + "\n")
    
    try:
        with rsk.Client() as client:
            # Calcul de notre but (opposé au but adverse)
            our_goal = (-config.GOAL_POSITION[0], 0.0)
            opponent_goal = config.GOAL_POSITION
            
            # Création du contrôleur défensif
            controller = DefensiveController(client, our_goal, opponent_goal)
            
            print("✅ Connexion établie")
            print("⏳ En attente du lancement du match dans le simulateur...")
            print("   (Cliquez sur 'Start Game' dans le simulateur)\n")
            
            game_started = False
            
            # Boucle principale
            try:
                while True:
                    # Vérifier si le jeu a démarré
                    if not game_started and controller.referee.is_game_running():
                        game_started = True
                        print("🚀 Match démarré ! Défense active !\n")
                    
                    try:
                        # Mise à jour du contrôleur
                        clearance_happened = controller.update()
                        
                        # Si un dégagement a eu lieu, petite pause tactique
                        if clearance_happened:
                            print(f"\n{'='*60}")
                            print("🥾 DÉGAGEMENT EFFECTUÉ !")
                            controller.print_stats()
                            time.sleep(0.3)  # Petite pause
                    
                    except ClientError as e:
                        # Gestion des erreurs de l'arbitre (pénalités, préemptions)
                        error_msg = str(e)
                        
                        if "preempted" in error_msg:
                            # Robot préempté par l'arbitre (normal, on attend)
                            if "penalty" in error_msg:
                                print(f"\n⚠️  Robot pénalisé : {error_msg}")
                        else:
                            # Autre erreur client
                            print(f"\n⚠️  Erreur client: {error_msg}")
                        
                        # Continue la boucle sans crasher
                        time.sleep(0.1)
                    
                    # Attente du prochain cycle
                    time.sleep(config.LOOP_DT)
            
            except KeyboardInterrupt:
                print("\n" + "="*60)
                print("⏹️  ARRÊT MANUEL (Ctrl+C)")
                print("="*60)
                controller.print_stats()
    
    except ClientError as e:
        print(f"\n❌ ERREUR DE CONNEXION RSK: {e}")
        print("Vérifiez que le simulateur est lancé.")
    
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n👋 Programme terminé proprement.\n")

if __name__ == "__main__":
    main_defense()
