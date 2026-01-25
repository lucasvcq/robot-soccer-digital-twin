"""
Programme principal
Point d'entrée pour le contrôle des robots soccer
"""
import time
import rsk
from rsk.client import ClientError  # Import correct
from team_controller import TeamController
import config

def main():
    """
    Fonction principale
    Lance la boucle de jeu avec stratégie d'équipe
    """
    print("="*60)
    print("🤖 ROBOT SOCCER KIT - STRATÉGIE D'ÉQUIPE")
    print("="*60)
    print(f"🎯 But adverse : {config.GOAL_POSITION}")
    print(f"⚙️  Mode debug  : {'Activé' if config.DEBUG_STRATEGY else 'Désactivé'}")
    print("="*60 + "\n")
    
    try:
        with rsk.Client() as client:
            # Création du contrôleur d'équipe
            controller = TeamController(client, config.GOAL_POSITION)
            
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
                        print("🚀 Match démarré ! Go go go !\n")
                    
                    try:
                        # Mise à jour du contrôleur
                        kick_happened = controller.update()
                        
                        # Si un tir a eu lieu, petite pause tactique
                        if kick_happened:
                            print(f"\n{'='*60}")
                            print("⚽ ACTION RÉALISÉE !")
                            controller.print_stats()
                            time.sleep(0.5)  # Pause après action
                    
                    except ClientError as e:
                        # Gestion des erreurs de l'arbitre (pénalités, préemptions)
                        error_msg = str(e)
                        
                        if "preempted" in error_msg:
                            # Robot préempté par l'arbitre (normal, on attend)
                            if "penalty" in error_msg:
                                print(f"\n⚠️  Robot pénalisé : {error_msg}")
                            # Pas besoin d'afficher pour les autres préemptions (pause, but, etc.)
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
    main()