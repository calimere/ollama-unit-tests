"""
Client pour communiquer avec Ollama
"""

import json
import logging
import time
from typing import Dict, Any, Optional

import requests

from .config import Config


class OllamaClient:
    """Client pour l'API Ollama"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_url = f"http://{config.host}"
        self.session = requests.Session()
        
        # Configuration des timeouts
        self.session.timeout = (10, config.timeout)
        
    def test_connection(self) -> bool:
        """
        Test la connexion avec Ollama
        
        Returns:
            True si la connexion est OK, False sinon
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            # Vérification que le modèle est disponible
            data = response.json()
            available_models = [model.get('name', '') for model in data.get('models', [])]
            
            if self.config.model not in available_models:
                # Vérification avec le nom de base (sans tag)
                model_base = self.config.model.split(':')[0]
                base_matches = [m for m in available_models if m.startswith(model_base + ':')]
                
                if not base_matches:
                    self.logger.error(f"Modèle '{self.config.model}' introuvable.")
                    self.logger.error(f"Modèles disponibles: {', '.join(available_models)}")
                    self.logger.error(f"Installez le modèle avec: ollama pull {self.config.model}")
                    return False
                else:
                    self.logger.warning(f"Modèle exact '{self.config.model}' non trouvé.")
                    self.logger.warning(f"Modèles similaires disponibles: {', '.join(base_matches)}")
                    # On continue quand même
            
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Erreur de connexion à Ollama: {e}")
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"Erreur de décodage JSON: {e}")
            return False
    
    def generate_response(self, prompt: str) -> Optional[str]:
        """
        Génère une réponse avec Ollama
        
        Args:
            prompt: Le prompt pour la génération
            
        Returns:
            La réponse générée ou None en cas d'erreur
        """
        self.logger.debug(f"Envoi du prompt à Ollama (taille: {len(prompt)} caractères)")
        self.logger.debug(f"Utilisation du modèle: {self.config.model}")
        
        try:
            payload = {
                "model": self.config.model,
                "prompt": prompt,
                "system": self.config.system_prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                    "stop": ["```\n\n", "# End of", "```python\n```"]
                }
            }
            
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "").strip()
            
            self.logger.debug(f"Réponse générée en {end_time - start_time:.2f}s (taille: {len(generated_text)} caractères)")
            
            if not generated_text:
                self.logger.warning("Réponse vide reçue d'Ollama")
                return None
            
            # Nettoyage de la réponse
            cleaned_text = self._clean_response(generated_text)
            
            return cleaned_text
            
        except requests.RequestException as e:
            self.logger.error(f"Erreur lors de la requête à Ollama: {e}")
            if "404" in str(e):
                self.logger.error(f"Le modèle '{self.config.model}' n'existe peut-être pas.")
                models = self.get_available_models()
                if models:
                    self.logger.error(f"Modèles disponibles: {', '.join(models)}")
                else:
                    self.logger.error("Aucun modèle trouvé. Installez un modèle avec: ollama pull <model_name>")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Erreur de décodage JSON de la réponse: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de la génération: {e}")
            return None
    
    def _clean_response(self, response: str) -> str:
        """
        Nettoie la réponse d'Ollama pour ne garder que le code Python
        
        Args:
            response: Réponse brute d'Ollama
            
        Returns:
            Code Python nettoyé
        """
        lines = response.split('\n')
        cleaned_lines = []
        in_code_block = False
        code_block_started = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Détection du début d'un bloc de code Python
            if line_stripped.startswith('```python') or line_stripped.startswith('```py'):
                in_code_block = True
                code_block_started = True
                continue
            
            # Détection de la fin d'un bloc de code
            if in_code_block and line_stripped == '```':
                in_code_block = False
                continue
            
            # Si on est dans un bloc de code, on ajoute la ligne
            if in_code_block:
                cleaned_lines.append(line)
            # Si aucun bloc de code n'a été détecté, on considère tout comme du code
            elif not code_block_started and line_stripped and not line_stripped.startswith('#'):
                # Éviter les explications en texte
                if not any(word in line_stripped.lower() for word in ['voici', 'voila', 'ci-dessous', 'following', 'here']):
                    cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # Si le résultat est vide et qu'on avait du contenu, on retourne l'original
        if not result and response.strip():
            self.logger.warning("Le nettoyage a produit un résultat vide, retour de la réponse originale")
            return response.strip()
        
        return result
    
    def get_available_models(self) -> list:
        """
        Récupère la liste des modèles disponibles
        
        Returns:
            Liste des noms de modèles disponibles
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            data = response.json()
            models = [model.get('name', '') for model in data.get('models', [])]
            
            return models
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des modèles: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Télécharge un modèle si nécessaire
        
        Args:
            model_name: Nom du modèle à télécharger
            
        Returns:
            True si le téléchargement a réussi, False sinon
        """
        try:
            payload = {"name": model_name}
            
            self.logger.info(f"Téléchargement du modèle {model_name}...")
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json=payload,
                stream=True
            )
            response.raise_for_status()
            
            # Traitement du stream de téléchargement
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        status = data.get('status', '')
                        if 'pulling' in status.lower():
                            self.logger.debug(status)
                        elif 'success' in status.lower():
                            self.logger.info(f"Modèle {model_name} téléchargé avec succès")
                            return True
                    except json.JSONDecodeError:
                        continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors du téléchargement du modèle {model_name}: {e}")
            return False