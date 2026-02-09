#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
APPLICATION WEB - RÉSUMEUR DE VIDÉOS YOUTUBE
Interface mobile-friendly avec Streamlit
"""

import streamlit as st
import requests
import json
import re
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="🎬 Résumeur YouTube",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé pour mobile
st.markdown("""
<style>
    /* Style général */
    .main {
        padding: 1rem;
    }
    
    /* Titres plus grands */
    h1 {
        font-size: 2rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Texte du résumé plus grand et lisible */
    .resume-text {
        font-size: 1.1rem !important;
        line-height: 1.8 !important;
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* Boutons plus grands pour mobile */
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.1rem !important;
        margin: 0.5rem 0;
    }
    
    /* Input plus grands */
    .stTextInput > div > div > input {
        font-size: 1.1rem !important;
        height: 3rem;
    }
    
    /* Radio buttons plus grands */
    .stRadio > div {
        font-size: 1.1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Credenciales
OPENAI_API_KEY = "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"

# Modèles disponibles
MODELOS = {
    "Mistral Large (Français) 🇫🇷": {
        "id": "mistralai/mistral-large-2411",
        "cost": "~0.002€"
    },
    "Llama 3.1 70B": {
        "id": "meta-llama/llama-3.1-70b-instruct",
        "cost": "~0.001€"
    },
    "Claude 3.5 Sonnet (Premium) ⭐": {
        "id": "anthropic/claude-3.5-sonnet",
        "cost": "~0.01€"
    }
}

# ===============================
# FONCTIONS
# ===============================

def extraer_video_id(url):
    """Extrait l'ID de la vidéo YouTube"""
    patrones = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)',
    ]
    
    for patron in patrones:
        match = re.search(patron, url)
        if match:
            return match.group(1)
    
    if len(url) == 11 and not '/' in url:
        return url
    
    return None

def obtener_transcripcion(video_id):
    """Obtient la transcription de la vidéo"""
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        
        available_transcripts = []
        for transcript in transcript_list:
            available_transcripts.append(transcript)
        
        if not available_transcripts:
            return None, "Aucune transcription disponible"
        
        priority_codes = ['fr', 'fr-FR', 'en', 'en-US', 'es', 'es-ES']
        
        for priority_lang in priority_codes:
            for transcript in available_transcripts:
                try:
                    if transcript.language_code.lower() == priority_lang.lower():
                        transcript_data = transcript.fetch()
                        
                        if transcript_data and len(transcript_data) > 0:
                            texto = " ".join([entry.text for entry in transcript_data])
                            texto = texto.replace('\n', ' ').strip()
                            return texto, None
                except:
                    continue
        
        for transcript in available_transcripts:
            try:
                transcript_data = transcript.fetch()
                if transcript_data and len(transcript_data) > 0:
                    texto = " ".join([entry.text for entry in transcript_data])
                    texto = texto.replace('\n', ' ').strip()
                    return texto, None
            except:
                continue
                
    except Exception as e:
        return None, f"Erreur: {str(e)}"
    
    return None, "Impossible d'obtenir la transcription"

