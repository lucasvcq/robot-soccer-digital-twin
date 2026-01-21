# 📖 Documentation de l'API Simple Shooter

## 🎯 Vue d'ensemble

L'API `simple_shooter.py` vous permet d'utiliser facilement les fonctions de tir dans n'importe quel code, sans vous soucier de la complexité de la navigation et du positionnement.

---

## 🚀 Installation

1. Copiez ces fichiers dans votre dossier :
   - `simple_shooter.py`
   - `config.py`
   - `field_utils.py`
   - `navigation.py`
   - `around_planner.py`

2. C'est tout ! Vous pouvez maintenant importer dans n'importe quel script.

---

## 📦 Deux façons d'utiliser l'API

### 1️⃣ **Fonctions Standalone** (Ultra Simple)

```python
from simple_shooter import shoot_at_goal

with rsk.Client() as client:
    # UNE SEULE LIGNE !
    shoot_at_goal(client.green1, client.ball)
```

✅ **Avantages** : 
- Une ligne de code
- Parfait pour tester rapidement

❌ **Inconvénients** :
- Moins de contrôle
- Bloquant (attend le tir complet)

---

### 2️⃣ **Classe SimpleShooter** (Plus de Contrôle)

```python
from simple_shooter import SimpleShooter

with rsk.Client() as client:
    shooter = SimpleShooter(client.green1)
    shooter.set_power(0.8)
    shooter.shoot_at_goal(client.ball)
```

✅ **Avantages** :
- Réutilisable (plusieurs tirs)
- Mode bloquant ou non-bloquant
- Personnalisable (puissance, cible)

---

## 🔧 Référence API

### Fonctions Standalone

#### `shoot_at_goal(robot, ball, goal=None, power=None)`

Tire au but (bloquant).

**Paramètres :**
- `robot` : Instance du robot (`client.green1` ou `client.green2`)
- `ball` : Tuple `(x, y)` de la position de la balle
- `goal` : (Optionnel) Tuple `(x, y)` du but. Par défaut : `config.GOAL_POSITION`
- `power` : (Optionnel) Puissance 0.0-1.0. Par défaut : `config.POWER_SHOOT`

**Retour :**
- `True` si le tir a réussi

**Exemple :**
```python
shoot_at_goal(client.green1, client.ball)
shoot_at_goal(client.green1, client.ball, power=0.7)
```

---

#### `shoot_at_target(robot, ball, target, power=None)`

Tire vers une cible spécifique (bloquant).

**Paramètres :**
- `robot` : Instance du robot
- `ball` : Tuple `(x, y)` de la balle
- `target` : Tuple `(x, y)` de la cible à viser
- `power` : (Optionnel) Puissance 0.0-1.0

**Exemple :**
```python
# Faire une passe vers (0.5, 0.3)
shoot_at_target(client.green1, client.ball, target=(0.5, 0.3), power=0.6)
```

---

### Classe SimpleShooter

#### `__init__(robot, goal=None)`

Crée un shooter.

**Paramètres :**
- `robot` : Instance du robot
- `goal` : (Optionnel) But par défaut

**Exemple :**
```python
shooter1 = SimpleShooter(client.green1)
shooter2 = SimpleShooter(client.green2, goal=(-1.0, 0.0))
```

---

#### `shoot_at_goal(ball, power=None, wait_for_kick=True)`

Tire au but.

**Paramètres :**
- `ball` : Tuple `(x, y)` de la balle
- `power` : (Optionnel) Puissance 0.0-1.0
- `wait_for_kick` : Si `True` = bloquant, si `False` = non-bloquant

**Retour :**
- `True` si le tir a été effectué
- `False` si encore en cours (mode non-bloquant uniquement)

**Exemple bloquant :**
```python
shooter.shoot_at_goal(ball)  # Attend le tir
```

**Exemple non-bloquant :**
```python
while not shooter.shoot_at_goal(ball, wait_for_kick=False):
    # Votre code ici (ex: surveiller l'adversaire)
    time.sleep(0.05)
```

---

#### `shoot_at(ball, target, power=None, wait_for_kick=True)`

Tire vers une cible.

**Paramètres :**
- `ball` : Tuple `(x, y)` de la balle
- `target` : Tuple `(x, y)` de la cible
- `power` : (Optionnel) Puissance
- `wait_for_kick` : Bloquant ou non

**Exemple :**
```python
shooter.shoot_at(ball, target=(0.8, -0.2), power=0.7)
```

---

#### `set_power(power)`

Change la puissance de tir.

