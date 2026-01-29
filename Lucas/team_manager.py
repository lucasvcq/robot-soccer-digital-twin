"""
🎮 GESTIONNAIRE D'ÉQUIPE FLEXIBLE - VERSION CORRIGÉE
Permet de choisir la couleur d'équipe et gère automatiquement la mi-temps

CORRECTIONS:
1. Détection de mi-temps améliorée avec état de transition
2. Utilisation des constantes du terrain depuis field_utils
3. Méthode force_halftime_change() pour debug
"""
from typing import Tuple, Optional


class TeamManager:
    """
    Gestionnaire d'équipe flexible
    - Choix de la couleur (green ou blue)
    - Détection automatique de la mi-temps
    - Inversion des buts à la mi-temps
    """
    
    # Constantes du terrain (en mètres)
    FIELD_HALF_LENGTH = 0.92  # 1.84m / 2
    
    def __init__(self, team_color: str):
        """
        Args:
            team_color: "green" ou "blue"
        """
        if team_color not in ["green", "blue"]:
            raise ValueError("team_color doit être 'green' ou 'blue'")
        
        self.team_color = team_color
        self.opponent_color = "blue" if team_color == "green" else "green"
        
        # État de la mi-temps
        self.is_second_half = False
        self.halftime_detected = False
        self._last_halftime_running = None  # Pour détecter la transition
        
        # Buts selon la couleur (1ère mi-temps)
        # RÈGLE : Verts attaquent GAUCHE (-), Bleus attaquent DROITE (+)
        if team_color == "green":
            self.original_opponent_goal = (-self.FIELD_HALF_LENGTH, 0.0)  # Verts attaquent à gauche
            self.original_our_goal = (self.FIELD_HALF_LENGTH, 0.0)         # Notre but à droite
        else:  # blue
            self.original_opponent_goal = (self.FIELD_HALF_LENGTH, 0.0)   # Bleus attaquent à droite
            self.original_our_goal = (-self.FIELD_HALF_LENGTH, 0.0)        # Notre but à gauche
        
        print(f"🎮 Équipe sélectionnée : {self.team_color.upper()}")
        print(f"🎯 1ère mi-temps : Attaque vers {self.original_opponent_goal}")
        print(f"🛡️  1ère mi-temps : Défense de {self.original_our_goal}")
    
    def get_current_goals(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Retourne les buts actuels (notre but, but adverse)
        Inversés si on est en 2ème mi-temps
        
        Returns:
            (our_goal, opponent_goal)
        """
        if self.is_second_half:
            # Mi-temps : on inverse !
            return (self.original_opponent_goal, self.original_our_goal)
        else:
            # 1ère mi-temps : normal
            return (self.original_our_goal, self.original_opponent_goal)
    
    def check_halftime(self, client) -> bool:
        """
        Vérifie si la mi-temps vient de se terminer (transition détectée)
        
        VERSION AMÉLIORÉE : Détecte la transition de halftime_is_running True → False
        
        Args:
            client: Client RSK
            
        Returns:
            bool: True si la mi-temps vient de se terminer (changement de côté nécessaire)
        """
        try:
            referee = client.referee
            halftime_running = referee.get("halftime_is_running", False)
            game_running = referee.get("game_is_running", False)
            
            # Debug optionnel
            # print(f"[TeamManager] halftime_running={halftime_running}, game_running={game_running}, is_second_half={self.is_second_half}")
            
            # Initialisation de l'état précédent
            if self._last_halftime_running is None:
                self._last_halftime_running = halftime_running
                return False
            
            # Détection de la TRANSITION : halftime passe de True à False
            # ET le jeu reprend (game_running = True)
            was_halftime = self._last_halftime_running
            now_halftime = halftime_running
            
            if was_halftime and not now_halftime and game_running:
                # La mi-temps vient de se terminer !
                self._last_halftime_running = halftime_running
                
                if not self.is_second_half:
                    # C'est la première fois qu'on détecte la fin de mi-temps
                    self.is_second_half = True
                    
                    our_goal, opponent_goal = self.get_current_goals()
                    
                    print("\n" + "="*70)
                    print("🔄 MI-TEMPS TERMINÉE - CHANGEMENT DE CÔTÉ")
                    print("="*70)
                    print(f"🛡️  Nouveau but à défendre   : {our_goal}")
                    print(f"🎯 Nouveau but à attaquer   : {opponent_goal}")
                    print("="*70 + "\n")
                    
                    return True  # Changement détecté !
            
            # Mise à jour de l'état précédent
            self._last_halftime_running = halftime_running
            return False
            
        except (KeyError, TypeError) as e:
            # print(f"[TeamManager] Erreur accès referee: {e}")
            return False
    
    def force_halftime_change(self):
        """
        Force le changement de mi-temps (pour debug/test)
        Utile si la détection automatique ne fonctionne pas
        """
        if not self.is_second_half:
            self.is_second_half = True
            our_goal, opponent_goal = self.get_current_goals()
            
            print("\n" + "="*70)
            print("⚠️  CHANGEMENT DE CÔTÉ FORCÉ (debug)")
            print("="*70)
            print(f"🛡️  Nouveau but à défendre   : {our_goal}")
            print(f"🎯 Nouveau but à attaquer   : {opponent_goal}")
            print("="*70 + "\n")
            
            return True
        else:
            print("⚠️  Déjà en 2ème mi-temps, pas de changement")
            return False
    
    def get_robots(self, client):
        """
        Retourne les robots de notre équipe
        
        Args:
            client: Client RSK
            
        Returns:
            (robot1, robot2)
        """
        if self.team_color == "green":
            return (client.green1, client.green2)
        else:
            return (client.blue1, client.blue2)
    
    def print_status(self):
        """Affiche l'état actuel de l'équipe"""
        our_goal, opponent_goal = self.get_current_goals()
        
        print(f"\n{'='*60}")
        print(f"📊 ÉTAT DE L'ÉQUIPE {self.team_color.upper()}")
        print(f"{'='*60}")
        print(f"Mi-temps : {'2ÈME' if self.is_second_half else '1ÈRE'}")
        print(f"🛡️  But à défendre : {our_goal}")
        print(f"🎯 But à attaquer : {opponent_goal}")
        print(f"{'='*60}\n")


def choose_team_interactive() -> str:
    """
    Demande interactivement la couleur d'équipe
    
    Returns:
        str: "green" ou "blue"
    """
    print("\n" + "="*70)
    print("🎮 SÉLECTION D'ÉQUIPE")
    print("="*70)
    print()
    print("Quelle équipe contrôlez-vous ?")
    print("  1. 🟢 VERTE (green)")
    print("  2. 🔵 BLEUE (blue)")
    print()
    
    while True:
        choice = input("Votre choix (1 ou 2) : ").strip()
        
        if choice == "1":
            print("\n✅ Équipe VERTE sélectionnée")
            return "green"
        elif choice == "2":
            print("\n✅ Équipe BLEUE sélectionnée")
            return "blue"
        else:
            print("❌ Choix invalide. Tapez 1 ou 2.")


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    # Mode interactif
    team_color = choose_team_interactive()
    
    # Créer le gestionnaire (côté automatique selon la couleur)
    manager = TeamManager(team_color)
    
    # Afficher l'état
    manager.print_status()
    
    print("\n💡 À la mi-temps, les buts seront automatiquement inversés !")
    print("💡 Intégrez ce gestionnaire dans votre main_strategy.py")
    print("\n💡 Pour debug : manager.force_halftime_change() force le changement")