#!/usr/bin/env python3
"""
Script de correction pour réparer les tests générés avec des erreurs de syntaxe
"""

import os
import sys
from pathlib import Path

def fix_test_file(file_path: Path) -> bool:
    """
    Corrige un fichier de test avec des erreurs de syntaxe
    
    Args:
        file_path: Chemin vers le fichier de test
        
    Returns:
        True si corrigé avec succès
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📝 Correction de {file_path.name}...")
        
        # Test de la syntaxe originale
        try:
            compile(content, str(file_path), 'exec')
            print(f"✅ {file_path.name} - Aucune erreur détectée")
            return True
        except SyntaxError as e:
            print(f"❌ {file_path.name} - Erreur ligne {e.lineno}: {e.msg}")
        
        # Corrections automatiques
        fixed_content = fix_common_issues(content)
        
        # Test après correction
        try:
            compile(fixed_content, str(file_path), 'exec')
            print(f"🔧 {file_path.name} - Corrigé automatiquement")
            
            # Sauvegarde du fichier corrigé
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            return True
            
        except SyntaxError as e:
            print(f"🚨 {file_path.name} - Correction échouée ligne {e.lineno}: {e.msg}")
            return False
            
    except Exception as e:
        print(f"💥 Erreur lors du traitement de {file_path}: {e}")
        return False

def fix_common_issues(content: str) -> str:
    """
    Corrige les erreurs communes dans les tests générés
    
    Args:
        content: Contenu du fichier
        
    Returns:
        Contenu corrigé
    """
    lines = content.split('\n')
    fixed_lines = []
    
    paren_count = 0
    bracket_count = 0
    brace_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        original_line = line
        
        # Compter les ouvertures/fermetures
        for char in line:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
            elif char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
        
        fixed_lines.append(original_line)
        
        # Vérifier si la ligne suivante nécessite des fermetures
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            needs_closure = (
                next_line.startswith('@pytest.fixture') or
                next_line.startswith('def ') or
                next_line.startswith('class ') or
                next_line.startswith('@pytest.mark') or
                next_line == ''
            )
        else:
            needs_closure = True  # Fin de fichier
        
        # Ajouter les fermetures si nécessaire
        if needs_closure:
            # Obtenir l'indentation de base
            indent = get_indentation(line)
            
            # Ajouter les fermetures manquantes
            while paren_count > 0:
                fixed_lines.append(indent + ')')
                paren_count -= 1
            
            while bracket_count > 0:
                fixed_lines.append(indent + ']')
                bracket_count -= 1
            
            while brace_count > 0:
                fixed_lines.append(indent + '}')
                brace_count -= 1
        
        i += 1
    
    # Corrections spéciales pour pytest.mark.parametrize
    result = '\n'.join(fixed_lines)
    result = fix_pytest_parametrize(result)
    
    return result

def get_indentation(line: str) -> str:
    """Obtient l'indentation d'une ligne"""
    indent = ""
    for char in line:
        if char in [' ', '\t']:
            indent += char
        else:
            break
    return indent

def fix_pytest_parametrize(content: str) -> str:
    """
    Corrige spécifiquement les erreurs de pytest.mark.parametrize
    """
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line.strip().startswith('@pytest.mark.parametrize'):
            # Collecter toutes les lignes jusqu'à la définition de fonction
            param_block = [line]
            j = i + 1
            
            while j < len(lines) and not lines[j].strip().startswith('def '):
                param_block.append(lines[j])
                j += 1
            
            # Vérifier et corriger le bloc de paramètres
            param_content = '\n'.join(param_block)
            
            if '[' in param_content and not '])' in param_content:
                # Ajouter la fermeture manquante
                # Trouver la dernière ligne avec du contenu
                last_content_idx = len(param_block) - 1
                while last_content_idx > 0 and param_block[last_content_idx].strip() == '':
                    last_content_idx -= 1
                
                last_line = param_block[last_content_idx].rstrip()
                if last_line.endswith(','):
                    param_block[last_content_idx] = last_line[:-1] + '])'
                else:
                    param_block[last_content_idx] = last_line + '])'
            
            fixed_lines.extend(param_block)
            i = j - 1
        else:
            fixed_lines.append(line)
        
        i += 1
    
    return '\n'.join(fixed_lines)

def main():
    """Script principal"""
    print("🔧 Script de correction automatique des tests générés")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        test_dir = Path(sys.argv[1])
    else:
        # Utiliser le répertoire du projet resawod par défaut
        test_dir = Path(r"C:\dev\github\resawod\resawod\tests")
    
    if not test_dir.exists():
        print(f"❌ Répertoire non trouvé: {test_dir}")
        print("Usage: python fix_tests.py [repertoire_tests]")
        return 1
    
    print(f"📂 Répertoire de tests: {test_dir}\n")
    
    # Trouver tous les fichiers de test Python
    test_files = list(test_dir.rglob("test_*.py"))
    
    if not test_files:
        print("⚠️  Aucun fichier de test trouvé")
        return 1
    
    print(f"📋 {len(test_files)} fichier(s) de test trouvé(s)\n")
    
    success_count = 0
    error_count = 0
    
    for test_file in test_files:
        if fix_test_file(test_file):
            success_count += 1
        else:
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats:")
    print(f"✅ Fichiers corrigés: {success_count}")
    print(f"❌ Fichiers en erreur: {error_count}")
    
    if error_count == 0:
        print("\n🎉 Tous les tests ont été corrigés avec succès!")
        print("💡 Vous pouvez maintenant exécuter:")
        print(f"   python -m pytest {test_dir} -v")
    else:
        print(f"\n⚠️  {error_count} fichier(s) nécessitent une correction manuelle")
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())