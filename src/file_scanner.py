"""
Scanner pour trouver les fichiers Python dans un répertoire
"""

import logging
from pathlib import Path
from typing import List, Set

from .config import Config


class PythonFileScanner:
    """Scanner pour fichiers Python"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def scan_directory(self) -> List[str]:
        """
        Scanne le répertoire source pour trouver tous les fichiers Python
        
        Returns:
            Liste des chemins des fichiers Python trouvés
        """
        python_files = []
        source_path = Path(self.config.source_dir)
        
        self.logger.debug(f"Scan du répertoire: {source_path}")
        
        for file_path in source_path.rglob("*.py"):
            if self._should_include_file(file_path):
                python_files.append(str(file_path))
                self.logger.debug(f"Fichier inclus: {file_path}")
            else:
                self.logger.debug(f"Fichier exclu: {file_path}")
        
        # Tri pour un ordre déterministe
        python_files.sort()
        return python_files
    
    def _should_include_file(self, file_path: Path) -> bool:
        """
        Détermine si un fichier doit être inclus dans l'analyse
        
        Args:
            file_path: Chemin du fichier à vérifier
            
        Returns:
            True si le fichier doit être inclus, False sinon
        """
        # Vérifier si le fichier est dans le répertoire de sortie des tests
        try:
            output_path = Path(self.config.output_dir).resolve()
            file_absolute = file_path.resolve()
            
            # Si le fichier est dans le répertoire de sortie ou un de ses sous-répertoires
            if output_path in file_absolute.parents or file_absolute == output_path:
                self.logger.debug(f"Fichier exclu (répertoire de tests): {file_path}")
                return False
        except (OSError, ValueError):
            # En cas d'erreur de résolution de chemin, on continue
            pass
        
        # Vérification du nom de fichier
        if file_path.name in self.config.exclude_files:
            return False
        
        # Vérification des répertoires parents
        for part in file_path.parts:
            if part in self.config.exclude_dirs:
                return False
            # Exclure les répertoires contenant "test" dans leur nom
            if "test" in part.lower():
                self.logger.debug(f"Fichier exclu (répertoire contient 'test'): {file_path}")
                return False
        
        # Vérification que ce n'est pas un répertoire caché
        if any(part.startswith('.') for part in file_path.parts):
            # Exception pour les répertoires de configuration communs
            allowed_hidden = {'.github', '.vscode'}
            if not any(part in allowed_hidden for part in file_path.parts):
                return False
        
        # Vérification que le fichier n'est pas vide
        try:
            if file_path.stat().st_size == 0:
                self.logger.debug(f"Fichier vide ignoré: {file_path}")
                return False
        except (OSError, IOError):
            self.logger.warning(f"Impossible de lire les informations du fichier: {file_path}")
            return False

        # Vérification que le fichier ne contient pas "test" dans son nom
        if "test" in file_path.stem.lower():
            self.logger.debug(f"Fichier de test exclu: {file_path}")
            return False
        
        return True
    
    def get_file_stats(self) -> dict:
        """
        Retourne des statistiques sur les fichiers trouvés
        
        Returns:
            Dictionnaire avec les statistiques
        """
        files = self.scan_directory()
        total_size = 0
        total_lines = 0
        
        for file_path in files:
            try:
                path = Path(file_path)
                total_size += path.stat().st_size
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_lines += sum(1 for _ in f)
            except (OSError, IOError, UnicodeDecodeError):
                self.logger.warning(f"Impossible de lire le fichier: {file_path}")
                continue
        
        return {
            'total_files': len(files),
            'total_size_bytes': total_size,
            'total_lines': total_lines,
            'average_size_bytes': total_size // len(files) if files else 0,
            'average_lines': total_lines // len(files) if files else 0
        }