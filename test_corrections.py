#!/usr/bin/env python3
"""
Script de test pour démontrer les corrections automatiques de parenthèses manquantes
"""

import sys
from pathlib import Path
sys.path.append('src')

# Imports directs des modules
import config
import ollama_client 
import test_generator
import code_analyzer

def test_parentheses_correction():
    """Démontre la correction automatique des parenthèses manquantes"""
    
    # Exemple de code généré avec des parenthèses manquantes (simulé)
    bad_code = '''"""Tests unitaires exemple"""

import pytest
from example import Calculator

@pytest.fixture
def calculator():
    return Calculator(
        precision=2,
        history=[]
        # Parenthèse fermante manquante ici !

def test_calculator_add(calculator):
    result = calculator.add(2, 3)
    assert result == 5
'''

    print("🔧 Tests de correction automatique des parenthèses manquantes")
    print("="*60)
    
    
    config_obj = config.Config(source_dir="./example")
    ollama_client_obj = ollama_client.OllamaClient(config_obj) 
    generator = test_generator.TestGenerator(config_obj, ollama_client_obj)
    
    print("📝 Code original (avec erreurs):")
    print(bad_code)
    print("\n" + "="*60)
    
    # Test de la correction
    try:
        # Vérification que le code original a bien une erreur
        compile(bad_code, '<test>', 'exec')
        print("⚠️  Erreur: le code original devrait avoir une erreur de syntaxe")
        return False
    except SyntaxError as e:
        print(f"✅ Erreur détectée comme attendu: {e}")
    
    # Correction automatique
    corrected_code = generator._fix_syntax_errors(bad_code)
    
    print("\n🔧 Code corrigé automatiquement:")
    print(corrected_code)
    print("\n" + "="*60)
    
    # Test de validation
    try:
        compile(corrected_code, '<test>', 'exec')
        print("✅ Code corrigé compilé avec succès!")
        return True
    except SyntaxError as e:
        print(f"❌ Échec de la correction: {e}")
        return False

def test_validation_improvement():
    """Test de l'amélioration de la validation"""
    print("\n🧪 Test d'amélioration de la validation")
    print("="*60)
    
    config_obj = config.Config(source_dir="./example")
    ollama_client_obj = ollama_client.OllamaClient(config_obj)
    generator = test_generator.TestGenerator(config_obj, ollama_client_obj)
    
    # Code avec erreurs multiples
    code_with_errors = '''
@pytest.fixture
def test_data():
    return [1, 2, 3
    # Crochet et parenthèse manquants

def test_function():
    data = test_data()
    assert len(data == 3  # Parenthèse manquante
'''
    
    print("📝 Code avec erreurs multiples:")
    print(code_with_errors)
    
    # Tentative de correction
    corrected = generator._fix_syntax_errors(code_with_errors)
    
    print("\n🔧 Code après correction:")
    print(corrected)
    
    # Validation
    is_valid = generator._test_syntax_only(corrected)
    print(f"\n{'✅' if is_valid else '❌'} Validation: {'Succès' if is_valid else 'Échec'}")
    
    return is_valid

if __name__ == "__main__":
    print("🚀 Tests des améliorations du générateur de tests\n")
    
    success = True
    
    # Test 1: Correction des parenthèses
    success &= test_parentheses_correction()
    
    # Test 2: Validation améliorée  
    success &= test_validation_improvement()
    
    print("\n" + "="*60)
    if success:
        print("🎉 Tous les tests de correction automatique ont réussi!")
        print("✅ Le générateur peut maintenant corriger automatiquement:")
        print("   • Parenthèses manquantes")
        print("   • Crochets manquants")  
        print("   • Accolades manquantes")
        print("   • Erreurs de syntaxe communes")
    else:
        print("❌ Certains tests ont échoué")
    
    print("\n💡 Utilisation recommandée:")
    print("   python run.py <source_dir> --verbose")
    print("   Les erreurs de syntaxe seront automatiquement corrigées!")