# Générateur de Tests Unitaires avec Ollama

Ce module permet de générer automatiquement des tests unitaires pour du code Python en utilisant Ollama avec un modèle de langage local.

## Fonctionnalités

- ✅ Analyse automatique du code Python (fonctions, classes, méthodes)
- ✅ Génération de tests unitaires avec pytest
- ✅ Support des modèles Ollama locaux
- ✅ Configuration flexible
- ✅ Filtrage des fichiers et répertoires
- ✅ Mode simulation (dry-run)
- ✅ Logging détaillé

## Installation

### Prérequis

1. **Ollama** doit être installé et en cours d'exécution
   ```bash
   # Installation d'Ollama (voir https://ollama.ai)
   ollama pull llama3.2  # ou votre modèle préféré
   ollama serve
   ```

2. **Python 3.8+** avec pip

### Installation des dépendances

```bash
pip install -r requirements.txt
```

## Utilisation

### Utilisation basique

```bash
python run.py /chemin/vers/votre/code
```

### Utilisation avancée

```bash
python run.py /chemin/vers/votre/code \
  --output-dir ./mes_tests \
  --model llama3.2 \
  --host localhost:11434 \
  --exclude-dirs __pycache__ .git venv \
  --exclude-files __init__.py setup.py \
  --verbose
```

### Mode simulation

Pour voir quels fichiers seraient traités sans générer de tests :

```bash
python run.py /chemin/vers/votre/code --dry-run --verbose
```

## Options de configuration

| Option | Description | Défaut |
|--------|-------------|---------|
| `source_dir` | Répertoire contenant le code source | (obligatoire) |
| `--output-dir` | Répertoire de sortie pour les tests | `./tests` |
| `--model` | Modèle Ollama à utiliser | `llama3.2` |
| `--host` | Hôte Ollama | `localhost:11434` |
| `--exclude-dirs` | Répertoires à exclure | `__pycache__`, `.git`, `venv`, etc. |
| `--exclude-files` | Fichiers à exclure | `__init__.py`, `setup.py` |
| `--verbose` | Mode verbose | `False` |
| `--dry-run` | Mode simulation | `False` |

## Structure des tests générés

Les tests sont générés dans une structure qui reflète celle du code source :

```
source/
├── module.py
├── package/
│   ├── __init__.py
│   └── submodule.py
└── utils.py

tests/
├── test_module.py
├── package/
│   └── test_submodule.py
└── test_utils.py
```

## Exemple de test généré

Pour un fichier source `calculator.py` :
```python
def add(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
```

Le test généré `test_calculator.py` ressemblera à :
```python
"""
Tests unitaires pour calculator.py
Générés automatiquement avec Ollama
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from calculator import *

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

class TestCalculator:
    def test_multiply(self):
        calc = Calculator()
        assert calc.multiply(3, 4) == 12
        assert calc.multiply(-2, 5) == -10
        assert calc.multiply(0, 10) == 0
```

## Configuration avancée

Vous pouvez modifier les prompts système dans `src/config.py` pour personnaliser le style de génération des tests.

## Logs

Les logs sont sauvegardés dans `unit_test_generator.log` et affichés dans la console selon le niveau de verbosité.

## Résolution de problèmes

### Ollama non accessible
```
Erreur de connexion à Ollama: ...
```
- Vérifiez qu'Ollama est installé et en cours d'exécution
- Utilisez `ollama serve` pour démarrer le serveur
- Vérifiez l'adresse avec `--host`

### Modèle non trouvé
```
Modèle llama3.2 non trouvé dans les modèles disponibles
```
- Installez le modèle : `ollama pull llama3.2`
- Vérifiez les modèles disponibles : `ollama list`

### Erreurs de génération
- Vérifiez que le code source est syntaxiquement correct
- Augmentez le timeout dans la configuration
- Essayez un modèle différent

## Contribution

Pour contribuer au projet :

1. Fork le repository
2. Créez une branche feature
3. Implémentez vos modifications
4. Ajoutez des tests
5. Soumettez une pull request

## License

MIT License - voir le fichier LICENSE pour les détails.