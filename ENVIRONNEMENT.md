# Nouvelles fonctionnalités - Génération d'environnement

## Paramètres ajoutés

### `--create-venv`
Active la création automatique d'un environnement virtuel et des scripts d'installation.

### `--os-type {windows,linux,auto}`
Spécifie le type d'OS pour les scripts générés :
- `windows` : Génère des scripts PowerShell (.ps1)
- `linux` : Génère des scripts Bash (.sh)
- `auto` (défaut) : Détection automatique basée sur `platform.system()`

## Fichiers générés

Quand `--create-venv` est activé, les fichiers suivants sont créés dans le répertoire de sortie :

### `requirements.txt`
Contient les dépendances nécessaires pour exécuter les tests :
```txt
pytest>=7.4.0
pytest-mock>=3.11.0  
pytest-cov>=4.1.0
faker>=19.0.0
```

### Scripts Windows (si `--os-type windows`)
- **`setup-env.ps1`** : Configure l'environnement virtuel
  - Vérifie Python
  - Crée l'environnement virtuel dans `./venv`
  - Installe les dépendances
  
- **`run-tests.ps1`** : Exécute les tests
  - Active l'environnement virtuel
  - Lance pytest avec couverture de code
  - Génère un rapport HTML dans `htmlcov/`

### Scripts Linux (si `--os-type linux`)
- **`setup-env.sh`** : Configure l'environnement virtuel
  - Vérifie Python3
  - Crée l'environnement virtuel dans `./venv`
  - Installe les dépendances
  - Scripts rendus exécutables automatiquement
  
- **`run-tests.sh`** : Exécute les tests
  - Active l'environnement virtuel
  - Lance pytest avec couverture de code
  - Génère un rapport HTML dans `htmlcov/`

## Utilisation

### Exemple Windows
```bash
python run.py "mon_projet" --output-dir "tests" --create-venv --os-type windows

# Dans le dossier tests/ :
.\setup-env.ps1     # Configuration initiale
.\run-tests.ps1     # Exécution des tests
```

### Exemple Linux
```bash
python run.py "mon_projet" --output-dir "tests" --create-venv --os-type linux

# Dans le dossier tests/ :
./setup-env.sh      # Configuration initiale
./run-tests.sh      # Exécution des tests
```

### Détection automatique
```bash
python run.py "mon_projet" --output-dir "tests" --create-venv
# Détecte automatiquement Windows/Linux et génère les scripts appropriés
```

## Avantages

1. **Isolation** : Environnement virtuel dédié aux tests
2. **Reproductibilité** : Dependencies figées dans requirements.txt
3. **Simplicité** : Scripts prêts à l'emploi
4. **Cross-platform** : Support Windows et Linux
5. **Rapports** : Couverture de code automatique