def generar_resumen(transcripcion, modelo_id):
    """Génère le résumé avec l'IA"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Tu es un expert en synthèse de contenu vidéo. Analyse la transcription suivante et crée un résumé détaillé en français.

TRANSCRIPTION:
{transcripcion}

INSTRUCTIONS:
1. Crée un résumé DÉTAILLÉ et STRUCTURÉ en français
2. Utilise des bullets points hiérarchiques (• pour les points principaux, - pour les sous-points)
3. Adapte la longueur du résumé à la richesse du contenu (généralement 10-20 points principaux)
4. Pour les vidéos financières/business, inclus:
   - Thèse d'investissement principale
   - Chiffres clés et métriques importantes
   - Forces et faiblesses identifiées
   - Recommandations ou conclusions
5. Pour les autres types de vidéos, structure selon le contenu
6. Sois précis et facile à lire
7. Garde les informations importantes (noms, chiffres, dates)

Réponds UNIQUEMENT avec le résumé en bullets, sans introduction ni conclusion."""

    payload = {
        "model": modelo_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code != 200:
            return None, f"Erreur HTTP {response.status_code}"
        
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            resumen = data["choices"][0]["message"]["content"].strip()
            return resumen, None
        else:
            return None, "Réponse API invalide"
            
    except Exception as e:
        return None, f"Erreur: {str(e)}"

# ===============================
# INTERFACE STREAMLIT
# ===============================

# Titre
st.title("🎬 Résumeur YouTube")
st.markdown("**Transformez n'importe quelle vidéo YouTube en résumé détaillé en français**")

# Séparateur
st.markdown("---")

# Étape 1 : URL
st.subheader("1️⃣ URL de la vidéo")
url_input = st.text_input(
    "Collez l'URL YouTube ici",
    placeholder="https://www.youtube.com/watch?v=...",
    help="Formats acceptés: youtube.com/watch?v=, youtu.be/, ou l'ID direct"
)

# Étape 2 : Choix du modèle
st.subheader("2️⃣ Choisissez le modèle IA")
modelo_seleccionado = st.radio(
    "Modèle",
    options=list(MODELOS.keys()),
    format_func=lambda x: f"{x} ({MODELOS[x]['cost']})",
    help="Mistral Large est recommandé pour le français"
)

# Bouton de génération
st.markdown("---")
generar_button = st.button("🚀 Générer le résumé", type="primary", use_container_width=True)

# Traitement
if generar_button:
    if not url_input:
        st.error("⚠️ Veuillez entrer une URL YouTube")
    else:
        # Extraire video ID
        video_id = extraer_video_id(url_input)
        
        if not video_id:
            st.error("❌ URL invalide. Vérifiez le format.")
        else:
            # Afficher le lien de la vidéo
            st.success(f"✅ Video ID: `{video_id}`")
            st.markdown(f"[🔗 Voir la vidéo](https://www.youtube.com/watch?v={video_id})")
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Étape 1: Transcription
            status_text.text("📥 Récupération de la transcription...")
            progress_bar.progress(33)
            
            transcripcion, error = obtener_transcripcion(video_id)
            
            if error:
                st.error(f"❌ {error}")
                st.info("💡 Astuce: Vérifiez que la vidéo a des sous-titres disponibles")
            else:
                st.success(f"✅ Transcription obtenue ({len(transcripcion)} caractères)")
                
                # Étape 2: Génération du résumé
                status_text.text("🤖 Génération du résumé par IA...")
                progress_bar.progress(66)
                
                modelo_id = MODELOS[modelo_seleccionado]["id"]
                resumen, error = generar_resumen(transcripcion, modelo_id)
                
                if error:
                    st.error(f"❌ {error}")
                else:
                    progress_bar.progress(100)
                    status_text.text("✅ Terminé!")
                    
                    # Afficher le résumé
                    st.markdown("---")
                    st.subheader("📄 Résumé de la vidéo")
                    
                    # Résumé dans une zone scrollable
                    st.markdown(f'<div class="resume-text">{resumen}</div>', unsafe_allow_html=True)
                    
                    # Boutons d'action
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Bouton copier
                        if st.button("📋 Copier", use_container_width=True):
                            st.code(resumen, language=None)
                            st.info("👆 Sélectionnez et copiez le texte ci-dessus")
                    
                    with col2:
                        # Bouton télécharger
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"resume_{video_id}_{timestamp}.txt"
                        
                        contenu_archivo = f"""RÉSUMÉ DE VIDÉO YOUTUBE
{"="*70}

Video ID: {video_id}
URL: https://www.youtube.com/watch?v={video_id}
Modèle IA: {modelo_seleccionado}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{"="*70}
RÉSUMÉ
{"="*70}

{resumen}

{"="*70}
"""
                        
                        st.download_button(
                            label="💾 Télécharger",
                            data=contenu_archivo,
                            file_name=filename,
                            mime="text/plain",
                            use_container_width=True
                        )
                    
                    # Bouton partager WhatsApp (mobile)
                    whatsapp_text = f"*Résumé YouTube*\n\n{resumen}\n\n🔗 {url_input}"
                    whatsapp_url = f"https://wa.me/?text={requests.utils.quote(whatsapp_text)}"
                    
                    st.markdown(f"""
                    <a href="{whatsapp_url}" target="_blank">
                        <button style="
                            width: 100%;
                            height: 3rem;
                            background-color: #25D366;
                            color: white;
                            border: none;
                            border-radius: 5px;
                            font-size: 1.1rem;
                            cursor: pointer;
                            margin-top: 0.5rem;
                        ">
                            💬 Partager sur WhatsApp
                        </button>
                    </a>
                    """, unsafe_allow_html=True)
                    
                    # Statistiques
                    st.markdown("---")
                    st.caption(f"📊 Statistiques: {len(transcripcion)} caractères → {len(resumen)} caractères (compression {100 - (len(resumen)/len(transcripcion)*100):.1f}%)")

# Footer
st.markdown("---")
st.caption("💡 Astuce: Sauvegardez cette page dans vos favoris pour un accès rapide!")
