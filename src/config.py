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
    exclude_dirs: List[str] = field(
        default_factory=lambda: [
            "__pycache__",
            ".git",
            "venv",
            "env",
            ".venv",
            ".pytest_cache",
            "node_modules",
            "dist",
            "build",
        ]
    )
    exclude_files: List[str] = field(
        default_factory=lambda: ["__init__.py", "setup.py", "conftest.py"]
    )
    dry_run: bool = False

    # Configuration du prompt pour Ollama
    system_prompt: str = """Tu es un développeur Python expert en tests unitaires. 
Génère du code Python syntaxiquement correct avec toutes les parenthèses, crochets et guillemets correctement fermés.
Utilise pytest pour les tests. Retourne UNIQUEMENT le code Python, sans explication.
"""

    user_prompt_template: str = """Écris des tests unitaires pytest pour ce code Python:

```python
{source_code}
```

Règles importantes:
- Utilise pytest
- Teste toutes les fonctions et classes publiques  
- Inclus les imports nécessaires
- Assure-toi que chaque parenthèse, crochet et guillemet est correctement fermé
- Vérifie la syntaxe Python
- Retourne UNIQUEMENT le code Python des tests, sans explication

Code Python des tests:
"""

    # Configuration avancée
    max_tokens: int = 8000
    temperature: float = 0.1
    timeout: int = 120  # secondes
    minimal_processing: bool = True  # Traitement minimal pour préserver la syntaxe

    def get_output_test_path(self, source_file: str) -> str:
        """Retourne le chemin du fichier de test pour un fichier source donné"""
        from pathlib import Path

        source_path = Path(source_file)
        relative_path = source_path.relative_to(self.source_dir)

        # Conversion du nom de fichier
        test_filename = f"test_{relative_path.stem}.py"
        test_path = Path(self.output_dir) / relative_path.parent / test_filename

        return str(test_path)
