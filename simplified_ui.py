#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Componenti UI semplificati per il Business Plan Builder.

Questo modulo fornisce funzioni helper per creare un'interfaccia utente
semplificata e facile da usare, adatta a utenti di livello scuola media.
"""

import streamlit as st
import html
from typing import List, Dict, Any, Optional, Tuple, Callable

# Funzione per creare uno step del wizard
def wizard_step(step_number: int, title: str, active: bool = False, description: str = None):
    """
    Crea un container per uno step del wizard.
    
    Args:
        step_number: Numero dello step
        title: Titolo dello step
        active: Se lo step è attivo
        description: Breve descrizione dello step (opzionale)
        
    Returns:
        Container di Streamlit per lo step
    """
    class_name = "simple-wizard-step active" if active else "simple-wizard-step"
    emoji_map = {
        "Informazioni di Base": "📋",
        "Carica Documenti": "📤",
        "Definisci Obiettivi": "🎯",
        "Crea Piano": "📝",
        "Analisi Finanziaria": "💰",
        "Revisione": "✅",
        "Esportazione": "📤"
    }
    
    # Emoji predefinita se il titolo non è nella mappa
    emoji = emoji_map.get(title, "📌")
    
    with st.container(border=True):  # Aggiungo border=True per rendere lo step più visibile
        # Applica stile CSS personalizzato
        st.markdown(f"""
        <div class="{class_name}" style="margin-bottom: 10px;">
            <div style="display: flex; align-items: center;">
                <span style="background-color: {'#4CAF50' if active else '#6c757d'}; color: white; 
                       border-radius: 50%; width: 30px; height: 30px; display: flex; 
                       justify-content: center; align-items: center; margin-right: 12px;">
                    {step_number}
                </span>
                <span style="font-size: 1.2rem; font-weight: bold;">{emoji} {title}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Aggiungi descrizione se presente
        if description:
            st.markdown(f"""
            <div style="margin-top: 8px; margin-left: 42px; color: #666; font-size: 0.9rem;">
                {description}
            </div>
            """, unsafe_allow_html=True)
        
        # Aggiungi suggerimenti o esempi se lo step è attivo
        if active:
            tips = {
                "Informazioni di Base": "Inserisci i dati principali della tua azienda. Esempio: settore, anno di fondazione, numero dipendenti.",
                "Carica Documenti": "Carica documenti utili come business plan precedenti, bilanci o ricerche di mercato.",
                "Definisci Obiettivi": "Definisci obiettivi SMART: Specifici, Misurabili, Achievable, Realistici, con un Tempo definito.",
                "Crea Piano": "Descriveremo ogni sezione del tuo business plan con l'aiuto dell'IA.",
                "Analisi Finanziaria": "Inserisci i dati finanziari di base come ricavi e costi principali.",
                "Revisione": "Controlla ogni sezione e fai le modifiche necessarie.",
                "Esportazione": "Salva il tuo business plan in formato PDF o Word."
            }
            
            tip = tips.get(title, "Compila i campi richiesti in questo passaggio.")
            st.markdown(f"""
            <div style="margin-top: 10px; margin-left: 42px; background-color: #f8f9fa; 
                    padding: 10px; border-radius: 5px; border-left: 3px solid #4CAF50;">
                <span style="color: #4CAF50;">💡 Suggerimento:</span> {tip}
            </div>
            """, unsafe_allow_html=True)
        
        # Ritorna il contenuto all'interno del contenitore
        return st.container()
    
    # Chiudi il div
    st.markdown("</div>", unsafe_allow_html=True)

# Funzione per mostrare un tooltip di aiuto
def help_tip(text: str, expanded: bool = False):
    """
    Mostra un box di aiuto con spiegazioni semplici.
    
    Args:
        text: Testo di aiuto da mostrare
        expanded: Se il box deve essere già espanso
    """
    with st.expander("💡 Hai bisogno di aiuto?", expanded=expanded):
        st.markdown(f"""
        <div style="background-color: #fffbec; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
            <div style="font-size: 1.15rem; line-height: 1.5;">
                <p style="margin-bottom: 10px;"><span style="font-size: 1.3rem;">🔎</span> <strong>Suggerimento:</strong></p>
                <p style="margin-left: 10px; margin-top: 0;">{text}</p>
                <p style="margin-top: 15px; font-style: italic; font-size: 0.9rem;">💬 Se hai ancora dubbi, usa la chat di supporto in basso a destra.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Funzione per mostrare una zona di upload file migliorata
def upload_zone(title: str, instructions: str, upload_types=None, key=None):
    """
    Crea una zona di upload file con istruzioni chiare e animazione.
    
    Args:
        title: Titolo della zona di upload
        instructions: Istruzioni per l'upload
        upload_types: Lista di tipi di file consentiti
        key: Chiave per il componente Streamlit
        
    Returns:
        File caricato
    """
    if upload_types is None:
        upload_types = ["pdf", "docx", "txt", "csv", "xlsx"]
    
    # Mostra tipi di file supportati in modo chiaro
    supported_types_text = ", ".join([f".{t.upper()}" for t in upload_types])
    
    # Crea un box colorato per l'upload
    st.markdown(f"""
    <div style="border: 2px dashed #4CAF50; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 20px; background-color: #f0f9f0;">
        <h3 style="margin-top: 0;">{title}</h3>
        <p>{instructions}</p>
        <p style="font-size: 0.9rem; color: #555;">Formati supportati: {supported_types_text}</p>
        <div style="font-size: 40px; margin: 10px 0;">📄 ⬆️</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Aggiungi indicatore di caricamento
    with st.container():
        file = st.file_uploader("", type=upload_types, key=key)
        if file is not None:
            st.success(f"File '{file.name}' caricato con successo! ✅")
            
            # Aggiungi un'anteprima del file se possibile
            if file.type.startswith(('text/', 'application/json')):
                with st.expander("Anteprima del file", expanded=False):
                    try:
                        content = file.getvalue().decode('utf-8')
                        st.text_area("", value=content[:1000] + ("..." if len(content) > 1000 else ""), height=200)
                    except:
                        st.write("Impossibile mostrare l'anteprima di questo file.")
    
    return file

# Funzione per mostrare un indicatore di progresso
def progress_indicator(steps: List[str], current_step: int):
    """
    Mostra un indicatore di progresso per il wizard.
    
    Args:
        steps: Lista dei nomi degli step
        current_step: Indice dello step corrente (0-based)
    """
    total_steps = len(steps)
    current_width = 0
    
    if current_step > 0:
        # Calcola larghezza della barra di progresso (in percentuale)
        current_width = int((current_step / (total_steps - 1)) * 100)
    
    # Mostra la percentuale di completamento
    st.caption(f"Completamento: {current_width}%")
    
    # Usa il componente standard di progresso di Streamlit
    st.progress(current_width / 100)
    
    # Crea una visualizzazione più semplice e chiara degli step
    cols = st.columns(len(steps))
    for i, (col, step_name) in enumerate(zip(cols, steps)):
        with col:
            # Determina lo stile per ogni step
            if i < current_step:
                emoji = "✅"  # Completato
                color = "#28a745"
            elif i == current_step:
                emoji = "🔍"  # Attuale
                color = "#007bff" 
            else:
                emoji = "⏳"  # Da fare
                color = "#6c757d"
                
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 20px; margin-bottom: 5px;">{emoji}</div>
                <div style="font-size: 0.8rem; color: {color}; font-weight: {'bold' if i == current_step else 'normal'};">
                    {i+1}. {step_name}
                </div>
            </div>
            """, unsafe_allow_html=True)

# Funzione per creare un pulsante di azione principale
def action_button(label: str, key: str, help_text: str = None):
    """
    Crea un pulsante di azione principale stilizzato.
    
    Args:
        label: Etichetta del pulsante
        key: Chiave per Streamlit
        help_text: Testo di aiuto opzionale
        
    Returns:
        True se il pulsante è stato cliccato
    """
    col1, col2 = st.columns([4, 1])
    
    with col1:
        result = st.button(label, key=key, use_container_width=True, type="primary")
        st.markdown("""
        <style>
        div[data-testid="stButton"] > button {
            padding: 10px 16px !important;
            font-size: 1.1rem !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
            transition: transform 0.2s !important;
        }
        div[data-testid="stButton"] > button:hover {
            transform: translateY(-2px) !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    with col2:
        if help_text:
            st.info(help_text)
    
    return result

# Funzione per creare una scheda informativa
def info_card(title: str, content: str, icon: str = "ℹ️", color: str = "#3182ce"):
    """
    Mostra una scheda informativa.
    
    Args:
        title: Titolo della scheda
        content: Contenuto della scheda
        icon: Icona da mostrare
        color: Colore principale della scheda (default: blu)
    """
    # Crea una versione più chiara del colore per lo sfondo
    bg_color = f"{color}15"  # 15% di opacità
    border_color = f"{color}30"  # 30% di opacità
    
    st.markdown(f"""
    <div style="border: 1px solid {border_color}; border-radius: 10px; padding: 18px; 
         margin: 15px 0; background-color: {bg_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
        <h3 style="margin-top: 0; color: {color}; font-size: 1.2rem; display: flex; align-items: center;">
            <span style="font-size: 1.5rem; margin-right: 10px;">{icon}</span>
            <span>{title}</span>
        </h3>
        <p style="margin-bottom: 0; font-size: 1rem; line-height: 1.6; color: #333;">{content}</p>
    </div>
    """, unsafe_allow_html=True)

# Funzione per creare una scheda con suggerimenti per il successo
def success_tips(tips: List[str]):
    """
    Mostra una lista di suggerimenti per il successo.
    
    Args:
        tips: Lista di suggerimenti
    """
    html_tips = ""
    for i, tip in enumerate(tips):
        emoji = ["💡", "🎯", "✨", "🚀", "⭐"][i % 5]  # Rotazione di 5 emoji diverse
        html_tips += f"""
        <div style="display: flex; margin-bottom: 12px; align-items: flex-start;">
            <div style="font-size: 1.2rem; margin-right: 10px; color: #2C7A39;">{emoji}</div>
            <div style="flex: 1;">{tip}</div>
        </div>
        """
    
    st.markdown(f"""
    <div style="border: 1px solid #c6e9c9; border-radius: 10px; padding: 18px; 
         margin: 15px 0; background-color: #f0fff4; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <h3 style="margin-top: 0; color: #2C7A39; font-size: 1.25rem; display: flex; align-items: center;">
            <span style="font-size: 1.4rem; margin-right: 10px;">✅</span>
            <span>Suggerimenti per il Successo</span>
        </h3>
        <div style="margin-top: 15px;">
            {html_tips}
        </div>
        <div style="margin-top: 10px; font-style: italic; color: #666; font-size: 0.9rem; text-align: right;">
            Segui questi consigli per ottenere risultati migliori!
        </div>
    </div>
    """, unsafe_allow_html=True)

# Funzione per creare una scheda con esempi
def example_card(title: str, examples: Dict[str, str]):
    """
    Mostra una scheda con esempi.
    
    Args:
        title: Titolo della scheda
        examples: Dizionario con chiave=titolo dell'esempio, valore=testo dell'esempio
    """
    html_examples = ""
    for example_title, example_text in examples.items():
        html_examples += f"""
        <div style="background-color: #f8fbff; padding: 12px; border-radius: 6px; margin-bottom: 12px; border-left: 3px solid #4c8bf5;">
            <h4 style="color: #2c5282; font-size: 1.1rem; margin-top: 0;">{example_title}</h4>
            <p style="margin-bottom: 0; font-size: 0.95rem; line-height: 1.5;">{example_text}</p>
        </div>
        """
    
    st.markdown(f"""
    <div style="border: 1px solid #e2eeff; border-radius: 10px; padding: 18px; margin: 15px 0; background-color: #f5f9ff; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <h3 style="margin-top: 0; color: #0066cc; display: flex; align-items: center; font-size: 1.3rem;">
            <span style="margin-right: 8px;">📝</span> {title}
        </h3>
        <div style="margin-top: 15px;">
            {html_examples}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Funzione per creare un navigatore "Next/Back"
def navigation_buttons(back_callback: Optional[Callable] = None, 
                      next_callback: Optional[Callable] = None,
                      back_label: str = "Indietro",
                      next_label: str = "Avanti"):
    """
    Mostra i pulsanti di navigazione Next e Back.
    
    Args:
        back_callback: Funzione da chiamare quando si preme "Indietro"
        next_callback: Funzione da chiamare quando si preme "Avanti"
        back_label: Etichetta per il pulsante indietro
        next_label: Etichetta per il pulsante avanti
        
    Returns:
        Tuple: (back_pressed, next_pressed)
    """
    col1, col2 = st.columns(2)
    
    back_pressed = False
    next_pressed = False
    
    with col1:
        if back_callback is not None:
            back_pressed = st.button(f"◀️ {back_label}", key="back_button", use_container_width=True)
            if back_pressed:
                back_callback()
    
    with col2:
        if next_callback is not None:
            next_pressed = st.button(f"{next_label} ▶️", key="next_button", use_container_width=True, type="primary")
            if next_pressed:
                next_callback()
    
    # Aggiungi stile ai pulsanti
    st.markdown("""
    <style>
    div[data-testid="stButton"] > button {
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    return back_pressed, next_pressed

# NUOVA FUNZIONE: Mostra un semplice tutorial passo-passo
def show_tutorial(steps: List[Dict[str, str]], key_prefix: str = "tutorial"):
    """
    Mostra un tutorial passo-passo con immagini e descrizioni.
    
    Args:
        steps: Lista di dizionari con chiavi 'title', 'description' e opzionalmente 'image_path'
        key_prefix: Prefisso per le chiavi dei componenti Streamlit
    """
    st.markdown("### 🎓 Tutorial Passo-Passo")
    
    # Usa una tab per ogni passo del tutorial
    tabs = st.tabs([f"{i+1}. {step['title']}" for i, step in enumerate(steps)])
    
    for i, (tab, step) in enumerate(zip(tabs, steps)):
        with tab:
            st.markdown(f"#### {step['title']}")
            
            # Se c'è un'immagine, mostrala
            if 'image_path' in step and step['image_path']:
                try:
                    st.image(step['image_path'], caption=f"Passo {i+1}: {step['title']}")
                except:
                    st.warning(f"Impossibile caricare l'immagine per il passo {i+1}")
            
            # Mostra la descrizione
            st.markdown(step['description'])
            
            # Aggiungi un checkbox "Ho capito" per tracciare il progresso
            st.checkbox(f"Ho capito questo passaggio", key=f"{key_prefix}_understood_{i}")

# NUOVA FUNZIONE: Indicatore di stato per i processi lunghi
def loading_indicator(message: str = "Elaborazione in corso...", step: int = 0, total_steps: int = 1):
    """
    Mostra un indicatore di caricamento chiaro per processi lunghi.
    
    Args:
        message: Messaggio da mostrare
        step: Passo corrente (se ci sono più fasi)
        total_steps: Totale dei passi
    """
    # Calcola percentuale di completamento
    if total_steps > 1:
        percent = int((step / total_steps) * 100)
        st.markdown(f"### {message} ({percent}%)")
        st.progress(step / total_steps)
        st.caption(f"Passo {step} di {total_steps}")
    else:
        st.markdown(f"### {message}")
        # Mostra uno spinner per indicare che il processo è in corso
        with st.spinner(message):
            # Nota: il contenuto qui dentro sarà mostrato mentre lo spinner è attivo
            st.info("Questo processo potrebbe richiedere alcuni secondi. Grazie per la pazienza!")

# NUOVA FUNZIONE: Status box per mostrare i risultati del caricamento dei documenti
def document_status_box(documents: List[Dict]):
    """
    Mostra un riepilogo chiaro dei documenti caricati con stato.
    
    Args:
        documents: Lista di dizionari con informazioni sui documenti
    """
    if not documents:
        st.info("Nessun documento caricato. Usa la zona di upload sopra per caricare i tuoi documenti.")
        return
    
    st.markdown("### 📄 Documenti Caricati")
    
    # Crea un container per la tabella
    with st.container(border=True):
        for i, doc in enumerate(documents):
            # Determina lo stato del documento
            status = doc.get("status", "caricato")
            
            # Scegli l'icona appropriata
            if status == "elaborato":
                icon = "✅"
                color = "#28a745"
            elif status == "in elaborazione":
                icon = "⏳"
                color = "#ffc107"
            elif status == "errore":
                icon = "❌"
                color = "#dc3545"
            else:
                icon = "📄"
                color = "#6c757d"
            
            # Mostra il documento con il suo stato
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"**{icon} {doc.get('name', f'Documento {i+1}')}**")
            with col2:
                file_size = doc.get('size', 0)
                if file_size > 0:
                    # Converti in KB o MB
                    if file_size > 1048576:
                        size_str = f"{file_size/1048576:.1f} MB"
                    else:
                        size_str = f"{file_size/1024:.1f} KB"
                    st.caption(f"Dimensione: {size_str}")
            with col3:
                st.markdown(f"<span style='color: {color};'><strong>{status.capitalize()}</strong></span>", unsafe_allow_html=True)
            
            # Mostra dettagli aggiuntivi in un expander
            with st.expander("Dettagli", expanded=False):
                st.caption(f"Tipo: {doc.get('type', 'Sconosciuto')}")
                if "upload_time" in doc:
                    st.caption(f"Caricato il: {doc['upload_time']}")
                if "error_message" in doc and doc.get("status", "") == "errore":
                    st.error(doc["error_message"])
                
                # Pulsante per rimuovere il documento
                if st.button("🗑️ Rimuovi", key=f"remove_doc_{i}"):
                    # Questo sarà gestito dal callback nella pagina principale
                    st.session_state[f"remove_document_{i}"] = True
                    st.rerun()
            
            # Aggiungi una linea divisoria
            if i < len(documents) - 1:
                st.markdown("---") 