#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Business Plan Builder - Versione Semplificata

Questa applicazione web semplificata permette la creazione di business plan
in modo guidato e intuitivo, adatto a utenti di livello scuola media.
"""

import os
import sys
import time
import json
import uuid
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd

# Importa i componenti UI semplificati
from simplified_ui import (
    wizard_step, help_tip, upload_zone, progress_indicator,
    action_button, info_card, success_tips, example_card, navigation_buttons,
    loading_indicator, document_status_box, show_tutorial
)

# Importa i componenti del sistema
from config import Config
from state import BusinessPlanState, initialize_state
from graph_builder import build_business_plan_graph, node_functions
from database import VectorDatabase, StatePersistence, UsageTracker

# Configurazione della pagina
st.set_page_config(
    page_title="Business Plan Builder - Semplificato",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS personalizzato per migliorare l'interfaccia utente ---
st.markdown("""
<style>
/* Migliora la leggibilità del testo */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
}

/* Stile per i titoli */
h1, h2, h3, h4 {
    color: #2c3e50;
    margin-bottom: 1rem;
}

/* Stile per i container con bordo */
[data-testid="stVerticalBlock"] > [data-testid="stContainer"][style*="border"] {
    border-radius: 10px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    padding: 1rem !important;
    margin-bottom: 1rem !important;
}

/* Rendi più visibili i pulsanti */
.stButton button {
    font-weight: bold !important;
    transition: all 0.3s !important;
}

/* Stile per i form */
.stForm {
    padding: 20px !important;
    border-radius: 10px !important;
    background-color: #f8f9fa !important;
}

/* Stile per i campi di input */
input, textarea, [data-baseweb="select"] {
    border-radius: 5px !important;
    border-width: 1px !important;
}

/* Stile per i campi di input con focus */
input:focus, textarea:focus {
    border-color: #4CAF50 !important;
    box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
}

/* Migliora la visibilità degli expander */
.streamlit-expanderHeader {
    font-weight: bold !important;
    color: #2c3e50 !important;
}

/* Stile per le icone emoji */
.emoji {
    font-size: 1.2rem;
    vertical-align: middle;
    margin-right: 0.5rem;
}

