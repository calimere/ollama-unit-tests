"""
Analyseur de code Python pour extraire les informations nécessaires 
à la génération de tests unitaires
"""

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Dict, Any, Optional

from .config import Config


@dataclass
class FunctionInfo:
    """Informations sur une fonction"""
    name: str
    args: List[str]
    returns: Optional[str] = None
    docstring: Optional[str] = None
    line_number: int = 0
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)
    complexity: int = 0  # Complexité cyclomatique approximative


@dataclass
class ClassInfo:
    """Informations sur une classe"""
    name: str
    methods: List[FunctionInfo] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    line_number: int = 0
    decorators: List[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """Informations sur les imports"""
    module: str
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    is_from_import: bool = False


@dataclass
class CodeAnalysis:
    """Résultat de l'analyse d'un fichier Python"""
    filename: str
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    global_variables: List[str] = field(default_factory=list)
    constants: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    total_lines: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    
    def has_testable_code(self) -> bool:
        """Vérifie si le fichier contient du code testable"""
        return len(self.functions) > 0 or len(self.classes) > 0
    
    def get_summary(self) -> str:
        """Retourne un résumé de l'analyse"""
        summary = []
        summary.append(f"Fichier: {self.filename}")
        summary.append(f"Lignes de code: {self.total_lines}")
        summary.append(f"Fonctions: {len(self.functions)}")
        summary.append(f"Classes: {len(self.classes)}")
        
        if self.functions:
            summary.append("\nFonctions détectées:")
            for func in self.functions:
                args_str = ", ".join(func.args)
                summary.append(f"  - {func.name}({args_str})")
        
        if self.classes:
            summary.append("\nClasses détectées:")
            for cls in self.classes:
                summary.append(f"  - {cls.name} (avec {len(cls.methods)} méthode(s))")
        
        if self.imports:
            summary.append(f"\nImports: {len(self.imports)} module(s)")
        
        return "\n".join(summary)


class CodeAnalyzer:
    """Analyseur de code Python utilisant AST"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def analyze_file(self, file_path: str) -> CodeAnalysis:
        """
        Analyse un fichier Python et retourne les informations extraites
        
        Args:
            file_path: Chemin vers le fichier Python
            
        Returns:
            Objet CodeAnalysis contenant les informations extraites
        """
        self.logger.debug(f"Analyse du fichier: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Parse du code avec AST
            tree = ast.parse(source_code, filename=file_path)
            
            # Création de l'objet d'analyse
            analysis = CodeAnalysis(filename=file_path)
            
            # Analyse des lignes
            lines = source_code.split('\n')
            analysis.total_lines = len(lines)
            analysis.blank_lines = sum(1 for line in lines if not line.strip())
            analysis.comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            
            # Visite de l'AST
            visitor = ASTVisitor(analysis)
            visitor.visit(tree)
            
            self.logger.debug(f"Analyse terminée: {len(analysis.functions)} fonctions, {len(analysis.classes)} classes")
            
            return analysis
            
        except SyntaxError as e:
            self.logger.error(f"Erreur de syntaxe dans {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse de {file_path}: {e}")
            raise


class ASTVisitor(ast.NodeVisitor):
    """Visiteur AST pour extraire les informations du code"""
    
    def __init__(self, analysis: CodeAnalysis):
        self.analysis = analysis
        self.current_class = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visite une définition de fonction"""
        func_info = self._extract_function_info(node)
        
        if self.current_class:
            self.current_class.methods.append(func_info)
        else:
            self.analysis.functions.append(func_info)
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visite une définition de fonction asynchrone"""
        func_info = self._extract_function_info(node, is_async=True)
        
        if self.current_class:
            self.current_class.methods.append(func_info)
        else:
            self.analysis.functions.append(func_info)
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visite une définition de classe"""
        class_info = ClassInfo(
            name=node.name,
            line_number=node.lineno,
            docstring=ast.get_docstring(node),
            base_classes=[self._get_name(base) for base in node.bases],
            decorators=[self._get_decorator_name(dec) for dec in node.decorator_list]
        )
        
        # Sauvegarde de la classe courante
        previous_class = self.current_class
        self.current_class = class_info
        
        # Visite des éléments de la classe
        self.generic_visit(node)
        
        # Extraction des attributs de classe
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        class_info.attributes.append(target.id)
        
        self.analysis.classes.append(class_info)
        self.current_class = previous_class
    
    def visit_Import(self, node: ast.Import):
        """Visite un import simple"""
        for alias in node.names:
            import_info = ImportInfo(
                module=alias.name,
                alias=alias.asname,
                is_from_import=False
            )
            self.analysis.imports.append(import_info)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visite un import from"""
        if node.module:
            names = [alias.name for alias in node.names]
            import_info = ImportInfo(
                module=node.module,
                names=names,
                is_from_import=True
            )
            self.analysis.imports.append(import_info)
    
    def visit_Assign(self, node: ast.Assign):
        """Visite une assignation"""
        if not self.current_class:  # Variable globale
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # Distinction entre variable et constante
                    if target.id.isupper():
                        self.analysis.constants.append(target.id)
                    else:
                        self.analysis.global_variables.append(target.id)
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """Visite un gestionnaire d'exception"""
        if node.type and isinstance(node.type, ast.Name):
            self.analysis.exceptions.append(node.type.id)
        self.generic_visit(node)
    
    def _extract_function_info(self, node, is_async=False) -> FunctionInfo:
        """Extrait les informations d'une fonction"""
        # Arguments
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        
        # Type de retour
        returns = None
        if node.returns:
            returns = self._get_name(node.returns)
        
        # Complexité approximative (nombre de branches)
        complexity = self._calculate_complexity(node)
        
        return FunctionInfo(
            name=node.name,
            args=args,
            returns=returns,
            docstring=ast.get_docstring(node),
            line_number=node.lineno,
            is_async=is_async,
            decorators=[self._get_decorator_name(dec) for dec in node.decorator_list],
            complexity=complexity
        )
    
    def _get_name(self, node) -> str:
        """Extrait le nom d'un nœud AST"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return str(node.__class__.__name__)
    
    def _get_decorator_name(self, node) -> str:
        """Extrait le nom d'un décorateur"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        else:
            return "decorator"
    
    def _calculate_complexity(self, node) -> int:
        """Calcule la complexité cyclomatique approximative"""
        complexity = 1  # Base
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity