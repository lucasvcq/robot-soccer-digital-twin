"""
Programme principal
Point d'entrée pour le contrôle des robots soccer
"""
import time
import rsk
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
            print("🚀 Démarrage de la stratégie...\n")
            
            # Boucle principale
            try:
                while True:
                    # Mise à jour du contrôleur
                    kick_happened = controller.update()
                    
                    # Si un tir a eu lieu, petite pause tactique
                    if kick_happened:
                        print(f"\n{'='*60}")
                        print("⚽ ACTION RÉALISÉE !")
                        controller.print_stats()
                        time.sleep(0.5)  # Pause après action
                    
                    # Attente du prochain cycle
                    time.sleep(config.LOOP_DT)
            
            except KeyboardInterrupt:
                print("\n" + "="*60)
                print("⏹️  ARRÊT MANUEL (Ctrl+C)")
                print("="*60)
                controller.print_stats()
    
    except rsk.ClientError as e:
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