/* Migliora la visualizzazione su dispositivi mobili */
@media (max-width: 640px) {
    h1 {
        font-size: 1.8rem !important;
    }
    .stButton button {
        padding: 0.5rem !important;
        font-size: 0.9rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# --- Inizializzazione Session State ---
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.wizard_step = 0  # Step corrente del wizard
    st.session_state.documents = []  # Lista di dict {nome_file, tipo, testo}
    st.session_state.state_dict = initialize_state(
        document_title="Business Plan - Nuova Azienda",
        company_name="Nuova Azienda",
        creation_date=datetime.now().strftime("%Y-%m-%d"),
        version=1
    )
    # Aggiungi campi per le info base allo stato
    st.session_state.state_dict.update({
        "business_sector": "", 
        "company_description": "", 
        "year_founded": "",
        "num_employees": "", 
        "main_products": "", 
        "target_market": "", 
        "area": "",
        "plan_objectives": "", 
        "time_horizon": "", 
        "funding_needs": "",
        "documents_text": "", 
        "section_documents_text": "",
    })
    st.session_state.current_output = ""  # Output del nodo corrente
    
    # Inizializzazione del gestore di utilizzo
    st.session_state.usage_tracker = UsageTracker()
    
    # Genera un ID di sessione univoco se non esiste
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Traccia l'utilizzo iniziale
    st.session_state.usage_stats = st.session_state.usage_tracker.get_usage_stats(st.session_state.session_id)

# --- Funzioni di navigazione del wizard ---
def go_to_step(step_index):
    """Vai a uno step specifico del wizard"""
    st.session_state.wizard_step = step_index

def next_step():
    """Vai allo step successivo del wizard"""
    st.session_state.wizard_step += 1

def prev_step():
    """Vai allo step precedente del wizard"""
    st.session_state.wizard_step -= 1

# --- Titolo principale dell'applicazione ---
st.title("🚀 Business Plan Builder - Versione Semplificata")
st.markdown("""
<div style="background-color: #f0f7ff; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
    <h2 style="color: #0066cc; margin-top: 0;">✨ Benvenuto nel tuo assistente personale per business plan!</h2>
    
    <p style="font-size: 1.1rem; margin-bottom: 15px;">
        Questa applicazione ti guida passo dopo passo nella creazione del tuo business plan, anche se non hai mai creato uno prima d'ora.
    </p>
    
    <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="color: #28a745; margin-top: 0; font-size: 1.2rem;">😊 Cos'è un business plan?</h3>
        <p>Un business plan è semplicemente un documento che descrive la tua idea di business, come funzionerà e come pensi di avere successo. È come una mappa che ti aiuta a raggiungere i tuoi obiettivi!</p>
    </div>
    
    <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="color: #28a745; margin-top: 0; font-size: 1.2rem;">🎯 Come funziona questa app?</h3>
        <p>Ti faremo delle domande semplici e tu dovrai solo rispondere. L'intelligenza artificiale farà gran parte del lavoro per te, creando un business plan professionale basato sulle tue risposte.</p>
    </div>
    
    <p>
        <span style="background-color: #007bff; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.9rem;">
            FACILE DA USARE
        </span>
        <span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.9rem; margin-left: 8px;">
            PASSO DOPO PASSO
        </span>
        <span style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.9rem; margin-left: 8px;">
            COMPLETO
        </span>
    </p>
</div>
""", unsafe_allow_html=True)

# --- Definizione degli step del wizard ---
WIZARD_STEPS = [
    "Informazioni di Base",
    "Carica Documenti",
    "Definisci Obiettivi",
    "Crea Piano",
    "Analisi Finanziaria",
    "Revisione",
    "Esportazione"
]

# --- Funzione per mostrare il footer ---
def show_footer():
    """Mostra un piè di pagina con informazioni di supporto."""
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 30px;">
        <h3 style="font-size: 1.1rem; color: #333;">Hai bisogno di aiuto? 💬</h3>
        <p>
            Se hai dubbi su come compilare il tuo business plan o come usare questa applicazione:
        </p>
        <ul style="margin-bottom: 15px;">
            <li>Cerca l'icona <strong>💡 Hai bisogno di aiuto?</strong> in ogni sezione</li>
            <li>Guarda gli esempi forniti in ogni passaggio</li>
            <li>Ricorda che puoi sempre tornare indietro e modificare le tue risposte</li>
        </ul>
        <p style="margin-bottom: 5px; font-size: 0.9rem; text-align: center; color: #666;">
            Business Plan Builder - Versione Semplificata © 2023<br>
            <a href="mailto:supporto@businessplanbuilder.it" style="color: #0066cc; text-decoration: none;">supporto@businessplanbuilder.it</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Visualizza l'indicatore di progresso ---
progress_indicator(WIZARD_STEPS, st.session_state.wizard_step)

# --- Sidebar con aiuto e informazioni ---
with st.sidebar:
    st.title("📚 Guida Rapida")
    
    # Menu di navigazione rapida
    st.markdown("### 🧭 Navigazione")
    for i, step_name in enumerate(WIZARD_STEPS):
        if st.button(f"{i+1}. {step_name}", key=f"nav_{i}", disabled=i == st.session_state.wizard_step):
            st.session_state.wizard_step = i
            st.rerun()
    
    # Visualizza le statistiche di utilizzo
    if hasattr(st.session_state, 'usage_stats'):
        with st.expander("📊 Utilizzo", expanded=False):
            stats = st.session_state.usage_stats
            st.progress(stats['percentage_used'] / 100)
            st.caption(f"Utilizzo: {stats['total_generations']}/{stats['limit']} generazioni")
    
    # Aggiungi sezione FAQ
    with st.expander("❓ Domande Frequenti", expanded=False):
        st.markdown("""
        **Come funziona il Business Plan Builder?**
        Segui semplicemente i passi del wizard! Ti guideremo attraverso ogni fase.
        
        **Posso salvare il mio lavoro?**
        Sì, potrai esportare il tuo business plan completo nell'ultimo passaggio.
        
        **Ho bisogno di conoscenze specifiche?**
        No, l'app è progettata per essere facile da usare anche senza esperienza.
        
        **I miei dati sono al sicuro?**
        Sì, i tuoi dati rimangono sul tuo computer e non vengono condivisi.
        """)

    # Aggiungi contatti per supporto
    with st.expander("📞 Supporto", expanded=False):
        st.markdown("""
        **Hai bisogno di aiuto?**
        
        * Email: supporto@example.com
        * Chat: Clicca sull'icona in basso a destra
        * Telefono: +39 123 456789
        """)
        
        # Pulsante per contattare il supporto
        if st.button("📩 Contatta il Supporto", use_container_width=True):
            st.info("Funzionalità di contatto non ancora implementata.")
    
    # Aggiungi risorse utili
    with st.expander("📖 Risorse Utili", expanded=False):
        st.markdown("""
        * [Guida alla creazione di un Business Plan](https://example.com/guida-business-plan)
        * [Template di esempio](https://example.com/template)
        * [Video tutorial](https://example.com/video)
        * [Consigli per un Business Plan efficace](https://example.com/consigli)
        """)

# --- Contenuto principale dell'app in base allo step corrente ---
current_step = st.session_state.wizard_step

# STEP 0: Informazioni di Base
if current_step == 0:
    with wizard_step(1, WIZARD_STEPS[0], active=True, 
                    description="In questa fase inseriremo le informazioni base della tua azienda o idea imprenditoriale"):
        st.subheader("📝 Dicci qualcosa sulla tua azienda")
        
        help_tip("""
        Le informazioni di base sono fondamentali per creare un business plan efficace.
        Non preoccuparti se non hai tutte le risposte ora, potrai sempre modificarle in seguito.
        """, expanded=True)
        
        # Form per raccogliere informazioni di base
        with st.form("business_info_form"):
            col1, col2 = st.columns(2)
            with col1:
                company_name = st.text_input("Nome dell'Azienda", 
                                            value=st.session_state.state_dict.get("company_name", ""),
                                            help="Il nome della tua azienda o progetto")
                
                business_sector = st.selectbox("Settore di Attività", 
                                            options=["", "Tecnologia", "Commercio", "Ristorazione", "Servizi", "Produzione", 
                                                    "Salute e Benessere", "Turismo", "Formazione", "Altro"],
                                            index=0,
                                            help="Il settore in cui opera la tua azienda")
                
                if business_sector == "Altro":
                    business_sector = st.text_input("Specifica il settore")
                
                year_founded = st.text_input("Anno di Fondazione (o previsto)", 
                                            value=st.session_state.state_dict.get("year_founded", ""),
                                            help="L'anno in cui è stata fondata o sarà fondata l'azienda")
                
                num_employees = st.text_input("Numero di Dipendenti (o previsto)", 
                                            value=st.session_state.state_dict.get("num_employees", ""),
                                            help="Il numero attuale o previsto di dipendenti")
            
            with col2:
                company_description = st.text_area("Breve Descrizione dell'Azienda", 
                                                value=st.session_state.state_dict.get("company_description", ""),
                                                help="Una breve descrizione della tua azienda e cosa fa",
                                                height=152)
                
                main_products = st.text_area("Principali Prodotti/Servizi", 
                                            value=st.session_state.state_dict.get("main_products", ""),
                                            help="I principali prodotti o servizi offerti")
            
            # Ulteriori campi
            target_market = st.text_area("Mercato Target", 
                                        value=st.session_state.state_dict.get("target_market", ""),
                                        help="Chi sono i tuoi clienti ideali? A chi ti rivolgi?")
            
            area = st.text_input("Area Geografica", 
                                value=st.session_state.state_dict.get("area", ""),
                                help="L'area geografica in cui operi o intendi operare")
            
            # Pulsante per salvare e continuare
            submit_button = st.form_submit_button("Salva e Continua")
            
            if submit_button:
                # Aggiornamento dello stato con i nuovi valori
                st.session_state.state_dict.update({
                    "company_name": company_name,
                    "business_sector": business_sector,
                    "company_description": company_description,
                    "year_founded": year_founded,
                    "num_employees": num_employees,
                    "main_products": main_products,
                    "target_market": target_market,
                    "area": area
                })
                
                # Mostra conferma e procedi al prossimo step
                st.success("✅ Informazioni salvate con successo!")
                time.sleep(1)  # Breve pausa per mostrare il messaggio
                next_step()
                st.rerun()  # Ricarica la pagina per mostrare il prossimo step

# STEP 1: Carica Documenti
elif current_step == 1:
    with wizard_step(2, WIZARD_STEPS[1], active=True, 
                    description="Carica documenti esistenti che possono aiutare a creare il tuo business plan"):
        st.subheader("📄 Carica documenti utili")
        
        help_tip("""
        Puoi caricare documenti che contengono informazioni utili per il tuo business plan.
        Ad esempio: business plan precedenti, ricerche di mercato, bilanci, presentazioni, ecc.
        Questo passaggio è opzionale - puoi anche procedere senza caricare documenti.
        """)
        
        # Zona di caricamento file
        uploaded_file = upload_zone(
            title="Carica Documenti Utili",
            instructions="Trascina qui i tuoi file o fai clic per selezionarli. Supportiamo PDF, Word, Excel e file di testo.",
            upload_types=["pdf", "docx", "xlsx", "txt", "csv"],
            key="doc_upload"
        )
        
        # Elabora il file caricato
        if uploaded_file is not None:
            # Mostra indicatore di caricamento durante l'elaborazione
            with st.spinner("Elaborazione del documento in corso..."):
                # Qui si dovrebbe aggiungere la logica di elaborazione del documento
                # Per semplicità, qui salviamo solo il nome del file
                if uploaded_file.name not in [doc["nome_file"] for doc in st.session_state.documents]:
                    st.session_state.documents.append({
                        "nome_file": uploaded_file.name,
                        "tipo": uploaded_file.type,
                        "testo": "Contenuto del documento"  # Placeholder
                    })
        
        # Mostra i documenti caricati
        if st.session_state.documents:
            document_status_box(st.session_state.documents)
        
        # Pulsanti di navigazione
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⬅️ Indietro", use_container_width=True):
                prev_step()
                st.rerun()
        with col2:
            if st.button("Avanti ➡️", use_container_width=True, type="primary"):
                next_step()
                st.rerun()

# STEP 2: Definisci Obiettivi
elif current_step == 2:
    with wizard_step(3, WIZARD_STEPS[2], active=True,
                    description="Definisci gli obiettivi che vuoi raggiungere con il tuo business plan"):
        st.subheader("🎯 Definisci gli obiettivi del tuo business plan")
        
        help_tip("""
        Definire obiettivi chiari ti aiuterà a creare un business plan più efficace.
        Pensa a cosa vuoi ottenere nei prossimi mesi o anni e quanto denaro potrebbe servirti.
        """)
        
        # Form per raccogliere obiettivi
        with st.form("objectives_form"):
            plan_objectives = st.text_area(
                "Quali sono i tuoi obiettivi principali?", 
                value=st.session_state.state_dict.get("plan_objectives", ""),
                height=150,
                help="Ad esempio: aumentare le vendite, espandere in nuovi mercati, lanciare un nuovo prodotto..."
            )
            
            # Esempi di obiettivi ben formulati
            example_card("Esempi di obiettivi ben formulati", {
                "Obiettivo di crescita": "Aumentare le vendite del 15% nei prossimi 12 mesi attraverso l'apertura di un nuovo punto vendita in centro città.",
                "Obiettivo di prodotto": "Lanciare una nuova linea di prodotti eco-sostenibili entro marzo 2026.",
                "Obiettivo finanziario": "Raggiungere il punto di pareggio entro 18 mesi dall'apertura."
            })
            
            col1, col2 = st.columns(2)
            with col1:
                time_horizon = st.selectbox(
                    "Orizzonte temporale del piano", 
                    options=["", "1 anno", "2 anni", "3 anni", "5 anni", "Altro"],
                    index=0,
                    help="Per quanto tempo in futuro stai pianificando?"
                )
                
                if time_horizon == "Altro":
                    time_horizon = st.text_input("Specifica l'orizzonte temporale")
            
            with col2:
                funding_needs = st.text_input(
                    "Necessità di finanziamento (se presenti)", 
                    value=st.session_state.state_dict.get("funding_needs", ""),
                    help="Ad esempio: €50.000 per l'apertura di un nuovo punto vendita"
                )
            
            # Pulsante per salvare e continuare
            submit_button = st.form_submit_button("Salva e Continua")
            
            if submit_button:
                # Aggiornamento dello stato con i nuovi valori
                st.session_state.state_dict.update({
                    "plan_objectives": plan_objectives,
                    "time_horizon": time_horizon,
                    "funding_needs": funding_needs
                })
                
                # Mostra conferma e procedi al prossimo step
                st.success("✅ Obiettivi salvati con successo!")
                time.sleep(1)  # Breve pausa per mostrare il messaggio
                next_step()
                st.rerun()
        
        # Pulsanti di navigazione al di fuori del form
        navigation_buttons(
            back_callback=lambda: (prev_step(), st.rerun()),
            back_label="⬅️ Indietro"
        )

# STEP 3: Crea Piano (semplificato)
elif current_step == 3:
    with wizard_step(4, WIZARD_STEPS[3], active=True,
                    description="L'intelligenza artificiale ti aiuterà a creare le sezioni del tuo business plan"):
        st.subheader("📝 Costruiamo il tuo business plan")
        
        help_tip("""
        Ora creeremo le varie sezioni del tuo business plan utilizzando l'intelligenza artificiale.
        Il processo è semplice: ti mostreremo una sezione alla volta e potrai modificarla se necessario.
        """)
        
        # Mostra le sezioni del business plan
        sections = list(Config.DEFAULT_BUSINESS_PLAN_STRUCTURE.keys())
        
        # Seleziona la sezione corrente (salva in session state)
        if 'current_section' not in st.session_state:
            st.session_state.current_section = 0
        
        section_tabs = st.tabs(sections)
        
        with section_tabs[st.session_state.current_section]:
            current_section = sections[st.session_state.current_section]
            st.markdown(f"### {current_section}")
            
            # Mostra subsections come checklist
            subsections = Config.DEFAULT_BUSINESS_PLAN_STRUCTURE[current_section]
            for subsection in subsections:
                st.checkbox(subsection, value=True, key=f"check_{subsection}")
            
            # Pulsante per generare il contenuto
            if st.button("Genera Contenuto", type="primary", key=f"gen_{current_section}"):
                with st.spinner(f"Generazione della sezione '{current_section}' in corso..."):
                    # Simulazione di generazione (qui dovresti integrare con il modello LLM)
                    time.sleep(2)  # Simula elaborazione
                    generated_text = f"Contenuto di esempio per la sezione {current_section}. " * 20
                    
                    # Salva il risultato in session state
                    if 'generated_sections' not in st.session_state:
                        st.session_state.generated_sections = {}
                    
                    st.session_state.generated_sections[current_section] = generated_text
            
            # Mostra il contenuto generato se disponibile
            if 'generated_sections' in st.session_state and current_section in st.session_state.generated_sections:
                st.text_area("Contenuto Generato (puoi modificarlo)", 
                           value=st.session_state.generated_sections[current_section],
                           height=300,
                           key=f"edit_{current_section}")
        
        # Pulsanti di navigazione tra le sezioni
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("◀️ Sezione Precedente", 
                      disabled=(st.session_state.current_section == 0),
                      use_container_width=True):
                st.session_state.current_section = max(0, st.session_state.current_section - 1)
                st.rerun()
        
        with col3:
            if st.button("Sezione Successiva ▶️", 
                      disabled=(st.session_state.current_section == len(sections) - 1),
                      use_container_width=True):
                st.session_state.current_section = min(len(sections) - 1, st.session_state.current_section + 1)
                st.rerun()
        
        # Pulsanti di navigazione tra gli step del wizard
        st.markdown("---")
        navigation_buttons(
            back_callback=lambda: (prev_step(), st.rerun()),
            next_callback=lambda: (next_step(), st.rerun()),
            back_label="⬅️ Indietro",
            next_label="Avanti ➡️"
        )

# STEP 4: Analisi Finanziaria
elif current_step == 4:
    with wizard_step(5, WIZARD_STEPS[4], active=True,
                    description="Crea le previsioni finanziarie per il tuo business plan"):
        st.subheader("💰 Previsioni Finanziarie")
        
        help_tip("""
        In questa sezione creerai le previsioni finanziarie per il tuo business plan.
        Non devi essere un esperto di finanza - ti guideremo passo per passo con un linguaggio semplice.
        """)
        
        # Tabs per le diverse sezioni finanziarie
        fin_tabs = st.tabs(["Ricavi", "Costi", "Investimenti", "Riepilogo"])
        
        with fin_tabs[0]:
            st.markdown("### 📈 Previsione dei Ricavi")
            
            st.info("I ricavi sono i soldi che la tua azienda guadagnerà vendendo prodotti o servizi.")
            
            # Esempio di form per i ricavi
            with st.form("revenue_form"):
                st.number_input("Prezzo medio del prodotto/servizio (€)", 
                              min_value=0.0, value=100.0, step=10.0)
                st.number_input("Unità vendute nel primo anno", 
                              min_value=0, value=100, step=10)
                st.slider("Crescita annuale prevista (%)", 
                        min_value=0, max_value=100, value=10)
                st.form_submit_button("Salva Previsioni Ricavi")
        
        with fin_tabs[1]:
            st.markdown("### 📉 Previsione dei Costi")
            
            st.info("I costi sono le spese che la tua azienda dovrà sostenere per operare.")
            
            # Form per i costi fissi
            st.subheader("Costi Fissi (mensili)")
            with st.form("fixed_costs_form"):
                st.number_input("Affitto (€/mese)", min_value=0, value=1000, step=100)
                st.number_input("Stipendi (€/mese)", min_value=0, value=5000, step=500)
                st.number_input("Utenze (€/mese)", min_value=0, value=300, step=50)
                st.form_submit_button("Salva Costi Fissi")
            
            # Form per i costi variabili
            st.subheader("Costi Variabili (per unità)")
            with st.form("variable_costs_form"):
                st.number_input("Costo materiali per unità (€)", min_value=0.0, value=20.0, step=5.0)
                st.number_input("Costo produzione per unità (€)", min_value=0.0, value=10.0, step=1.0)
                st.number_input("Altri costi variabili per unità (€)", min_value=0.0, value=5.0, step=1.0)
                st.form_submit_button("Salva Costi Variabili")
        
        with fin_tabs[2]:
            st.markdown("### 💸 Investimenti Iniziali")
            
            st.info("Gli investimenti iniziali sono i soldi che devi spendere per avviare la tua attività.")
            
            # Form per gli investimenti
            with st.form("investments_form"):
                st.number_input("Attrezzature e macchinari (€)", min_value=0, value=10000, step=1000)
                st.number_input("Arredamento e allestimento (€)", min_value=0, value=5000, step=500)
                st.number_input("Marketing iniziale (€)", min_value=0, value=2000, step=500)
                st.number_input("Altri investimenti (€)", min_value=0, value=3000, step=500)
                st.form_submit_button("Salva Investimenti")
        
        with fin_tabs[3]:
            st.markdown("### 📊 Riepilogo Finanziario")
            
            # Qui mostreremmo un riepilogo delle previsioni finanziarie
            st.info("Questa sezione mostrerà un riepilogo delle tue previsioni finanziarie.")
            
            # Placeholder per una tabella di riepilogo
            data = {
                "Anno": ["Anno 1", "Anno 2", "Anno 3"],
                "Ricavi": ["€50,000", "€60,000", "€72,000"],
                "Costi": ["€40,000", "€45,000", "€51,000"],
                "Profitto": ["€10,000", "€15,000", "€21,000"]
            }
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # Aggiungi pulsante per generare report completo
            st.button("Genera Report Finanziario Completo", type="primary")
        
        # Pulsanti di navigazione
        navigation_buttons(
            back_callback=lambda: (prev_step(), st.rerun()),
            next_callback=lambda: (next_step(), st.rerun()),
            back_label="⬅️ Indietro",
            next_label="Avanti ➡️"
        )

# STEP 5: Revisione
elif current_step == 5:
    with wizard_step(6, WIZARD_STEPS[5], active=True,
                    description="Rivedi il tuo business plan e apporta le ultime modifiche"):
        st.subheader("✅ Rivedi il tuo business plan")
        
        help_tip("""
        In questa fase puoi rivedere tutte le sezioni del tuo business plan.
        Controlla che tutto sia corretto e fai le modifiche necessarie prima di procedere all'esportazione.
        """)
        
        # Tabs per le diverse sezioni del business plan
        sections = list(Config.DEFAULT_BUSINESS_PLAN_STRUCTURE.keys())
        section_tabs = st.tabs(sections)
        
        # Mostra placeholder per ogni sezione
        for i, tab in enumerate(section_tabs):
            with tab:
                section = sections[i]
                st.markdown(f"### {section}")
                
                # Mostra il contenuto generato o un placeholder
                if 'generated_sections' in st.session_state and section in st.session_state.generated_sections:
                    content = st.session_state.generated_sections[section]
                else:
                    content = f"Contenuto non ancora generato per la sezione {section}."
                
                st.text_area("Contenuto", value=content, height=300, key=f"review_{section}")
                
                st.button("Modifica questa sezione", key=f"edit_btn_{section}")
        
        # Pulsanti di navigazione
        navigation_buttons(
            back_callback=lambda: (prev_step(), st.rerun()),
            next_callback=lambda: (next_step(), st.rerun()),
            back_label="⬅️ Indietro",
            next_label="Vai all'Esportazione ➡️"
        )

# STEP 6: Esportazione
elif current_step == 6:
    with wizard_step(7, WIZARD_STEPS[6], active=True,
                    description="Esporta il tuo business plan in diversi formati"):
        st.subheader("📤 Esporta il tuo business plan")
        
        help_tip("""
        Ora puoi esportare il tuo business plan in diversi formati.
        Potrai scaricarlo, condividerlo o stamparlo.
        """)
        
        # Opzioni di formato
        st.markdown("### Scegli il formato di esportazione")
        export_format = st.selectbox(
            "Formato", 
            options=["PDF", "Word (DOCX)", "Presentazione PowerPoint", "HTML"],
            index=0
        )
        
        # Opzioni di personalizzazione
        st.markdown("### Personalizza l'esportazione")
        
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Includere immagini", value=True)
            st.checkbox("Includere indice", value=True)
            st.checkbox("Includere pagina di copertina", value=True)
        
        with col2:
            st.checkbox("Includere grafici finanziari", value=True)
            st.checkbox("Includere tabelle di dati", value=True)
            st.checkbox("Includere appendici", value=False)
        
        # Anteprima del documento
        st.markdown("### Anteprima")
        st.info("Qui verrà mostrata un'anteprima del tuo business plan prima dell'esportazione.")
        
        # Placeholder per un'anteprima
        st.image("https://via.placeholder.com/800x400?text=Anteprima+Business+Plan", use_column_width=True)
        
        # Pulsante di esportazione
        if st.button("Esporta Business Plan", type="primary"):
            with st.spinner("Preparazione del documento in corso..."):
                # Simulare l'esportazione
                time.sleep(2)
                st.success("🎉 Business plan esportato con successo!")
                
                # Link di download (placeholder)
                st.markdown("[Scarica il tuo Business Plan](#)")
        
        # Pulsanti di navigazione
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Indietro", use_container_width=True):
                prev_step()
                st.rerun()
        
        with col3:
            if st.button("🔄 Ricomincia", use_container_width=True):
                # Reset della sessione
                st.session_state.wizard_step = 0
                # Altri reset qui se necessari
                st.rerun()

# Mostra il footer alla fine della pagina, indipendentemente dallo step
show_footer()

# --- Visualizza il footer ---
st.markdown("---")
st.caption("Business Plan Builder - Versione Semplificata © 2023")
if st.button("💬 Contattaci", key="contact_button"):
    st.sidebar.success("Grazie per averci contattato! Ti risponderemo al più presto.")
    st.session_state.contact_clicked = True
