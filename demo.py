#!/usr/bin/env python3
"""
Script de démonstration du générateur de tests unitaires
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Démonstration du générateur de tests"""
    print("=== Démonstration du Générateur de Tests Unitaires ===\n")
    
    # Chemin vers le répertoire d'exemple
    example_dir = Path(__file__).parent / "example"
    output_dir = Path(__file__).parent / "generated_tests"
    
    print(f"📁 Répertoire source: {example_dir}")
    print(f"📁 Répertoire de sortie: {output_dir}")
    print()
    
    # Commande à exécuter
    cmd = [
        sys.executable, 
        "run.py",
        str(example_dir),
        "--output-dir", str(output_dir),
        "--model", "llama3.2",
        "--verbose"
    ]
    
    print("🚀 Exécution de la commande:")
    print(" ".join(cmd))
    print("\n" + "="*60 + "\n")
    
    try:
        # Exécution du générateur
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        print("\n" + "="*60)
        print(f"✅ Terminé avec le code de sortie: {result.returncode}")
        
        if result.returncode == 0:
            print(f"\n📋 Vérifiez les tests générés dans: {output_dir}")
        
    except FileNotFoundError:
        print("❌ Erreur: Impossible de trouver Python ou le script run.py")
        print("Assurez-vous d'être dans le bon répertoire.")
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Interruption utilisateur")
        return 0
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())