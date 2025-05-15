#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interfaccia Streamlit per la generazione diretta di sezioni del business plan.
Questo script fornisce un'interfaccia utente semplice per il modulo direct_section_generator.py.
"""

import os
import sys
import streamlit as st
from datetime import datetime

# Assicurati che la directory principale sia nel path per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa i componenti necessari
try:
    from config import Config
    from state import initialize_state
    from direct_section_generator import generate_section, extract_pure_content
except ImportError as e:
    st.error(f"Errore nell'importare i moduli: {e}")
    st.stop()

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Generatore di Sezioni Business Plan",
    page_icon="📝",
    layout="wide"
)

# Titolo principale
st.title("📝 Generatore di Sezioni del Business Plan")
st.subheader("Strumento per generare rapidamente singole sezioni del business plan")

# Inizializza lo stato se non esiste
if 'state_dict' not in st.session_state:
    st.session_state.state_dict = initialize_state(
        document_title="Business Plan di Test",
        company_name="Azienda di Test",
        creation_date=datetime.now().strftime("%Y-%m-%d"),
        version=1
    )
    
    # Aggiungi campi aggiuntivi allo stato
    st.session_state.state_dict.update({
        "business_sector": "Tecnologia",
        "company_description": "Un'azienda innovativa nel settore tecnologico",
        "year_founded": "2022",
        "num_employees": "10",
        "main_products": "Software, Consulenza",
        "target_market": "PMI",
        "area": "Italia",
        "plan_objectives": "Crescita e espansione",
        "time_horizon": "3 anni",
        "funding_needs": "€500.000",
        "documents_text": "",
        "section_documents_text": "",
        "temperature": Config.TEMPERATURE,
        "max_tokens": Config.MAX_TOKENS
    })

# Crea layout a colonne
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Informazioni Aziendali")
    with st.form(key="company_info_form"):
        # Dati aziendali di base
        st.session_state.state_dict["company_name"] = st.text_input(
            "Nome Azienda", 
            value=st.session_state.state_dict.get("company_name", "")
        )
        
        st.session_state.state_dict["business_sector"] = st.text_input(
            "Settore", 
            value=st.session_state.state_dict.get("business_sector", "")
        )
        
        st.session_state.state_dict["company_description"] = st.text_area(
            "Descrizione Azienda", 
            value=st.session_state.state_dict.get("company_description", ""),
            height=100
        )
        
        # Informazioni aggiuntive
        col_a, col_b = st.columns(2)
        with col_a:
            st.session_state.state_dict["year_founded"] = st.text_input(
                "Anno Fondazione", 
                value=st.session_state.state_dict.get("year_founded", "")
            )
        
        with col_b:
            st.session_state.state_dict["num_employees"] = st.text_input(
                "Numero Dipendenti", 
                value=st.session_state.state_dict.get("num_employees", "")
            )
        
        st.session_state.state_dict["target_market"] = st.text_input(
            "Mercato Target", 
            value=st.session_state.state_dict.get("target_market", "")
        )
        
        st.session_state.state_dict["area"] = st.text_input(
            "Area Geografica", 
            value=st.session_state.state_dict.get("area", "Italia")
        )
        
        st.session_state.state_dict["main_products"] = st.text_input(
            "Prodotti/Servizi Principali", 
            value=st.session_state.state_dict.get("main_products", "")
        )
        
        # Pulsante per salvare i dati
        submit_btn = st.form_submit_button("Salva Informazioni", type="primary", use_container_width=True)
        if submit_btn:
            st.success("✅ Informazioni aziendali salvate con successo!")

    # Impostazioni di generazione
    st.markdown("### Impostazioni di Generazione")
    
    # Lunghezza del testo
    length_options = {"Breve": "breve", "Media": "media", "Dettagliata": "dettagliata"}
    selected_length = st.radio(
        "Lunghezza del testo",
        options=list(length_options.keys()),
        index=1  # Default: Media
    )
    st.session_state.state_dict["length_type"] = length_options[selected_length]
    
    # Temperatura (creatività)
    st.session_state.state_dict["temperature"] = st.slider(
        "Temperatura (Creatività)",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Valori più alti = più creatività, valori più bassi = più coerenza"
    )

with col2:
    st.markdown("### Generazione Sezioni")
    
    # Lista delle sezioni disponibili
    available_sections = [
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
    
    # Selettore di sezione
    selected_section = st.selectbox(
        "Seleziona la sezione da generare",
        available_sections,
        index=0
    )
    
    # Pulsante per generare la sezione
    if st.button("✨ Genera Sezione", type="primary", use_container_width=True):
        with st.spinner(f"Generazione in corso..."):
            try:
                # Esegui la generazione
                content = generate_section(selected_section, st.session_state.state_dict)
                
                # Pulisci il contenuto
                clean_content = extract_pure_content(content)
                
                # Memorizza il risultato
                if 'generated_sections' not in st.session_state:
                    st.session_state.generated_sections = {}
                
                st.session_state.generated_sections[selected_section] = clean_content
                
                st.success(f"✅ Sezione generata con successo!")
            
            except Exception as e:
                st.error(f"Si è verificato un errore durante la generazione: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Mostra il contenuto generato
    st.markdown("### Contenuto Generato")
    
    if 'generated_sections' in st.session_state and selected_section in st.session_state.generated_sections:
        generated_content = st.session_state.generated_sections[selected_section]
        
        # Area di testo per il contenuto generato
        edited_content = st.text_area(
            "",
            value=generated_content,
            height=500,
            key=f"content_{selected_section}"
        )
        
        # Pulsante per salvare le modifiche
        col_save, col_download = st.columns(2)
        
        with col_save:
            if st.button("💾 Salva Modifiche", use_container_width=True):
                st.session_state.generated_sections[selected_section] = edited_content
                st.success("✅ Modifiche salvate!")
        
        with col_download:
            filename = selected_section.lower().replace(" ", "_").replace("'", "")
            filename = f"{filename}.txt"
            
            st.download_button(
                "📥 Scarica come TXT",
                data=edited_content,
                file_name=filename,
                mime="text/plain",
                use_container_width=True
            )
    else:
        st.info("👆 Seleziona una sezione e clicca su 'Genera Sezione' per iniziare.")

# Visualizza tutte le sezioni generate
if 'generated_sections' in st.session_state and st.session_state.generated_sections:
    st.markdown("---")
    st.markdown("### Tutte le Sezioni Generate")
    
    # Tabs per ogni sezione
    section_tabs = st.tabs(list(st.session_state.generated_sections.keys()))
    
    for i, section_name in enumerate(st.session_state.generated_sections.keys()):
        with section_tabs[i]:
            st.text_area(
                "",
                value=st.session_state.generated_sections[section_name],
                height=300,
                key=f"view_{section_name}"
            )
    
    # Pulsante per scaricare il business plan completo
    st.markdown("### Esporta Business Plan Completo")
    
    if st.button("📥 Scarica Business Plan Completo", type="primary", use_container_width=True):
        # Crea il contenuto completo
        full_content = f"# Business Plan - {st.session_state.state_dict.get('company_name', 'Azienda')}\n"
        full_content += f"Data: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        # Aggiungi le sezioni nell'ordine standard
        for section in available_sections:
            if section in st.session_state.generated_sections:
                full_content += f"## {section}\n\n"
                full_content += st.session_state.generated_sections[section]
                full_content += "\n\n"
        
        # Crea un link per il download
        filename = st.session_state.state_dict.get('company_name', 'azienda')
        filename = filename.replace(" ", "_") + ".txt"
        
        st.download_button(
            label="📄 Scarica Business Plan Completo",
            data=full_content,
            file_name=filename,
            mime="text/plain",
            use_container_width=True
        )

# Link per tornare all'applicazione principale
st.markdown("---")
st.markdown("👈 [Torna all'applicazione principale](http://localhost:8501)") 