import time
from pynput import keyboard
import rsk

class KeyboardController:
    def __init__(self, robot, linear_speed=0.3, angular_speed=2.0, update_rate=0.05):
        self.robot = robot
        self.linear_speed = linear_speed
        self.angular_speed = angular_speed
        self.update_rate = update_rate
        self.keys_pressed = set()
        self.running = True

        # Listener pour les touches
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()

    def on_press(self, key):
        try:
            self.keys_pressed.add(key.char.lower())
        except AttributeError:
            self.keys_pressed.add(key)
    
    def on_release(self, key):
        try:
            self.keys_pressed.remove(key.char.lower())
        except (AttributeError, KeyError):
            self.keys_pressed.discard(key)
        if key == keyboard.Key.esc:
            self.running = False
            return False

    def update(self):
        """Calcule les vitesses et envoie la commande au robot"""
        vx = 0.0
        vy = 0.0
        omega = 0.0

        # Déplacement
        if 'z' in self.keys_pressed:
            vx += self.linear_speed
        if 's' in self.keys_pressed:
            vx -= self.linear_speed
        if 'q' in self.keys_pressed:
            vy += self.linear_speed
        if 'd' in self.keys_pressed:
            vy -= self.linear_speed

        # Rotation sur soi-même
        if 'a' in self.keys_pressed:
            omega += self.angular_speed
        if 'e' in self.keys_pressed:
            omega -= self.angular_speed

        # Tir
        if keyboard.Key.space in self.keys_pressed:
            self.robot.kick()

        # Envoi des commandes
        self.robot.control(vx, vy, omega)

    def run(self):
        """Boucle principale de contrôle"""
        while self.running:
            self.update()
            time.sleep(self.update_rate)

# Exemple d’utilisation
if __name__ == "__main__":
    print("Connexion au simulateur...")
    with rsk.Client() as client:
        robot = client.green1
        controller = KeyboardController(robot)
        print("Contrôle du robot green1 avec ZQSD + A/E pour rotation, espace pour tirer, ESC pour quitter")
        controller.run()
