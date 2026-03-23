"""
Générateur de tests unitaires utilisant Ollama
"""

import logging
import os
from pathlib import Path
from typing import Optional

from .config import Config
from .code_analyzer import CodeAnalysis
from .ollama_client import OllamaClient


class TestGenerator:
    """Générateur de tests unitaires avec Ollama"""

    def __init__(self, config: Config, ollama_client: OllamaClient):
        self.config = config
        self.ollama_client = ollama_client
        self.logger = logging.getLogger(__name__)

    def generate_tests(self, source_file: str, analysis: CodeAnalysis) -> int:
        """
        Génère des tests unitaires pour un fichier source

        Args:
            source_file: Chemin vers le fichier source
            analysis: Analyse du code source

        Returns:
            Nombre de tests générés
        """
        try:
            # Lecture du code source
            with open(source_file, "r", encoding="utf-8") as f:
                source_code = f.read()

            # Création du prompt
            prompt = self._create_prompt(source_file, source_code, analysis)

            # Génération avec Ollama
            self.logger.debug(f"Génération des tests pour {source_file}")
            generated_tests = self.ollama_client.generate_response(prompt)

            if not generated_tests:
                self.logger.warning(f"Aucun test généré pour {source_file}")
                return 0

            # Post-traitement des tests générés
            if self.config.minimal_processing:
                # Traitement minimal pour préserver la syntaxe
                processed_tests = self._minimal_post_process_tests(
                    generated_tests, analysis
                )
            else:
                # Traitement complet (peut introduire des erreurs de syntaxe)
                processed_tests = self._post_process_tests(generated_tests, analysis)

            # Sauvegarde des tests
            test_file_path = self._save_tests(source_file, processed_tests)

            if test_file_path:
                self.logger.info(f"Tests sauvegardés dans {test_file_path}")
                # Comptage approximatif des tests générés
                test_count = self._count_tests_in_code(processed_tests)
                return test_count
            else:
                return 0

        except Exception as e:
            self.logger.error(
                f"Erreur lors de la génération des tests pour {source_file}: {e}"
            )
            return 0

    def _create_prompt(
        self, filename: str, source_code: str, analysis: CodeAnalysis
    ) -> str:
        """
        Crée le prompt pour Ollama

        Args:
            filename: Nom du fichier source
            source_code: Code source
            analysis: Analyse du code

        Returns:
            Prompt formaté
        """
        # Prompt simplifié sans l'analyse qui peut confuser le modèle
        return self.config.user_prompt_template.format(
            filename=Path(filename).name, source_code=source_code
        )

    def _post_process_tests(self, generated_tests: str, analysis: CodeAnalysis) -> str:
        """
        Post-traite les tests générés pour améliorer leur qualité

        Args:
            generated_tests: Tests générés par Ollama
            analysis: Analyse du code original

        Returns:
            Tests post-traités
        """
        lines = generated_tests.split("\n")
        processed_lines = []

        # Ajout du header et imports basiques
        processed_lines.extend(
            [
                "# Tests générés automatiquement",
                "",
            ]
        )

        # Ajout des imports nécessaires si manquants
        has_pytest_import = any("import pytest" in line for line in lines[:10])
        has_unittest_import = any("import unittest" in line for line in lines[:10])

        # Header du fichier de test
        if not any(
            line.startswith("#") or line.startswith('"""') for line in lines[:3]
        ):
            processed_lines.extend(
                [
                    '"""',
                    f"Tests unitaires pour {Path(analysis.filename).name}",
                    "Générés automatiquement avec Ollama",
                    '"""',
                    "",
                ]
            )

        # Ajout des imports standard
        imports_added = False

        if not has_pytest_import and not has_unittest_import:
            # Générer les lignes sys.path dynamiquement
            path_setup_lines = self._generate_path_setup(analysis.filename)
            processed_lines.extend(path_setup_lines)
            processed_lines.extend(
                [
                    "import pytest",
                    "from unittest.mock import Mock, patch, MagicMock",
                    "",
                ]
            )
            imports_added = True

        # Ajout de l'import du module testé
        module_import = self._generate_module_import(analysis.filename)
        if module_import:
            processed_lines.append(module_import)
            processed_lines.append("")
            imports_added = True

        # Si on a ajouté des imports, on ajoute une ligne vide
        if imports_added and lines and lines[0].strip():
            processed_lines.append("")

        # Traitement des lignes du code généré
        for line in lines:
            line_stripped = line.strip()

            # Filtrage des lignes parasites
            if self._is_unwanted_line(line_stripped):
                continue

            # Filtrage des imports redondants du module testé (génér's par Ollama)
            if line_stripped.startswith(
                "from math_operations import"
            ) or line_stripped.startswith("import math_operations"):
                continue

            # Correction des noms de test
            if line_stripped.startswith("def ") and "test" not in line_stripped:
                # Assure que les fonctions de test commencent par 'test_'
                func_name = line_stripped.split("(")[0].replace("def ", "")
                if not func_name.startswith("test_"):
                    line = line.replace(f"def {func_name}", f"def test_{func_name}")

            # Ajout d'assertions basiques si manquantes
            if "assert" not in line and line_stripped.endswith("pass"):
                processed_lines.append(
                    line.replace(
                        "pass",
                        "assert True  # TODO: Ajouter des assertions spécifiques",
                    )
                )
            else:
                processed_lines.append(line)

        result = "\n".join(processed_lines)

        # Nettoyage spécialisé pour les erreurs communes d'Ollama
        result = self._clean_ollama_artifacts(result)

        # Validation basique du code généré
        if not self._validate_generated_tests(result):
            self.logger.warning("Les tests générés contiennent des erreurs de syntaxe")
            self.logger.warning(
                "Vous devrez peut-être corriger manuellement le code généré"
            )

        return result

    def _minimal_post_process_tests(
        self, generated_tests: str, analysis: CodeAnalysis
    ) -> str:
        """
        Post-traitement minimal pour préserver la syntaxe

        Args:
            generated_tests: Tests générés par Ollama
            analysis: Analyse du code original

        Returns:
            Tests avec traitement minimal
        """
        # Supprimer seulement les lignes explicitement problématiques
        lines = generated_tests.split("\n")
        processed_lines = []

        # Header simple pour les tests
        processed_lines.extend(
            [
                "# Tests générés automatiquement",
                "",
            ]
        )
        
        # Ajouter les lignes sys.path pour les imports
        path_setup_lines = self._generate_path_setup(analysis.filename)
        processed_lines.extend(path_setup_lines)

        # Vérifier si les imports sont déjà présents et collecter les imports du module
        has_module_import = False
        module_name = Path(analysis.filename).stem
        module_import_lines = []
        other_lines = []

        for line in lines:
            line_stripped = line.strip().lower()

            # Supprimer uniquement les lignes d'explication évidentes
            if (
                line_stripped.startswith("voici")
                or line_stripped.startswith("voila")
                or line_stripped.startswith("here")
                or line_stripped.startswith("```")
                or "explication" in line_stripped
            ):
                continue

            # Séparer les imports du module testé des autres lignes
            line_orig = line.strip()
            if (
                line_orig.startswith("from ") or line_orig.startswith("import ")
            ) and line_orig != "import pytest":
                # Vérifier si c'est un import du bon module
                if (
                    f"from {module_name}" in line_orig
                    or f"import {module_name}" in line_orig
                ):
                    has_module_import = True
                    module_import_lines.append(line)
                elif (
                    "pytest" in line_orig
                    or "unittest" in line_orig
                    or "mock" in line_orig.lower()
                ):
                    # Garder les imports de test - les ajouter après sys.path mais avant module
                    processed_lines.append(line)
                else:
                    # Supprimer les autres imports (probablement incorrects)
                    self.logger.debug(f"Suppression de l'import incorrect: {line_orig}")
                    continue
            else:
                # Vérifier si l'import du module est déjà présent dans cette ligne
                if f"from {module_name}" in line or f"import {module_name}" in line:
                    has_module_import = True
                    module_import_lines.append(line)
                else:
                    other_lines.append(line)

        # Ajouter l'import du module s'il manque
        if not has_module_import:
            # Générer l'import correct
            module_import = self._generate_correct_module_import(analysis.filename)
            if module_import:
                module_import_lines.append(module_import)

        # Maintenant assembler dans le bon ordre: sys.path -> autres imports -> imports module -> reste du code
        if module_import_lines:
            processed_lines.extend(module_import_lines)
            processed_lines.append("")
        
        # Ajouter le reste du code
        processed_lines.extend(other_lines)

        result = "\n".join(processed_lines).strip()

        # Validation basique uniquement
        if "def test_" not in result:
            self.logger.warning("Aucune fonction de test trouvée dans le code généré")

        return result

    def _generate_correct_module_import(self, source_file: str) -> Optional[str]:
        """
        Génère l'import correct pour le module testé de manière simple

        Args:
            source_file: Chemin du fichier source

        Returns:
            Ligne d'import ou None
        """
        try:
            source_path = Path(source_file)

            # Calculer le chemin relatif depuis le répertoire source
            source_dir = Path(self.config.source_dir)

            # Si le fichier est dans le répertoire source ou ses sous-répertoires
            if source_path.is_absolute():
                try:
                    relative_path = source_path.relative_to(source_dir)
                    # Construire le nom du module
                    if len(relative_path.parts) == 1:
                        # Fichier à la racine
                        module_name = relative_path.stem
                    else:
                        # Fichier dans un sous-répertoire
                        module_parts = list(relative_path.with_suffix("").parts)
                        module_name = ".".join(module_parts)

                    return f"from {module_name} import *"
                except ValueError:
                    # Le fichier n'est pas dans le répertoire source
                    pass

            # Fallback: utiliser juste le nom du fichier
            module_name = source_path.stem
            return f"from {module_name} import *"

        except Exception as e:
            self.logger.debug(f"Erreur lors de la génération de l'import: {e}")
            return None

    def _test_syntax_only(self, code: str) -> bool:
        """
        Test uniquement la syntaxe sans logging

        Args:
            code: Code à tester

        Returns:
            True si syntaxiquement correct
        """
        try:
            compile(code, "<generated>", "exec")
            return True
        except SyntaxError:
            return False

    def _clean_ollama_artifacts(self, code: str) -> str:
        """
        Nettoie les artefacts spécifiques générés par Ollama

        Args:
            code: Code généré par Ollama

        Returns:
            Code nettoyé
        """
        lines = code.split("\n")
        cleaned_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()

            # Correction des paramètres pytest incomplets
            if line_stripped.startswith("@pytest.mark.parametrize"):
                # Vérifier si la ligne suivante contient des paramètres incomplets
                param_lines = [line]
                j = i + 1

                # Collecter toutes les lignes de paramètres
                while j < len(lines) and not lines[j].strip().startswith("def "):
                    param_lines.append(lines[j])
                    j += 1

                # Vérifier et corriger le format des paramètres
                param_block = "\n".join(param_lines)
                if "[" in param_block and not ("])" in param_block):
                    # Trouver la dernière ligne de paramètres et ajouter la fermeture
                    if param_lines:
                        last_line = param_lines[-1].rstrip()
                        if not last_line.endswith("])"):
                            if last_line.endswith(","):
                                param_lines[-1] = last_line[:-1] + "])"
                            else:
                                param_lines[-1] = last_line + "])"

                cleaned_lines.extend(param_lines)
                i = j - 1
            else:
                cleaned_lines.append(line)

            i += 1

        return "\n".join(cleaned_lines)

    def _is_unwanted_line(self, line: str) -> bool:
        """
        Détermine si une ligne doit être filtrée

        Args:
            line: Ligne à analyser (sans espaces)

        Returns:
            True si la ligne doit être supprimée
        """
        # Lignes parasites communes
        unwanted_patterns = [
            # Noms de fichiers isolés
            r"^[a-zA-Z_][a-zA-Z0-9_]*\.py:?$",
            # Commentaires de structure vides
            r"^#\s*$",
            # Lignes avec juste des caractères spéciaux
            r"^[^\w\s]*$",
            # Instructions de formatage
            r"^```",
            r"^Here",
            r"voici",
            r"voila",
        ]

        import re

        for pattern in unwanted_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True

        return False

    def _generate_module_import(self, source_file: str) -> Optional[str]:
        """
        Génère l'import pour le module testé

        Args:
            source_file: Chemin du fichier source

        Returns:
            Ligne d'import ou None
        """
        try:
            source_path = Path(source_file)

            # Si le fichier source est dans un sous-répertoire par rapport
            # à la racine du projet, on doit ajuster l'import
            project_root = Path(self.config.source_dir).parent
            relative_from_project = source_path.relative_to(project_root)

            # Conversion du chemin en import Python
            module_parts = list(relative_from_project.with_suffix("").parts)
            module_name = ".".join(module_parts)

            return f"from {module_name} import *"

        except Exception:
            # Fallback: on essaie avec le chemin relatif depuis le working dir
            try:
                # Import direct du nom du fichier avec le chemin depuis le working dir
                rel_path = Path(source_file).relative_to(Path.cwd())
                if len(rel_path.parts) > 1:
                    # Il y a un répertoire, on doit l'inclure
                    module_parts = list(rel_path.with_suffix("").parts)
                    module_name = ".".join(module_parts)
                    return f"from {module_name} import *"
                else:
                    # Import direct
                    filename = Path(source_file).stem
                    return f"from {filename} import *"
            except Exception:
                # Dernier fallback: import direct du nom de fichier
                filename = Path(source_file).stem
                return f"import {filename}"

    def _validate_generated_tests(self, test_code: str) -> bool:
        """
        Validation basique du code de test généré

        Args:
            test_code: Code des tests

        Returns:
            True si le code semble valide, False sinon
        """
        # Vérifications basiques
        if not test_code.strip():
            return False

        # Au moins une fonction de test
        if "def test_" not in test_code:
            return False

        # Tentative de compilation (vérification syntaxique)
        try:
            compile(test_code, "<generated>", "exec")
            return True
        except SyntaxError as e:
            self.logger.warning(f"Erreur de syntaxe dans les tests générés: {e}")

            # Tentative de correction automatique des parenthèses manquantes
            corrected_code = self._fix_syntax_errors(test_code)
            if corrected_code != test_code:
                self.logger.info(
                    "Tentative de correction automatique des erreurs de syntaxe..."
                )
                try:
                    compile(corrected_code, "<generated>", "exec")
                    self.logger.info("Correction automatique réussie")
                    return True
                except SyntaxError:
                    self.logger.warning("Correction automatique échouée")
                    return False
            return False

    def _fix_syntax_errors(self, test_code: str) -> str:
        """
        Tente de corriger automatiquement les erreurs de syntaxe communes

        Args:
            test_code: Code avec des erreurs potentielles

        Returns:
            Code corrigé
        """
        lines = test_code.split("\n")
        corrected_lines = []

        paren_stack = []  # Stack pour parenthèses ()
        bracket_stack = []  # Stack pour crochets []
        brace_stack = []  # Stack pour accolades {}

        i = 0
        while i < len(lines):
            line = lines[i]
            original_line = line
            line_stripped = line.strip()

            # Compter et tracker les ouvertures/fermetures
            for j, char in enumerate(line):
                if char == "(":
                    paren_stack.append((i, j))
                elif char == ")" and paren_stack:
                    paren_stack.pop()
                elif char == "[":
                    bracket_stack.append((i, j))
                elif char == "]" and bracket_stack:
                    bracket_stack.pop()
                elif char == "{":
                    brace_stack.append((i, j))
                elif char == "}" and brace_stack:
                    brace_stack.pop()

            # Détection de points de fermeture nécessaires
            needs_closing = False

            # Si ligne suivante commence par @pytest.fixture, def, class ou si fin de fichier
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                needs_closing = (
                    next_line.startswith("@pytest.fixture")
                    or next_line.startswith("def ")
                    or next_line.startswith("class ")
                    or next_line.startswith("@pytest.mark")
                )
            else:
                needs_closing = True  # Fin de fichier

            corrected_lines.append(original_line)

            # Si on a besoin de fermer et qu'il y a des ouvertures non fermées
            if needs_closing:
                # Fermer dans l'ordre inverse d'ouverture
                closures = []

                # Déterminer l'indentation appropriée
                base_indent = self._get_base_indentation(line)

                # Ajouter les fermetures manquantes
                while paren_stack:
                    closures.append(base_indent + ")")
                    paren_stack.pop()

                while bracket_stack:
                    closures.append(base_indent + "]")
                    bracket_stack.pop()

                while brace_stack:
                    closures.append(base_indent + "}")
                    brace_stack.pop()

                # Ajouter les closures avant la ligne suivante
                corrected_lines.extend(closures)

            i += 1

        # Fermetures finales si nécessaire
        final_closures = []
        while paren_stack:
            final_closures.append(")")
            paren_stack.pop()
        while bracket_stack:
            final_closures.append("]")
            bracket_stack.pop()
        while brace_stack:
            final_closures.append("}")
            brace_stack.pop()

        corrected_lines.extend(final_closures)

        return "\n".join(corrected_lines)

    def _get_base_indentation(self, line: str) -> str:
        """
        Obtient l'indentation de base d'une ligne

        Args:
            line: Ligne de code

        Returns:
            String d'indentation (espaces)
        """
        indent = ""
        for char in line:
            if char in [" ", "\t"]:
                indent += char
            else:
                break
        return indent

    def _save_tests(self, source_file: str, test_code: str) -> Optional[str]:
        """
        Sauvegarde les tests générés

        Args:
            source_file: Fichier source original
            test_code: Code des tests générés

        Returns:
            Chemin du fichier de test sauvegardé ou None en cas d'erreur
        """
        try:
            test_file_path = self.config.get_output_test_path(source_file)
            test_path = Path(test_file_path)

            # Création du répertoire si nécessaire
            test_path.parent.mkdir(parents=True, exist_ok=True)

            # Sauvegarde du fichier
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(test_code)

            self.logger.debug(f"Tests sauvegardés dans {test_path}")
            return str(test_path)

        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des tests: {e}")
            return None

    def _count_tests_in_code(self, test_code: str) -> int:
        """
        Compte le nombre de tests dans le code généré

        Args:
            test_code: Code des tests

        Returns:
            Nombre de tests trouvés
        """
        return test_code.count("def test_")

    def generate_test_suite_summary(self, source_files: list, analyses: list) -> str:
        """
        Génère un résumé de la suite de tests

        Args:
            source_files: Liste des fichiers sources
            analyses: Liste des analyses correspondantes

        Returns:
            Résumé de la suite de tests
        """
        total_functions = sum(len(analysis.functions) for analysis in analyses)
        total_classes = sum(len(analysis.classes) for analysis in analyses)
        total_methods = sum(
            sum(len(cls.methods) for cls in analysis.classes) for analysis in analyses
        )

        summary = []
        summary.append("# Résumé de la génération de tests")
        summary.append(f"- Fichiers analysés: {len(source_files)}")
        summary.append(f"- Fonctions trouvées: {total_functions}")
        summary.append(f"- Classes trouvées: {total_classes}")
        summary.append(f"- Méthodes trouvées: {total_methods}")
        summary.append("")
        summary.append("## Détail par fichier:")

        for source_file, analysis in zip(source_files, analyses):
            rel_path = Path(source_file).relative_to(self.config.source_dir)
            summary.append(
                f"- {rel_path}: {len(analysis.functions)} fonctions, {len(analysis.classes)} classes"
            )

        return "\n".join(summary)
    
    def _generate_path_setup(self, source_file: str) -> list[str]:
        """Génère les lignes sys.path de manière générique
        
        Args:
            source_file: Chemin vers le fichier source à tester
            
        Returns:
            Liste des lignes de code pour configurer sys.path
        """
        try:
            source_path = Path(source_file).resolve()
            source_dir = Path(self.config.source_dir).resolve() 
            tests_dir = Path(self.config.output_dir).resolve()
            
            # Calculer la racine du projet (parent du répertoire source)
            project_root = source_dir.parent
            
            # Calculer le répertoire du fichier source à tester
            source_file_dir = source_path.parent
            
            # Chemins relatifs depuis le répertoire de tests
            rel_project_root = os.path.relpath(project_root, tests_dir)
            rel_source_dir = os.path.relpath(source_file_dir, tests_dir)
            
            # Convertir les chemins Windows en format Python (avec '/' au lieu de '\\')
            rel_project_root = rel_project_root.replace('\\', '/')
            rel_source_dir = rel_source_dir.replace('\\', '/')
            
            lines = [
                "import sys",
                "import os",
                "",
                "# Ajouter le répertoire racine du projet au PYTHONPATH",
                f'project_root = os.path.join(os.path.dirname(__file__), "{rel_project_root}")',
                "sys.path.insert(0, os.path.abspath(project_root))",
                ""
            ]
            
            # Ajouter le répertoire du fichier source seulement s'il est différent de la racine
            if rel_source_dir != rel_project_root:
                lines.extend([
                    f"# Ajouter le répertoire '{source_file_dir.name}/' pour les imports directs",
                    f'source_dir = os.path.join(os.path.dirname(__file__), "{rel_source_dir}")',
                    "sys.path.insert(0, os.path.abspath(source_dir))",
                    ""
                ])
            
            return lines
            
        except Exception as e:
            self.logger.debug(f"Erreur lors de la génération du path setup: {e}")
            # Fallback simple
            return [
                "import sys", 
                "import os",
                "",
                "# Configuration par défaut du PYTHONPATH",
                'project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))',
                "sys.path.insert(0, os.path.abspath(project_root))",
                ""
            ]
