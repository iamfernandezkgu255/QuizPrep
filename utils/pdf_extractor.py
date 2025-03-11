"""
Utilitaires pour l'extraction de texte à partir de fichiers PDF
"""

import io
import re
import PyPDF2
from PIL import Image
import pytesseract

def extract_text_from_pdf(pdf_file):
    """
    Extrait le texte d'un fichier PDF, qu'il s'agisse de texte sélectionnable
    ou d'images contenant du texte (OCR).
    
    Args:
        pdf_file: Objet fichier chargé via st.file_uploader
        
    Returns:
        str: Le texte extrait du PDF
    """
    # Convertir en objet BytesIO pour PyPDF2
    pdf_bytes = io.BytesIO(pdf_file.read())
    
    # Réinitialiser le pointeur du fichier (important)
    pdf_bytes.seek(0)
    
    extracted_text = ""
    
    try:
        # Ouvrir le PDF avec PyPDF2
        pdf_reader = PyPDF2.PdfReader(pdf_bytes)
        num_pages = len(pdf_reader.pages)
        
        # Parcourir chaque page
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text() or ""
            
            # Si peu ou pas de texte est extrait, c'est peut-être une image
            if len(page_text.strip()) < 50:
                # TODO: Implémenter l'OCR si nécessaire
                # Cette partie nécessite l'installation de Tesseract OCR
                pass
            
            extracted_text += page_text + "\n\n"
        
        # Nettoyer le texte
        extracted_text = clean_pdf_text(extracted_text)
        
        return extracted_text
    
    except Exception as e:
        raise Exception(f"Erreur lors de l'extraction du texte: {str(e)}")

def clean_pdf_text(text):
    """
    Nettoie le texte extrait d'un PDF en supprimant les caractères spéciaux
    et en normalisant les espaces, sauts de ligne, etc.
    
    Args:
        text (str): Texte à nettoyer
        
    Returns:
        str: Texte nettoyé
    """
    # Remplacer les sauts de ligne multiples par un seul
    text = re.sub(r'\n+', '\n', text)
    
    # Supprimer les caractères non imprimables
    text = ''.join(c for c in text if c.isprintable() or c == '\n')
    
    # Normaliser les espaces
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+\n', '\n', text)
    text = re.sub(r'\n\s+', '\n', text)
    
    # Supprimer les numéros de page isolés
    text = re.sub(r'\n\d+\n', '\n', text)
    
    return text.strip()

def extract_text_from_image(image_data):
    """
    Utilise OCR pour extraire du texte d'une image
    Nécessite l'installation de Tesseract OCR
    
    Args:
        image_data (bytes): Données de l'image
        
    Returns:
        str: Texte extrait de l'image
    """
    try:
        # Convertir les bytes en image PIL
        image = Image.open(io.BytesIO(image_data))
        
        # Appliquer l'OCR (français)
        text = pytesseract.image_to_string(image, lang='fra')
        
        return text
    except Exception as e:
        print(f"Erreur lors de l'OCR: {str(e)}")
        return ""