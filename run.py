#!/usr/bin/env python3
"""
Module principal pour générer des tests unitaires avec Ollama
"""

import argparse
import logging
import os
import platform
import sys
from pathlib import Path

from src.file_scanner import PythonFileScanner
from src.code_analyzer import CodeAnalyzer
from src.ollama_client import OllamaClient
from src.test_generator import TestGenerator
from src.config import Config


def setup_logging(verbose: bool = False):
    """Configure le système de logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("unit_test_generator.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    parser = argparse.ArgumentParser(
        description="Générateur de tests unitaires avec Ollama"
    )
    parser.add_argument(
        "source_dir",
        type=str,
        help="Répertoire contenant les fichiers Python à analyser",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./tests",
        help="Répertoire de sortie pour les tests générés (défaut: ./tests)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama3:8b",
        help="Modèle Ollama à utiliser (défaut: llama3:8b)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost:11434",
        help="Hôte Ollama (défaut: localhost:11434)",
    )
    parser.add_argument(
        "--exclude-dirs",
        nargs="*",
        default=["__pycache__", ".git", "venv", "env", ".venv"],
        help="Répertoires à exclure de l'analyse",
    )
    parser.add_argument(
        "--exclude-files",
        nargs="*",
        default=["__init__.py", "setup.py"],
        help="Fichiers à exclure de l'analyse",
    )
    parser.add_argument("--verbose", action="store_true", help="Mode verbose")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode simulation (sans génération de tests)",
    )
    parser.add_argument(
        "--no-minimal-processing",
        action="store_true",
        help="Désactiver le traitement minimal (peut introduire des erreurs de syntaxe)",
    )
    parser.add_argument(
        "--create-venv",
        action="store_true",
        help="Créer un environnement virtuel et les scripts d'installation",
    )
    parser.add_argument(
        "--os-type",
        choices=["windows", "linux", "auto"],
        default="auto",
        help="Type d'OS pour les scripts (auto=détection automatique)",
    )
    args = parser.parse_args()

    # Configuration du logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Validation des paramètres
        source_path = Path(args.source_dir)
        if not source_path.exists():
            logger.error(f"Le répertoire source {source_path} n'existe pas")
            return 1

        if not source_path.is_dir():
            logger.error(f"{source_path} n'est pas un répertoire")
            return 1
        # Détection de l'OS
        if args.os_type == "auto":
            detected_os = (
                "windows" if platform.system().lower() == "windows" else "linux"
            )
        else:
            detected_os = args.os_type
            # Configuration
        config = Config(
            source_dir=str(source_path),
            output_dir=args.output_dir,
            model=args.model,
            host=args.host,
            exclude_dirs=args.exclude_dirs,
            exclude_files=args.exclude_files,
            dry_run=args.dry_run,
            minimal_processing=not args.no_minimal_processing,  # Traitement minimal par défaut
        )

        logger.info(f"Démarrage de la génération de tests pour {source_path}")
        logger.info(f"Modèle Ollama: {config.model}")
        logger.info(f"Hôte Ollama: {config.host}")
        logger.info(f"Répertoire de sortie: {config.output_dir}")
        logger.debug(f"Le répertoire de sortie sera automatiquement exclu de l'analyse")

        # Initialisation des composants
        scanner = PythonFileScanner(config)
        analyzer = CodeAnalyzer(config)
        ollama_client = OllamaClient(config)
        generator = TestGenerator(config, ollama_client)

        # Test de connexion à Ollama
        if not args.dry_run:
            logger.info("Test de connexion à Ollama...")
            if not ollama_client.test_connection():
                logger.error("Impossible de se connecter à Ollama")
                return 1
            logger.info("Connexion à Ollama réussie")

        # Scan des fichiers Python
        logger.info("Recherche des fichiers Python...")
        python_files = scanner.scan_directory()
        logger.info(f"Trouvé {len(python_files)} fichier(s) Python")

        if not python_files:
            logger.warning("Aucun fichier Python trouvé")
            return 0

        # Traitement de chaque fichier
        total_tests_generated = 0
        for i, file_path in enumerate(python_files, 1):
            logger.info(f"[{i}/{len(python_files)}] Traitement de {file_path}")

            try:
                # Analyse du code
                analysis = analyzer.analyze_file(file_path)

                if not analysis.has_testable_code():
                    logger.info(f"Aucun code testable trouvé dans {file_path}")
                    continue

                # Génération des tests
                if not args.dry_run:
                    test_count = generator.generate_tests(file_path, analysis)
                    total_tests_generated += test_count
                    logger.info(f"Généré {test_count} test(s) pour {file_path}")
                else:
                    logger.info(f"[DRY RUN] Aurait généré des tests pour {file_path}")

            except Exception as e:
                logger.error(f"Erreur lors du traitement de {file_path}: {e}")
                if args.verbose:
                    logger.exception("Détails de l'erreur:")
                continue

        # Résumé
        logger.info(f"Traitement terminé")
        if not args.dry_run:
            logger.info(f"Total de {total_tests_generated} test(s) généré(s)")
            logger.info(f"Tests sauvegardés dans {config.output_dir}")
            # Génération des scripts d'environnement si demandé
            if args.create_venv:
                logger.info("Génération des scripts d'environnement...")
                _create_environment_scripts(config.output_dir, detected_os)
                logger.info(f"Scripts d'environnement créés pour {detected_os}")
        return 0

    except KeyboardInterrupt:
        logger.info("Interruption utilisateur")
        return 0
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        if args.verbose:
            logger.exception("Détails de l'erreur:")
        return 1


def _create_environment_scripts(output_dir: str, os_type: str):
    """Crée les scripts d'environnement pour l'OS spécifié"""
    output_path = Path(output_dir)

    # Créer requirements.txt
    requirements_content = """# Requirements pour l'exécution des tests générés
