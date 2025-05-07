#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generatore di Business Plan Semplificato
Questa è una versione semplificata dell'applicazione che si concentra solo sulla generazione delle sezioni.
"""

import os
import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime

# Carica variabili d'ambiente da .env se presente
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("File .env caricato")
except ImportError:
    print("dotenv non installato")

# Configurazione
GEMINI_MODEL = "gemini-1.5-pro"  # Modello più stabile e ampiamente disponibile
TEMPERATURE = 0.2
MAX_TOKENS = 4000

# Titolo dell'app
st.set_page_config(page_title="Generatore Business Plan Semplificato", layout="wide")
st.title("🚀 Generatore Business Plan Semplificato")

# Sidebar per i dati dell'azienda
with st.sidebar:
    st.header("Informazioni Azienda")
    
    company_name = st.text_input("Nome Azienda", value="La Mia Azienda")
    business_sector = st.text_input("Settore", value="Tecnologia")
    company_description = st.text_area("Descrizione", value="Un'azienda innovativa nel settore tecnologico.")
    year_founded = st.text_input("Anno Fondazione", value="2023")
    num_employees = st.text_input("Numero Dipendenti", value="10")
    main_products = st.text_input("Prodotti/Servizi", value="Software, Consulenza")
    target_market = st.text_input("Mercato Target", value="PMI")
    area = st.text_input("Area Geografica", value="Italia")
    
    # Pulsante per caricare un esempio
    if st.button("Carica Esempio"):
        company_name = "TechSolutions Italia"
        business_sector = "Software e Servizi IT"
        company_description = "TechSolutions Italia è un'azienda specializzata nello sviluppo di soluzioni software innovative per la digitalizzazione delle PMI italiane."
        year_founded = "2022"
        num_employees = "15"
        main_products = "Software gestionale cloud, consulenza IT, servizi di cybersecurity"
        target_market = "Piccole e medie imprese italiane nel settore manifatturiero e retail"
        area = "Italia, con focus su Nord e Centro Italia"
        st.success("Esempio caricato!")

# Funzione per generare una sezione
def generate_section(section_name):
    # Verifica se la chiave API è disponibile
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except:
            st.error("Chiave API Gemini non trovata. Imposta la variabile d'ambiente GEMINI_API_KEY o configura st.secrets.")
            return None
    
    # Configura l'API Gemini
    genai.configure(api_key=api_key)
    
    # Crea il modello
    model = genai.GenerativeModel(GEMINI_MODEL)
    
    # Costruisci il prompt
    prompt = f"""
    Sei un esperto consulente di business plan. Scrivi SOLO il testo completo e pronto da incollare della sezione '{section_name}' del business plan per l'azienda {company_name}.
    
    NON includere meta-informazioni, intestazioni, ruoli, parentesi graffe, markdown, né alcuna spiegazione tecnica.
    Il testo deve essere scorrevole, professionale, coerente e adatto a un documento finale.
    Se la sezione è molto lunga, concludi la frase e non troncare a metà.
    Se necessario, suddividi in paragrafi ma senza titoli o numerazioni.
    
    Informazioni sull'azienda:
    - Nome: {company_name}
    - Settore: {business_sector}
    - Descrizione: {company_description}
    - Anno fondazione: {year_founded}
    - Dipendenti: {num_employees}
    - Prodotti/Servizi: {main_products}
    - Mercato target: {target_market}
    - Area geografica: {area}
    
    La risposta deve essere di circa 800 parole.
    Scrivi in italiano con stile professionale e formale.
    """
    
    # Aggiungi istruzioni specifiche per sezione
    if section_name.lower() in ["sommario esecutivo", "executive summary"]:
        prompt += """
        Per questa sezione di sommario esecutivo, includi:
        - Breve descrizione dell'azienda e della sua missione
        - Prodotti o servizi offerti
        - Mercato target e opportunità di mercato
        - Vantaggio competitivo
        - Obiettivi finanziari principali
        - Eventuali richieste di finanziamento
        """
    elif section_name.lower() in ["descrizione dell'azienda", "company description"]:
        prompt += """
        Per questa sezione di descrizione dell'azienda, includi:
        - Storia e background dell'azienda
        - Missione e visione
        - Obiettivi a breve e lungo termine
        - Struttura legale
        - Localizzazione e infrastrutture
        """
    elif section_name.lower() in ["prodotti e servizi", "products and services"]:
        prompt += """
        Per questa sezione di prodotti e servizi, includi:
        - Descrizione dettagliata dei prodotti/servizi
        - Benefici e valore per i clienti
        - Stato di sviluppo (esistente, in sviluppo)
        - Proprietà intellettuale o brevetti
        - Ricerca e sviluppo futuri
        """
    elif section_name.lower() in ["analisi di mercato", "market analysis"]:
        prompt += """
        Per questa sezione di analisi di mercato, includi:
        - Dimensione attuale del mercato con dati numerici
        - Tasso di crescita previsto (CAGR)
        - Segmentazione del mercato
        - Tendenze principali
        - Opportunità e sfide
        """
    elif section_name.lower() in ["analisi competitiva", "competitor analysis"]:
        prompt += """
        Per questa sezione di analisi competitiva, includi:
        - Panoramica dei principali concorrenti
        - Punti di forza e debolezza dei concorrenti
        - Posizionamento dell'azienda rispetto ai concorrenti
        - Vantaggi competitivi dell'azienda
        - Analisi SWOT sintetica
        """
    
    # Genera il contenuto
    try:
        generation_config = {
            "temperature": TEMPERATURE,
            "max_output_tokens": MAX_TOKENS,
            "top_p": 0.95,
            "top_k": 40
        }
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        return response.text
    except Exception as e:
        st.error(f"Errore nella generazione: {str(e)}")
        return None

# Sezioni disponibili
sections = [
    "Sommario Esecutivo",
    "Descrizione dell'Azienda",
    "Prodotti e Servizi",
    "Analisi di Mercato",
    "Analisi Competitiva",
    "Strategia di Marketing",
    "Piano Operativo",
    "Organizzazione e Team di Gestione",
    "Analisi dei Rischi",
    "Piano Finanziario"
]

# Area principale
st.header("Seleziona una sezione da generare")

# Layout a colonne per le sezioni
col1, col2 = st.columns(2)

with col1:
    selected_section = st.selectbox("Sezione", sections)
    
    # Pulsante per generare
    if st.button("Genera Sezione", type="primary"):
        with st.spinner(f"Generazione della sezione '{selected_section}' in corso..."):
            generated_text = generate_section(selected_section)
            
            if generated_text:
                # Salva il risultato in session_state
                if 'generated_sections' not in st.session_state:
                    st.session_state.generated_sections = {}
                
                st.session_state.generated_sections[selected_section] = generated_text
                st.success(f"Sezione '{selected_section}' generata con successo!")
                
                # Mostra il risultato
                st.subheader(f"Contenuto generato: {selected_section}")
                st.text_area("", value=generated_text, height=400, key=f"output_{selected_section}")
                
                # Pulsante per copiare negli appunti (JavaScript)
                st.markdown("""
                <script>
                function copyToClipboard(text) {
                    navigator.clipboard.writeText(text).then(function() {
                        alert('Copiato negli appunti!');
                    }, function() {
                        alert('Errore durante la copia');
                    });
                }
                </script>
                """, unsafe_allow_html=True)

with col2:
    # Mostra le sezioni già generate
    st.subheader("Sezioni Generate")
    
    if 'generated_sections' in st.session_state and st.session_state.generated_sections:
        for section, content in st.session_state.generated_sections.items():
            with st.expander(section):
                st.text_area("", value=content, height=200, key=f"saved_{section}")
    else:
        st.info("Nessuna sezione generata. Usa il pulsante 'Genera Sezione' per iniziare.")

# Pulsante per esportare tutto il business plan
if 'generated_sections' in st.session_state and st.session_state.generated_sections:
    st.header("Esporta Business Plan Completo")
    
    if st.button("Esporta come TXT"):
        # Crea il contenuto completo
        full_content = f"# Business Plan - {company_name}\n"
        full_content += f"Data: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        # Aggiungi le sezioni nell'ordine corretto
        for section in sections:
            if section in st.session_state.generated_sections:
                full_content += f"## {section}\n\n"
                full_content += st.session_state.generated_sections[section]
                full_content += "\n\n"
        
        # Crea un link per il download
        st.download_button(
            label="Scarica Business Plan",
            data=full_content,
            file_name=f"business_plan_{company_name.replace(' ', '_')}.txt",
            mime="text/plain"
        )

# Sezione di debug
with st.expander("Debug e Diagnostica"):
    st.subheader("Test Connessione Gemini")
    
    if st.button("Verifica Connessione API"):
        try:
            # Verifica se la chiave API è disponibile
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                try:
                    api_key = st.secrets["GEMINI_API_KEY"]
                except:
                    st.error("Chiave API Gemini non trovata. Imposta la variabile d'ambiente GEMINI_API_KEY o configura st.secrets.")
                    api_key = None
            
            if api_key:
                # Configura l'API Gemini
                genai.configure(api_key=api_key)
                
                # Crea il modello e testa una generazione semplice
                model = genai.GenerativeModel(GEMINI_MODEL)
                response = model.generate_content("Ciao, sono un test di connessione.")
                
                st.success(f"✅ Connessione a Gemini riuscita! Risposta: {response.text[:50]}...")
        except Exception as e:
            st.error(f"❌ Errore di connessione a Gemini: {str(e)}")
    
    # Mostra informazioni sul sistema
    st.subheader("Informazioni di Sistema")
    
    # Mostra le variabili d'ambiente (solo quelle sicure)
    safe_env_vars = {
        "PYTHONPATH": os.environ.get("PYTHONPATH", "Non impostato"),
        "STREAMLIT_SERVER_PORT": os.environ.get("STREAMLIT_SERVER_PORT", "Non impostato"),
        "GEMINI_API_KEY": "***" if os.environ.get("GEMINI_API_KEY") else "Non impostato"
    }
    
    st.json(safe_env_vars)
