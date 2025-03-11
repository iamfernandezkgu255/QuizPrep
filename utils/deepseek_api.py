"""
Utilitaires pour l'intégration avec l'API Deepseek via OpenRouter
"""

import re
import requests
import json
import os
import sys
import time
from config import OPENROUTER_API_KEY, OPENROUTER_API_URL, DEEPSEEK_MODEL, API_CONFIG

def call_deepseek_api(prompt, system_prompt=""):
    """
    Appelle l'API Deepseek via OpenRouter
    
    Args:
        prompt (str): Le message à envoyer à l'API
        system_prompt (str): Instructions système optionnelles
        
    Returns:
        str: La réponse de l'API
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("Clé API OpenRouter manquante. Veuillez configurer votre clé API dans config.py")
    
    # Préparer les headers
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Préparer le payload
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt} if system_prompt else {},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": API_CONFIG["max_tokens"],
        "temperature": API_CONFIG["temperature"],
        "top_p": API_CONFIG["top_p"],
        "frequency_penalty": API_CONFIG["frequency_penalty"],
        "presence_penalty": API_CONFIG["presence_penalty"]
    }
    
    # Nettoyer les messages vides
    payload["messages"] = [msg for msg in payload["messages"] if msg]
    
    try:
        # Faire la requête API
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Lever une exception pour les erreurs HTTP
        
        # Extraire la réponse
        response_json = response.json()
        
        if "choices" in response_json and len(response_json["choices"]) > 0:
            return response_json["choices"][0]["message"]["content"]
        else:
            raise ValueError("Format de réponse API invalide")
            
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel à l'API: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Détails: {e.response.text}")
        
        # Retourner un message d'erreur formaté
        return "Erreur de communication avec l'API. Veuillez vérifier votre connexion et votre clé API."
    
    except Exception as e:
        print(f"Erreur inattendue: {str(e)}")
        return "Une erreur inattendue s'est produite."

def generate_quiz_from_text(text, num_questions=5):
    """
    Génère un quiz à partir d'un texte en utilisant l'API Deepseek
    
    Args:
        text (str): Le texte source pour le quiz
        num_questions (int): Le nombre de questions à générer
        
    Returns:
        list: Liste des questions générées
    """
    # Si le texte est trop long, le tronquer
    max_text_length = 4000  # Ajustez selon les limites de l'API
    if len(text) > max_text_length:
        text = text[:max_text_length] + "..."
    
    system_prompt = f"""
    Vous êtes un expert en pédagogie qui aide à créer des quiz éducatifs.
    Votre tâche est de générer {num_questions} questions pertinentes à partir du texte fourni.
    
    Consignes:
    1. Créez des questions qui testent la compréhension profonde des concepts, pas la mémorisation simple
    2. Formulez des questions ouvertes qui nécessitent des réponses détaillées
    3. Concentrez-vous sur les concepts clés et les idées principales du texte
    4. Variez les types de questions (explication, comparaison, analyse, application)
    5. Retournez uniquement la liste des questions, sans autre texte
    6. Les questions doivent être en français
    """
    
    prompt = f"""
    Voici le texte pour lequel vous devez créer un quiz de {num_questions} questions:
    
    {text}
    
    Générez exactement {num_questions} questions pertinentes pour évaluer la compréhension de ce texte.
    """
    
    try:
        response = call_deepseek_api(prompt, system_prompt)
        
        # Nettoyer et parser la réponse pour extraire les questions
        questions = parse_questions_from_response(response, num_questions)
        
        # Si nous n'avons pas assez de questions, compléter avec des questions génériques
        while len(questions) < num_questions:
            questions.append(f"Question supplémentaire: Résumez un des concepts clés du texte.")
        
        return questions[:num_questions]  # S'assurer qu'on a exactement le nombre demandé
        
    except Exception as e:
        print(f"Erreur lors de la génération du quiz: {str(e)}")
        
        # En cas d'erreur, générer des questions génériques
        return [f"Question {i+1}: Expliquez un des concepts importants présentés dans le texte." 
                for i in range(num_questions)]

def parse_questions_from_response(response, expected_count):
    """
    Parse la réponse de l'API pour extraire les questions
    
    Args:
        response (str): La réponse brute de l'API
        expected_count (int): Le nombre de questions attendu
        
    Returns:
        list: Liste des questions extraites
    """
    # Diviser la réponse en lignes
    lines = response.strip().split('\n')
    
    # Filtrer les lignes qui semblent être des questions
    questions = []
    
    for line in lines:
        line = line.strip()
        
        # Ignorer les lignes vides
        if not line:
            continue
            
        # Patterns communs pour les questions
        if (line.startswith("Question") or 
            line.startswith("Q") or 
            line.startswith("-") or 
            line.startswith("*") or
            line.startswith("#") or
            line.startswith("1") or
            line.startswith("2")):
            
            # Nettoyer la question
            # Supprimer les préfixes numériques, tirets, etc.
            clean_line = re.sub(r'^[Q0-9#\-\*\.]+\.?\s*', '', line)
            clean_line = re.sub(r'^Question\s*[0-9]+\s*[:\.]\s*', '', clean_line)
            
            # Ajouter à la liste si non vide
            if clean_line:
                questions.append(clean_line)
    
    # Si le parsing n'a pas fonctionné, essayer une approche plus simple
    if len(questions) < expected_count / 2:
        # Diviser par lignes vides
        chunks = re.split(r'\n\s*\n', response)
        questions = [chunk.strip() for chunk in chunks if chunk.strip()]
    
    return questions