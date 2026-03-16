"""
Module de génération automatique de tests unitaires avec Ollama
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"

from .config import Config
from .file_scanner import PythonFileScanner
from .code_analyzer import CodeAnalyzer, CodeAnalysis
from .ollama_client import OllamaClient
from .test_generator import TestGenerator

__all__ = [
    "Config",
    "PythonFileScanner",
    "CodeAnalyzer", 
    "CodeAnalysis",
    "OllamaClient",
    "TestGenerator"
]