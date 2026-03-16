#!/usr/bin/env python3
"""
Module principal pour générer des tests unitaires avec Ollama
"""

import argparse
import logging
import os
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
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('unit_test_generator.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    parser = argparse.ArgumentParser(
        description='Générateur de tests unitaires avec Ollama'
    )
    parser.add_argument(
        'source_dir',
        type=str,
        help='Répertoire contenant les fichiers Python à analyser'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./tests',
        help='Répertoire de sortie pour les tests générés (défaut: ./tests)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='llama3:8b',
        help='Modèle Ollama à utiliser (défaut: llama3:8b)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='localhost:11434',
        help='Hôte Ollama (défaut: localhost:11434)'
    )
    parser.add_argument(
        '--exclude-dirs',
        nargs='*',
        default=['__pycache__', '.git', 'venv', 'env', '.venv'],
        help='Répertoires à exclure de l\'analyse'
    )
    parser.add_argument(
        '--exclude-files',
        nargs='*',
        default=['__init__.py', 'setup.py'],
        help='Fichiers à exclure de l\'analyse'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Mode verbose'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mode simulation (sans génération de tests)'
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

        # Configuration
        config = Config(
            source_dir=str(source_path),
            output_dir=args.output_dir,
            model=args.model,
            host=args.host,
            exclude_dirs=args.exclude_dirs,
            exclude_files=args.exclude_files,
            dry_run=args.dry_run
        )
        
        logger.info(f"Démarrage de la génération de tests pour {source_path}")
        logger.info(f"Modèle Ollama: {config.model}")
        logger.info(f"Hôte Ollama: {config.host}")
        
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
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Interruption utilisateur")
        return 0
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        if args.verbose:
            logger.exception("Détails de l'erreur:")
        return 1

if __name__ == "__main__":
    sys.exit(main())
