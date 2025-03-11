import streamlit as st
import os
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import re
from utils.text_processor import extract_key_concepts, generate_quiz
from utils.pdf_extractor import extract_text_from_pdf
from utils.deepseek_api import generate_quiz_from_text

# Configuration de la page
st.set_page_config(
    page_title="QuizPrep - Votre assistant de révision",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation des dossiers de données
if not os.path.exists("data/notes"):
    os.makedirs("data/notes")
if not os.path.exists("data/quiz_history"):
    os.makedirs("data/quiz_history")

# Fonctions utilitaires pour la sauvegarde et le chargement des notes
def save_note(title, content):
    filename = f"data/notes/{title.replace(' ', '_')}.json"
    data = {
        "title": title,
        "content": content,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return filename

def load_notes():
    notes = []
    for filename in os.listdir("data/notes"):
        if filename.endswith(".json"):
            with open(f"data/notes/{filename}", "r", encoding="utf-8") as f:
                note = json.load(f)
                notes.append(note)
    return notes

def save_quiz_result(note_title, questions, answers, scores):
    filename = f"data/quiz_history/{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    data = {
        "note_title": note_title,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "questions": questions,
        "answers": answers,
        "scores": scores,
        "average_score": sum(scores) / len(scores) if scores else 0
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return filename

def load_quiz_history():
    history = []
    for filename in os.listdir("data/quiz_history"):
        if filename.endswith(".json"):
            with open(f"data/quiz_history/{filename}", "r", encoding="utf-8") as f:
                quiz = json.load(f)
                history.append(quiz)
    return history

# Fonction pour nettoyer les balises HTML et formater les questions
def clean_html_tags(text):
    # Remplacer les balises courantes par du texte en gras ou en italique pour Markdown
    text = text.replace('<strong>', '**').replace('</strong>', '**')
    text = text.replace('<b>', '**').replace('</b>', '**')
    text = text.replace('<em>', '*').replace('</em>', '*')
    text = text.replace('<i>', '*').replace('</i>', '*')
    
    # Nettoyer les balises span avec des classes spécifiques
    # Pour span avec classe spécifique, gardez le texte mais supprimez les balises
    text = re.sub(r'<span[^>]*class=["\'](code|method|attribute|tag)["\'][^>]*>', '`', text)
    text = re.sub(r'</span>', '`', text)
    
    # Pour d'autres balises span, simplement supprimez-les
    text = re.sub(r'<span[^>]*>', '', text)
    text = re.sub(r'</span>', '', text)
    
    # Supprimez toutes les autres balises HTML
    text = re.sub(r'<[^>]*>', '', text)
    
    return text

# État de session
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'current_note' not in st.session_state:
    st.session_state.current_note = None
if 'quiz_questions' not in st.session_state:
    st.session_state.quiz_questions = []
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = []
if 'quiz_scores' not in st.session_state:
    st.session_state.quiz_scores = []

# Barre latérale
with st.sidebar:
    st.title("📚 QuizPrep")
    
    # Navigation
    st.subheader("Navigation")
    if st.button("🏠 Accueil", use_container_width=True):
        st.session_state.page = 'home'
    if st.button("📝 Gestion des Notes", use_container_width=True):
        st.session_state.page = 'notes'
    if st.button("❓ Mode Quiz", use_container_width=True):
        st.session_state.page = 'quiz'
    if st.button("📊 Statistiques", use_container_width=True):
        st.session_state.page = 'stats'
    
    st.divider()
    st.caption("Développé avec ❤️ pour optimiser vos révisions")

# Page d'accueil
def show_home_page():
    st.title("Bienvenue sur QuizPrep 📚")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Comment ça marche")
        st.markdown("""
        1. **Ajoutez vos notes** en texte brut ou importez un PDF
        2. **Générez des quiz** basés sur vos notes
        3. **Évaluez votre compréhension** et suivez vos progrès
        """)
        
        if st.button("Commencer maintenant →", type="primary", use_container_width=True):
            st.session_state.page = 'notes'
    
    with col2:
        st.header("Statistiques rapides")
        notes = load_notes()
        quizzes = load_quiz_history()
        
        st.metric("Notes enregistrées", len(notes))
        st.metric("Quiz complétés", len(quizzes))
        if quizzes:
            avg_score = sum([q["average_score"] for q in quizzes]) / len(quizzes)
            st.metric("Score moyen", f"{avg_score:.2f}/5")

# Page de gestion des notes
def show_notes_page():
    st.title("📝 Gestion des Notes")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Notes existantes")
        notes = load_notes()
        
        if not notes:
            st.info("Aucune note trouvée. Créez votre première note!")
        
        for note in notes:
            if st.button(f"📄 {note['title']}", key=f"note_{note['title']}", use_container_width=True):
                st.session_state.current_note = note
    
    with col2:
        tab1, tab2 = st.tabs(["Nouvelle note", "Importer un PDF"])
        
        with tab1:
            note_title = st.text_input("Titre de la note", value="" if not st.session_state.current_note else st.session_state.current_note.get('title', ''))
            note_content = st.text_area("Contenu de la note", height=300, value="" if not st.session_state.current_note else st.session_state.current_note.get('content', ''))
            
            if st.button("Enregistrer la note", type="primary"):
                if note_title and note_content:
                    save_note(note_title, note_content)
                    st.success(f"Note '{note_title}' enregistrée avec succès!")
                    st.session_state.current_note = None
                    st.rerun()
                else:
                    st.error("Veuillez remplir le titre et le contenu de la note.")
        
        with tab2:
            uploaded_file = st.file_uploader("Choisir un fichier PDF", type="pdf")
            if uploaded_file is not None:
                pdf_title = st.text_input("Titre de la note pour ce PDF")
                
                if st.button("Extraire le texte et enregistrer"):
                    try:
                        text_content = extract_text_from_pdf(uploaded_file)
                        if pdf_title and text_content:
                            save_note(pdf_title, text_content)
                            st.success(f"PDF importé et enregistré sous '{pdf_title}'!")
                            st.session_state.current_note = None
                            st.rerun()
                        else:
                            st.error("Veuillez fournir un titre et vérifier que le PDF contient du texte.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'extraction du PDF: {str(e)}")

# Page de quiz
def show_quiz_page():
    st.title("❓ Mode Quiz")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Choisir une note")
        notes = load_notes()
        
        if not notes:
            st.info("Aucune note trouvée. Créez une note d'abord!")
            return
        
        note_titles = [note["title"] for note in notes]
        selected_note_title = st.selectbox("Sélectionner une note pour générer un quiz", note_titles)
        
        selected_note = next((note for note in notes if note["title"] == selected_note_title), None)
        
        if selected_note:
            num_questions = st.slider("Nombre de questions", min_value=3, max_value=10, value=5)
            
            if st.button("Générer un quiz", type="primary"):
                with st.spinner("Génération du quiz en cours..."):
                    try:
                        # Utiliser l'API Deepseek pour générer des questions
                        questions = generate_quiz_from_text(selected_note["content"], num_questions)
                        
                        # Assurer que le format des questions est correct
                        formatted_questions = []
                        
                        # Si questions est un dictionnaire avec une clé 'questions'
                        if isinstance(questions, dict) and 'questions' in questions:
                            formatted_questions = questions['questions']
                        # Si questions est déjà une liste
                        elif isinstance(questions, list):
                            # Vérifier si chaque élément est un dictionnaire ou une chaîne
                            if all(isinstance(q, dict) for q in questions):
                                # Si ce sont des dictionnaires, extraire la question
                                formatted_questions = [q.get('question', str(q)) for q in questions]
                            else:
                                # Si ce sont déjà des chaînes ou autre chose, les convertir en chaînes
                                formatted_questions = [str(q) for q in questions]
                        # Si c'est une chaîne contenant plusieurs questions
                        elif isinstance(questions, str):
                            # Diviser la chaîne en questions séparées
                            questions_split = questions.split('\n\n')
                            formatted_questions = [q.strip() for q in questions_split if q.strip()]
                        
                        # S'assurer qu'on a au moins une question
                        if not formatted_questions:
                            st.error("Aucune question n'a pu être générée. Essayez avec un contenu plus détaillé.")
                            return
                        
                        # Nettoyer les balises HTML dans chaque question
                        cleaned_questions = [clean_html_tags(q) for q in formatted_questions]
                            
                        st.session_state.quiz_questions = cleaned_questions
                        st.session_state.quiz_answers = [""] * len(cleaned_questions)
                        st.session_state.quiz_scores = [0] * len(cleaned_questions)
                        st.session_state.current_note = selected_note
                        
                    except Exception as e:
                        st.error(f"Erreur lors de la génération du quiz: {str(e)}")
                        return
                        
                st.success("Quiz généré avec succès!")
                st.rerun()
    
    with col2:
        if st.session_state.quiz_questions:
            st.subheader(f"Quiz sur: {st.session_state.current_note['title']}")
            
            # Afficher les questions et collecter les réponses
            for i, question in enumerate(st.session_state.quiz_questions):
                # Utiliser markdown pour rendre l'affichage plus propre
                st.markdown(f"**Question {i+1}:** {question}")
                
                answer = st.text_area(f"Votre réponse #{i+1}", 
                                     value=st.session_state.quiz_answers[i], 
                                     key=f"answer_{i}")
                
                st.session_state.quiz_answers[i] = answer
                
                # Système de notation
                score = st.slider(f"Auto-évaluation #{i+1} (0-5)", 
                                 min_value=0, max_value=5, 
                                 value=st.session_state.quiz_scores[i],
                                 key=f"score_{i}")
                
                st.session_state.quiz_scores[i] = score
                st.divider()
            
            if st.button("Enregistrer les résultats", type="primary"):
                save_quiz_result(
                    st.session_state.current_note["title"],
                    st.session_state.quiz_questions,
                    st.session_state.quiz_answers,
                    st.session_state.quiz_scores
                )
                st.success("Résultats enregistrés avec succès!")
                st.balloons()
                
                # Réinitialiser le quiz
                st.session_state.quiz_questions = []
                st.session_state.quiz_answers = []
                st.session_state.quiz_scores = []

# Page de statistiques
def show_stats_page():
    st.title("📊 Suivi des Performances")
    
    quiz_history = load_quiz_history()
    
    if not quiz_history:
        st.info("Pas encore d'historique de quiz. Complétez un quiz pour voir vos statistiques!")
        return
    
    # Préparation des données
    df = pd.DataFrame([
        {
            "Date": quiz["date"],
            "Note": quiz["note_title"],
            "Score moyen": quiz["average_score"],
            "Nombre de questions": len(quiz["questions"])
        }
        for quiz in quiz_history
    ])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Score moyen global")
        average_score = df["Score moyen"].mean()
        st.metric("Score moyen", f"{average_score:.2f}/5")
        
        # Afficher un graphique d'évolution des scores
        st.subheader("Évolution des scores")
        df_sorted = df.sort_values("Date")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(df_sorted["Date"], df_sorted["Score moyen"], marker='o')
        ax.set_xlabel("Date")
        ax.set_ylabel("Score moyen")
        ax.set_ylim(0, 5)
        ax.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        st.pyplot(fig)
    
    with col2:
        st.subheader("Scores par note")
        
        # Grouper par note
        note_scores = df.groupby("Note")["Score moyen"].mean().reset_index()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(note_scores["Note"], note_scores["Score moyen"])
        ax.set_xlabel("Notes")
        ax.set_ylabel("Score moyen")
        ax.set_ylim(0, 5)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        st.pyplot(fig)
    
    st.subheader("Historique détaillé des quiz")
    st.dataframe(df)

# Affichage de la page en fonction de l'état
if st.session_state.page == 'home':
    show_home_page()
elif st.session_state.page == 'notes':
    show_notes_page()
elif st.session_state.page == 'quiz':
    show_quiz_page()
elif st.session_state.page == 'stats':
    show_stats_page()