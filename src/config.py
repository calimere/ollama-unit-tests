"""
Configuration pour le générateur de tests unitaires
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    """Configuration du générateur de tests unitaires"""
    source_dir: str
    output_dir: str = "./tests"
    model: str = "llama3:8b"
    host: str = "localhost:11434"
    exclude_dirs: List[str] = field(default_factory=lambda: [
        "__pycache__", ".git", "venv", "env", ".venv", ".pytest_cache", 
        "node_modules", "dist", "build"
    ])
    exclude_files: List[str] = field(default_factory=lambda: [
        "__init__.py", "setup.py", "conftest.py"
    ])
    dry_run: bool = False
    
    # Configuration du prompt pour Ollama
    system_prompt: str = """Tu es un expert en développement Python et en tests unitaires.
Ton rôle est de générer des tests unitaires complets et pertinents pour du code Python.

Instructions:
- Génère des tests utilisant pytest
- Couvre tous les cas possibles: cas normaux, cas limites, cas d'erreur
- Utilise des mocks quand nécessaire pour les dépendances externes
- Assure-toi que les tests sont clairs et documentés
- Respecte les bonnes pratiques de test
- Génère uniquement le code Python des tests, sans explication supplémentaire
"""
    
    user_prompt_template: str = """Génère des tests unitaires complets pour le code Python suivant:

Nom du fichier: {filename}
Code source:
```python
{source_code}
```

Analyse du code:
{analysis}

Génère les tests en utilisant pytest. Assure-toi de:
1. Tester toutes les fonctions publiques
2. Tester toutes les classes et leurs méthodes
3. Couvrir les cas limites et les erreurs
4. Utiliser des fixtures si nécessaire
5. Mocker les dépendances externes

Retourne uniquement le code Python des tests, prêt à être sauvegardé dans un fichier.
"""
    
    # Configuration avancée
    max_tokens: int = 8000
    temperature: float = 0.1
    timeout: int = 120  # secondes
    
    def get_output_test_path(self, source_file: str) -> str:
        """Retourne le chemin du fichier de test pour un fichier source donné"""
        from pathlib import Path
        
        source_path = Path(source_file)
        relative_path = source_path.relative_to(self.source_dir)
        
        # Conversion du nom de fichier
        test_filename = f"test_{relative_path.stem}.py"
        test_path = Path(self.output_dir) / relative_path.parent / test_filename
        
        return str(test_path)