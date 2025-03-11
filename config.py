# Configuration de l'application et clés API

# Clé API OpenRouter pour accéder à Deepseek
# IMPORTANT: Pour des raisons de sécurité, ne stockez pas directement votre clé API dans ce fichier.
# Utilisez des variables d'environnement ou un fichier .env
# OPENROUTER_API_KEY = "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"  # À remplacer par votre clé API
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Récupération sécurisée de la clé API depuis les variables d'environnement
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# URL de l'API OpenRouter
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Modèle Deepseek à utiliser
DEEPSEEK_MODEL = "deepseek/deepseek-r1-zero:free"

# Configuration des requêtes API
API_CONFIG = {
    "max_tokens": 2048,
    "temperature": 0.7,
    "top_p": 0.9,
    "frequency_penalty": 0,
    "presence_penalty": 0
}

# Nombre maximum de questions par défaut
DEFAULT_MAX_QUESTIONS = 10

# Chemins des dossiers de données
DATA_FOLDER = "data"
NOTES_FOLDER = os.path.join(DATA_FOLDER, "notes")
QUIZ_HISTORY_FOLDER = os.path.join(DATA_FOLDER, "quiz_history")

# Création des répertoires s'ils n'existent pas
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(NOTES_FOLDER, exist_ok=True)
os.makedirs(QUIZ_HISTORY_FOLDER, exist_ok=True)

# Configuration des types de contenu supportés
SUPPORTED_FILE_TYPES = ["pdf", "txt"]