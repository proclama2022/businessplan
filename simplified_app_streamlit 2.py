#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Versione semplificata dell'applicazione Business Plan Builder.

Questa versione è ottimizzata per commercialisti e utenti meno tecnici,
con un'interfaccia più semplice e intuitiva.
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

# Aggiungi la directory corrente al path di Python
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importa i componenti necessari
try:
    from config import Config
    from state import BusinessPlanState, initialize_state
    from graph_builder import build_business_plan_graph
    from database.vector_store import VectorDatabase
    from simplified_financial_tab import add_simplified_financial_tab
    from simplified_navigation import simplified_navigation_bar, add_context_help, save_current_section_output
except ImportError as e:
    st.error(f"Errore nell'importazione dei moduli: {e}")

# Esegui l'app se il file viene eseguito direttamente
if __name__ == "__main__":
    run_simplified_app()

def run_simplified_app():
    """
    Funzione principale per eseguire l'applicazione in modalità semplificata.
    Questa funzione viene chiamata da app_streamlit.py quando l'utente sceglie
    la modalità semplificata.
    """
    # --- Configurazione della pagina ---
    st.set_page_config(
        page_title="Business Plan Builder - Versione Semplificata",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Verifica se siamo nella schermata iniziale
    is_initial_screen = st.session_state.current_node == "initial_planning" and not st.session_state.current_output

    # --- Barra Laterale Semplificata ---
    with st.sidebar:
        # Logo e titolo
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem;">
            <h1 style="color: #0066cc; margin-bottom: 0.5rem;">Business Plan</h1>
            <p style="color: #6c757d; font-size: 0.9rem;">Strumento semplificato</p>
        </div>
        """, unsafe_allow_html=True)

        # Separatore
        st.markdown('<hr style="margin: 0.5rem 0 1.5rem 0;">', unsafe_allow_html=True)

        # Informazioni aziendali semplificate
        if is_initial_screen:
            st.subheader("📋 Informazioni Aziendali")
            company_name = st.text_input(
                "Nome Azienda",
                value=st.session_state.state_dict.get("company_name", ""),
                help="Inserisci il nome della tua azienda"
            )

            # Aggiorna lo stato se il nome è cambiato
            if company_name != st.session_state.state_dict.get("company_name", ""):
                st.session_state.state_dict["company_name"] = company_name
                st.session_state.state_dict["document_title"] = f"Business Plan - {company_name}"

        # --- Navigazione semplificata ---
        st.sidebar.divider()
        st.sidebar.subheader("🧭 Sezioni")

        # Lista semplificata delle sezioni
        simplified_sections = [
            ("executive_summary", "Sommario Esecutivo"),
            ("company_description", "Descrizione Azienda"),
            ("products_and_services", "Prodotti e Servizi"),
            ("market_analysis", "Analisi di Mercato"),
            ("financial_plan", "Piano Finanziario"),
            ("document_generation", "Genera Documento")
        ]

        # Crea pulsanti per ogni sezione
        for section_key, section_name in simplified_sections:
            # Evidenzia la sezione corrente
            is_current = section_key == st.session_state.current_node
            button_style = "primary" if is_current else "secondary"

            # Verifica se questa sezione ha già contenuto
            has_content = False
            for node_name, _, output in st.session_state.history:
                if node_name == section_key and output:
                    has_content = True
                    break

            # Aggiungi un'icona per indicare lo stato
            icon = "✅ " if has_content else "📝 "
            if is_current:
                icon = "🔍 "

            if st.sidebar.button(f"{icon}{section_name}", key=f"nav_{section_key}", type=button_style, use_container_width=True):
                st.session_state.current_node = section_key
                st.session_state.current_output = ""
                for node_name, _, output in st.session_state.history:
                    if node_name == section_key:
                        st.session_state.current_output = output
                        break
                st.rerun()

        # Aggiungi una guida rapida
        with st.sidebar.expander("❓ Guida Rapida", expanded=False):
            st.markdown("""
            ### Come usare l'applicazione:

            1. Seleziona una sezione dalla barra laterale
            2. Genera il contenuto con il pulsante "Genera"
            3. Modifica il testo se necessario
            4. Passa alla sezione successiva
            5. Alla fine, genera il documento completo

            Per assistenza, contatta il supporto.
            """)

        # Pulsante per tornare alla modalità completa
        if st.sidebar.button("🔄 Torna alla Modalità Completa", help="Torna all'interfaccia completa"):
            st.session_state.simplified_mode = False
            st.rerun()

    # --- Area Principale Semplificata ---
    if is_initial_screen:
        # Schermata di benvenuto semplificata
        st.title("📊 Business Plan Builder")
        st.markdown("### Benvenuto nella versione semplificata")

        st.markdown("""
        Questo strumento ti aiuta a creare un business plan professionale in modo semplice e veloce.

        **Per iniziare:**
        1. Inserisci il nome della tua azienda nella barra laterale
        2. Clicca su "Iniziamo!" per procedere
        3. Segui le istruzioni per completare ogni sezione
        """)

        # Pulsante per iniziare
        if st.button("Iniziamo!", type="primary", key="welcome_start"):
            st.session_state.current_node = "executive_summary"
            st.rerun()
    else:
        # Interfaccia principale semplificata
        # Mostra il titolo della sezione corrente
        current_node_name = st.session_state.current_node.replace('_', ' ').title()
        st.title(current_node_name)

        # Aggiungi aiuto contestuale
        add_context_help(st.session_state.current_node)

        # Barra di navigazione semplificata
        simplified_navigation_bar(
            simplified_sections,
            st.session_state.current_node
        )

        # Contenuto principale in un'unica tab
        with st.container(border=True):
            # Istruzioni contestuali semplificate
            section_instructions = {
                "executive_summary": "Riassumi i punti chiave del tuo business plan",
                "company_description": "Descrivi la tua azienda, la sua missione e visione",
                "products_and_services": "Descrivi i prodotti o servizi offerti",
                "market_analysis": "Analizza il mercato di riferimento",
                "financial_plan": "Descrivi il piano finanziario della tua azienda",
                "document_generation": "Genera il documento finale del business plan"
            }

            current_instruction = section_instructions.get(
                st.session_state.current_node,
                "Compila questa sezione del business plan"
            )

            # Mostra le istruzioni
            st.caption(current_instruction)

            # Area di output semplificata
            output_area = st.text_area(
                "",  # Rimuovi l'etichetta
                value=st.session_state.current_output,
                height=350,
                key=f"output_{st.session_state.current_node}",
                placeholder="Il contenuto generato apparirà qui..."
            )

            # Pulsanti di azione semplificati
            col1, col2 = st.columns(2)

            with col1:
                # Bottone per generare contenuto
                generate_btn = st.button(
                    "✨ Genera Contenuto",
                    key="generate",
                    use_container_width=True,
                    type="primary"
                )

            with col2:
                # Bottone per salvare modifiche
                save_btn = st.button(
                    "💾 Salva Modifiche",
                    key="save",
                    use_container_width=True
                )

            # Logica per la generazione del contenuto
            if generate_btn:
                with st.spinner("Generazione in corso..."):
                    # Qui andrebbe la logica di generazione del contenuto
                    # Per ora usiamo un placeholder
                    st.session_state.current_output = f"Contenuto di esempio per la sezione {current_node_name}."
                    
                    # Salva automaticamente nella cronologia usando la funzione dedicata
                    save_current_section_output(
                        st.session_state.current_node,
                        st.session_state.current_output,
                        st.session_state.history
                    )
                    
                    st.rerun()

            # Logica per il salvataggio delle modifiche
            if save_btn and output_area:
                st.session_state.current_output = output_area
                
                # Salva automaticamente nella cronologia usando la funzione dedicata
                save_current_section_output(
                    st.session_state.current_node,
                    output_area,
                    st.session_state.history
                )
                
                st.success("✅ Modifiche salvate con successo!")

        # Se siamo nella sezione finanziaria, mostra la tab finanziaria semplificata
        if st.session_state.current_node == "financial_plan":
            st.markdown("---")
            add_simplified_financial_tab()

    # --- Footer semplificato ---
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin-top: 1rem;">
        <p style="color: #6c757d; font-size: 0.9rem;">
            <strong>Business Plan Builder - Versione Semplificata</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

# Esegui l'app se il file viene eseguito direttamente
if __name__ == "__main__":
    run_simplified_app()
