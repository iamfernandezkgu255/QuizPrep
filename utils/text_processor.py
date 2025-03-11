"""
Utilitaires pour le traitement de texte et la génération de quiz
"""

import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# Télécharger les ressources NLTK nécessaires (à exécuter la première fois)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

def clean_text(text):
    """
    Nettoie le texte brut (enlève les caractères spéciaux, normalise les espaces, etc.)
    """
    # Remplacer les sauts de ligne multiples par un seul
    text = re.sub(r'\n+', '\n', text)
    
    # Remplacer les espaces multiples par un seul
    text = re.sub(r'\s+', ' ', text)
    
    # Normaliser les tirets
    text = re.sub(r'[–—]', '-', text)
    
    return text.strip()

def extract_key_concepts(text, num_concepts=10):
    """
    Extrait les concepts clés d'un texte en identifiant les termes les plus fréquents
    (hors mots vides comme "le", "la", "et", etc.)
    
    Args:
        text (str): Le texte à analyser
        num_concepts (int): Le nombre de concepts à extraire
        
    Returns:
        list: Liste de tuples (concept, fréquence)
    """
    text = clean_text(text)
    
    # Tokenization
    words = word_tokenize(text.lower(), language='french')
    
    # Filtrer les mots vides
    french_stopwords = set(stopwords.words('french'))
    filtered_words = [word for word in words if word.isalnum() and word not in french_stopwords and len(word) > 2]
    
    # Compter les fréquences
    word_freq = {}
    for word in filtered_words:
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1
    
    # Trier par fréquence et prendre les N premiers
    sorted_concepts = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_concepts[:num_concepts]

def extract_sentences_with_concept(text, concept):
    """
    Extrait les phrases contenant un concept spécifique
    
    Args:
        text (str): Le texte à analyser
        concept (str): Le concept à rechercher
        
    Returns:
        list: Liste des phrases contenant le concept
    """
    text = clean_text(text)
    sentences = sent_tokenize(text, language='french')
    
    # Rechercher les phrases contenant le concept (insensible à la casse)
    pattern = re.compile(r'\b' + re.escape(concept) + r'\b', re.IGNORECASE)
    matching_sentences = [s for s in sentences if pattern.search(s)]
    
    return matching_sentences

def generate_quiz(text, num_questions=5):
    """
    Génère un quiz simple basé sur le texte fourni
    REMARQUE: Cette fonction est un placeholder. L'implémentation réelle 
    devrait utiliser l'API Deepseek pour une génération plus intelligente.
    
    Args:
        text (str): Le texte source pour générer le quiz
        num_questions (int): Le nombre de questions à générer
        
    Returns:
        list: Liste de questions générées
    """
    text = clean_text(text)
    
    # Extraire les concepts clés
    key_concepts = extract_key_concepts(text, num_concepts=num_questions*2)
    
    questions = []
    for i, (concept, _) in enumerate(key_concepts):
        if i >= num_questions:
            break
            
        # Trouver des phrases mentionnant le concept
        relevant_sentences = extract_sentences_with_concept(text, concept)
        
        if relevant_sentences:
            # Créer une question simple sur ce concept
            questions.append(f"Expliquez le concept de '{concept}' tel qu'il est présenté dans le texte.")
    
    # Si nous n'avons pas assez de questions, ajouter des questions génériques
    while len(questions) < num_questions:
        questions.append(f"Résumez la partie du texte qui traite des points clés.")
    
    return questions