#!/usr/bin/env python3
"""
Script d'installation et de vérification pour le générateur de tests unitaires
"""

import subprocess
import sys
import requests
from pathlib import Path

def check_python_version():
    """Vérifie la version de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ requis (version actuelle: {version.major}.{version.minor})")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_requirements():
    """Installe les dépendances"""
    print("📦 Installation des dépendances...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dépendances installées")
            return True
        else:
            print(f"❌ Erreur lors de l'installation: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def check_ollama():
    """Vérifie si Ollama est accessible"""
    print("🤖 Vérification d'Ollama...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"✅ Ollama accessible ({len(models)} modèle(s) disponible(s))")
            
            if models:
                print("   Modèles disponibles:")
                for model in models[:5]:  # Limiter à 5 modèles
                    name = model.get('name', 'Inconnu')
                    print(f"   - {name}")
                if len(models) > 5:
                    print(f"   ... et {len(models) - 5} autre(s)")
            else:
                print("   ⚠️  Aucun modèle installé")
                print("   Installez un modèle avec: ollama pull llama3.2")
            
            return True
        else:
            print(f"❌ Ollama non accessible (status: {response.status_code})")
            return False
            
    except requests.ConnectionError:
        print("❌ Impossible de se connecter à Ollama")
        print("   Assurez-vous qu'Ollama est installé et démarré:")
        print("   - Installation: https://ollama.ai")
        print("   - Démarrage: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification d'Ollama: {e}")
        return False

def test_module():
    """Test basique du module"""
    print("🧪 Test du module...")
    
    try:
        # Test d'import
        from src.config import Config
        from src.file_scanner import PythonFileScanner
        from src.code_analyzer import CodeAnalyzer
        
        # Test basique
        config = Config(source_dir="./example")
        scanner = PythonFileScanner(config)
        
        # Vérification que l'exemple existe
        if not Path("./example").exists():
            print("❌ Répertoire d'exemple non trouvé")
            return False
        
        files = scanner.scan_directory()
        if files:
            print(f"✅ Module fonctionne ({len(files)} fichier(s) trouvé(s))")
            return True
        else:
            print("⚠️  Module fonctionne mais aucun fichier trouvé")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors du test du module: {e}")
        return False

def main():
    """Installation et vérification complète"""
    print("=== Installation et Vérification ===\n")
    
    success = True
    
    # Vérification de Python
    if not check_python_version():
        success = False
    
    # Installation des dépendances
    if not install_requirements():
        success = False
    
    # Vérification d'Ollama
    if not check_ollama():
        success = False
    
    # Test du module
    if not test_module():
        success = False
    
    print("\n" + "="*50)
    
    if success:
        print("✅ Installation réussie !")
        print("\n📝 Utilisation:")
        print("   python run.py ./example --dry-run --verbose")
        print("   python demo.py")
    else:
        print("❌ Installation incomplète")
        print("Corrigez les erreurs ci-dessus avant de continuer")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())