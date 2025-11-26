# main_strategy.py
from robot_shoot import TwoRobotsShooter
import time

def main():
    # Initialisation unique du jeu
    game = TwoRobotsShooter()
    
    try:
        # --- ÉTAPE 1 : FAIRE UNE PASSE ---
        print(">>> ÉTAPE 1 : Passe vers le point (0, 0.5)")
        # On définit un point au milieu du terrain un peu en haut
        point_de_passe = (0.0, 0.5)
        
        # On lance run avec auto_loop=False pour que ça s'arrête après le tir
        game.run(target=point_de_passe, auto_loop=False)
        
        print(">>> Passe effectuée ! Pause tactique...")
        time.sleep(1.0) # Petite pause entre les actions

        # --- ÉTAPE 2 : TIRER AU BUT ---
        print(">>> ÉTAPE 2 : Tir au but (comportement infini)")
        # Si on met target=None, il reprendra le but par défaut défini dans __init__
        # Ou on peut forcer le but : (-0.91, 0)
        but_adverse = (-0.91, 0.0) 
        
        game.run(target=None, auto_loop=True)

    except KeyboardInterrupt:
        print("Arrêt stratégie.")
    finally:
        game.close()

if __name__ == "__main__":
    main()