**Paramètres :**
- `power` : Float 0.0-1.0

**Exemple :**
```python
shooter.set_power(0.8)  # 80% de puissance
```

---

#### `set_goal(goal)`

Change le but par défaut.

**Paramètres :**
- `goal` : Tuple `(x, y)`

**Exemple :**
```python
shooter.set_goal((-0.9, 0.0))
```

---

#### `reset()`

Réinitialise l'état de navigation (utile si le robot est bloqué).

**Exemple :**
```python
shooter.reset()
```

---

## 💡 Cas d'Usage Typiques

### Cas 1 : Test Rapide

```python
from simple_shooter import shoot_at_goal
import rsk

with rsk.Client() as client:
    shoot_at_goal(client.green1, client.ball)
```

---

### Cas 2 : Intégration dans Votre Code de Match

```python
from simple_shooter import SimpleShooter
import rsk
import time

with rsk.Client() as client:
    shooter = SimpleShooter(client.green1)
    
    while True:
        # Votre logique de stratégie
        if conditions_pour_tirer():
            shooter.shoot_at_goal(client.ball, wait_for_kick=False)
        
        # Autre logique (défense, positionnement, etc.)
        # ...
        
        time.sleep(0.05)
```

---

### Cas 3 : Passe Entre Robots

```python
from simple_shooter import SimpleShooter

shooter1 = SimpleShooter(client.green1)
shooter2 = SimpleShooter(client.green2)

# Robot 1 passe à Robot 2
position_robot2 = client.green2.position
shooter1.shoot_at(client.ball, target=position_robot2, power=0.6)

# Robot 2 attend et tire
shooter2.shoot_at_goal(client.ball)
```

---

### Cas 4 : Boucle Non-Bloquante avec Autre Logique

```python
shooter = SimpleShooter(client.green1)
kick_done = False

while not kick_done:
    # Tir en cours
    kick_done = shooter.shoot_at_goal(client.ball, wait_for_kick=False)
    
    # Pendant ce temps, faire autre chose
    surveiller_adversaire()
    ajuster_defenseur()
    
    time.sleep(0.05)
```

---

## ⚙️ Configuration

L'API utilise les constantes de `config.py` :

```python
# Puissances par défaut
POWER_SHOOT = 1.0    # Tir au but
POWER_PASS = 0.6     # Passe

# Position du but
GOAL_POSITION = (-1.83/2, 0.0)

# Distance de capture
CAPTURE_DISTANCE = 0.13

# Tolérance d'angle
ANGLE_TOL = math.radians(8)
```

Vous pouvez les modifier dans `config.py` ou passer des paramètres custom.

---

## 🐛 Résolution de Problèmes

### Le robot ne tire pas

**Causes possibles :**
1. La balle est `None` → Attendez qu'elle soit disponible
2. Le robot ne peut pas atteindre la balle → Vérifiez les obstacles
3. Timeout dépassé → Reset avec `shooter.reset()`

**Solution :**
```python
if client.ball is not None:
    shooter.shoot_at_goal(client.ball)
else:
    print("Attente de la balle...")
```

---

### Le robot va dans la mauvaise direction

**Cause :** Le but est mal configuré

**Solution :**
```python
# Vérifiez config.GOAL_POSITION
print(config.GOAL_POSITION)

# Ou forcez le but
shooter.set_goal((-0.9, 0.0))
```

---

### Import Error

**Cause :** Fichiers manquants

**Solution :**
```bash
# Vérifiez que ces fichiers existent :
ls config.py field_utils.py navigation.py around_planner.py simple_shooter.py
```

---

## 🎓 Comparaison des Approches

| Critère | Fonction Standalone | Classe SimpleShooter |
|---------|-------------------|---------------------|
| **Simplicité** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Flexibilité** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Performance** | ⭐⭐⭐ | ⭐⭐⭐⭐ (réutilisable) |
| **Contrôle** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Use Case** | Tests rapides | Production, matches |

---

## 📞 Support

Si vous avez des questions :
1. Lisez les exemples dans `example_usage.py`
2. Vérifiez que tous les fichiers sont présents
3. Testez d'abord avec une fonction standalone
4. Ajoutez des `print()` pour débugger

---

## 🔗 Fichiers Liés

- `simple_shooter.py` - L'API principale
- `example_usage.py` - 8 exemples complets
- `config.py` - Configuration
- `field_utils.py` - Utilitaires géométriques
- `navigation.py` - Navigation intelligente
- `around_planner.py` - Contournement de la balle