pytest>=7.4.0
pytest-mock>=3.11.0
pytest-cov>=4.1.0
faker>=19.0.0  # Pour la génération de données de test

# Dépendances du projet principal
"""

    # Lire et ajouter les dépendances du requirements.txt principal
    main_requirements_path = Path(__file__).parent / "requirements.txt"
    if main_requirements_path.exists():
        try:
            with open(main_requirements_path, "r", encoding="utf-8") as f:
                main_requirements = f.read()
            
            # Filtrer les commentaires et lignes vides du fichier principal
            main_lines = []
            for line in main_requirements.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    main_lines.append(line)
            
            if main_lines:
                requirements_content += '\n'.join(main_lines) + '\n'
        except Exception as e:
            print(f"Attention: Impossible de lire {main_requirements_path}: {e}")

    requirements_path = output_path / "requirements.txt"
    with open(requirements_path, "w", encoding="utf-8") as f:
        f.write(requirements_content)

    if os_type == "windows":
        _create_windows_scripts(output_path)
    else:
        _create_linux_scripts(output_path)

def _create_windows_scripts(output_path: Path):
    """Crée les scripts PowerShell pour Windows"""

    # Script de création d'environnement
    setup_script = """#!/usr/bin/env powershell
# Script de configuration de l'environnement de test pour Windows

Write-Host "Configuration de l'environnement de test..." -ForegroundColor Green

# Verifier si Python est installe
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python n'est pas installe ou n'est pas dans le PATH"
    exit 1
}

# Creer l'environnement virtuel
Write-Host "Creation de l'environnement virtuel..." -ForegroundColor Yellow
python -m venv venv-tests

if (-not $?) {
    Write-Error "Echec de la creation de l'environnement virtuel"
    exit 1
}

# Activer l'environnement virtuel
Write-Host "Activation de l'environnement virtuel..." -ForegroundColor Yellow
& .\\venv-tests\\Scripts\\Activate.ps1

# Mettre a jour pip
Write-Host "Mise a jour de pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Installer les dependances
Write-Host "Installation des dependances..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install -r tests/requirements.txt

Write-Host "Configuration terminee!" -ForegroundColor Green
Write-Host "-----------------------" -ForegroundColor Red
Write-Host "Attention, assurez-vous d'exécuter les scripts avec les permissions appropriées" -ForegroundColor Red
Write-Host "Attention, assurez-vous d'exécuter les scripts à la racine du projet" -ForegroundColor Red
Write-Host "Pour executer les tests: .//tests//run-tests.ps1" -ForegroundColor Cyan
Write-Host "-----------------------" -ForegroundColor Red

"""

    # Script de lancement des tests
    run_tests_script = """#!/usr/bin/env powershell
    # Script pour exécuter les tests

    Write-Host "Exécution des tests..." -ForegroundColor Green

    # Vérifier si l'environnement virtuel existe
    if (-not (Test-Path "venv-tests\\\\Scripts\\\\Activate.ps1")) {
        Write-Error "Environnement virtuel non trouvé. Exécutez d'abord setup-env.ps1"
        exit 1
    }

    # Activer l'environnement virtuel
    & .\\venv-tests\\Scripts\\Activate.ps1

    # Exécuter les tests avec coverage
    pytest --cov=. --cov-report=html --cov-report=term-missing -v

    Write-Host "Tests terminés. Rapport de couverture disponible dans htmlcov/index.html" -ForegroundColor Cyan
    """

    with open(output_path / "setup-env.ps1", "w", encoding="utf-8") as f:
        f.write(setup_script)

    with open(output_path / "run-tests.ps1", "w", encoding="utf-8") as f:
        f.write(run_tests_script)


def _create_linux_scripts(output_path: Path):
    """Crée les scripts Bash pour Linux"""
    import stat

    # Script de création d'environnement
    setup_script = """#!/bin/bash
# Script de configuration de l'environnement de test pour Linux/macOS

echo "Configuration de l'environnement de test..."

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Erreur: Python3 n'est pas installé ou n'est pas dans le PATH"
    exit 1
fi

# Créer l'environnement virtuel
echo "Création de l'environnement virtuel..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Erreur: Échec de la création de l'environnement virtuel"
    exit 1
fi

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate

# Mettre à jour pip
echo "Mise à jour de pip..."
python -m pip install --upgrade pip

# Installer les dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt
pip install -r tests/requirements.txt

echo "Configuration terminée!"
echo "Pour activer l'environnement: source venv/bin/activate"
echo "Pour exécuter les tests: pytest"
"""

    # Script de lancement des tests
    run_tests_script = """#!/bin/bash
# Script pour exécuter les tests

echo "Exécution des tests..."

# Vérifier si l'environnement virtuel existe
if [ ! -f "venv/bin/activate" ]; then
    echo "Erreur: Environnement virtuel non trouvé. Exécutez d'abord ./setup-env.sh"
    exit 1
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Exécuter les tests avec coverage
pytest --cov=. --cov-report=html --cov-report=term-missing -v

echo "Tests terminés. Rapport de couverture disponible dans htmlcov/index.html"
"""

    setup_path = output_path / "setup-env.sh"
    run_path = output_path / "run-tests.sh"

    with open(setup_path, "w", encoding="utf-8") as f:
        f.write(setup_script)

    with open(run_path, "w", encoding="utf-8") as f:
        f.write(run_tests_script)

    # Rendre les scripts exécutables
    setup_path.chmod(setup_path.stat().st_mode | stat.S_IEXEC)
    run_path.chmod(run_path.stat().st_mode | stat.S_IEXEC)


if __name__ == "__main__":
    sys.exit(main())
