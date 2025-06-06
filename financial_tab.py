#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo per la tab finanziaria nell'applicazione Streamlit.

Questo modulo implementa la tab finanziaria per l'integrazione con le funzionalità di analisi finanziaria.
"""

import streamlit as st
from financial.ui import FinancialUI
from financial.dashboard import financial_dashboard

def add_financial_tab_to_app():
    """
    Aggiunge la tab finanziaria all'applicazione Streamlit.
    
    Questa funzione crea una tab finanziaria che permette all'utente di:
    - Caricare file con dati finanziari
    - Visualizzare riepiloghi e metriche chiave
    - Eseguire analisi dettagliata
    - Esportare i dati
    """
    # Ottieni o crea l'istanza di FinancialUI
    if 'financial_ui' not in st.session_state:
        st.session_state.financial_ui = FinancialUI()
    
    financial_ui = st.session_state.financial_ui
    
    st.markdown("## 💰 Analisi Finanziaria")
    st.caption("Carica e analizza i dati finanziari per il tuo business plan")
    
    # Ottieni i dati finanziari dallo stato della sessione
    financial_data = st.session_state.get('financial_data', None)
    
    # Crea una tab per le diverse funzionalità finanziarie
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard", 
        "📄 Riepilogo", 
        "📈 Metriche Chiave", 
        "🔍 Analisi Dettagliata"
    ])
    
    # Dashboard finanziaria
    with tab1:
        st.markdown("### 📊 Dashboard Finanziaria")
        st.info("Usa il caricamento file qui sotto per iniziare l'analisi")
        
        # Area per il caricamento del file
        uploaded_file = st.file_uploader(
            "Carica un file con dati finanziari (Excel, CSV o PDF)",
            type=['xlsx', 'xls', 'csv', 'pdf'],
            help="Supporta file Excel (.xlsx, .xls), CSV (.csv) e PDF (.pdf)"
        )
        
        # Bottone per importare i dati
        if st.button("📥 Importa Dati Finanziari", type="primary", use_container_width=True) and uploaded_file:
            with st.spinner("Importazione in corso..."):
                try:
                    # Crea una directory temporanea
                    import tempfile
                    import os
                    
                    temp_dir = tempfile.mkdtemp()
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    
                    # Salva il file temporaneamente
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    
                    # Importa i dati
                    from financial.financial_importer import import_financial_data
                    imported_data = import_financial_data(file_path)
                    
                    # Aggiorna lo stato della sessione
                    st.session_state.financial_data = imported_data
                    st.success("✅ Dati finanziari importati con successo!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Errore nell'importazione dei dati finanziari: {str(e)}")
    
    # Riepilogo finanziario
    with tab2:
        st.markdown("### 📄 Riepilogo Finanziario")
        if financial_data:
            financial_ui.render_financial_summary(financial_data)
        else:
            st.info("ℹ️ Nessun dato finanziario disponibile. Carica un file per iniziare.")
    
    # Metriche chiave
    with tab3:
        st.markdown("### 📈 Metriche Finanziarie Chiave")
        if financial_data:
            metrics = extract_key_financial_metrics(financial_data)
            financial_ui.render_key_metrics(metrics)
        else:
            st.info("ℹ️ Nessun dato finanziario disponibile. Carica un file per iniziare.")
    
    # Analisi dettagliata
    with tab4:
        st.markdown("### 🔍 Analisi Dettagliata")
        if financial_data:
            financial_ui.render_detailed_analysis(financial_data)
        else:
            st.info("ℹ️ Nessun dato finanziario disponibile. Carica un file per iniziare.")
    
    # Sezione per l'assistente finanziario
    st.markdown("## 💼 Assistente Finanziario")
    st.caption("Chiedi all'assistente informazioni specifiche sui tuoi dati finanziari")
    
    # Campo per le domande dell'utente
    user_query = st.text_area(
        "Cosa vuoi sapere sui tuoi dati finanziari?",
        placeholder="Esempio: Qual è il margine di profitto medio? Quali sono le spese principali?...",
        height=100
    )
    
    # Bottone per inviare la domanda
    if st.button("❓ Fai una Domanda", type="secondary", use_container_width=True) and user_query:
        with st.spinner("Analisi in corso..."):
            try:
                # Ottieni i suggerimenti dall'integrazione finanziaria
                from financial_integration import get_financial_tips
                tips = get_financial_tips(financial_data)
                
                # Mostra i suggerimenti contestuali
                if tips:
                    st.markdown("### 📝 Suggerimenti Finanziari")
                    for tip in tips:
                        st.markdown(f"- {tip}")
                else:
                    st.info("Nessun suggerimento generato. Verifica i dati o riprova con una domanda diversa.")
            except Exception as e:
                st.error(f"Errore nell'elaborazione della domanda: {e}")

def extract_key_financial_metrics(financial_data):
    """
    Estrae le metriche finanziarie chiave dai dati.
    """
    # Implementazione di esempio
    return {
        "roi": "15%",
        "profitability": "22%",
        "break_even": "6 mesi",
        "cash_flow": "Positivo",
        "growth_rate": "8% annuo"
    }

if __name__ == "__main__":
    # Test della tab finanziaria
    st.set_page_config(page_title="Business Plan Builder - Finanza", layout="wide")
    st.title("Business Plan Builder - Tab Finanziaria")
    
    # Test dei dati di esempio
    test_financial_data = {
        "raw_data": {
            "Sheet1": [
                {"Data": "2023-01-01", "Ricavi": 10000, "Costi": 6000, "Profitto": 4000},
                {"Data": "2023-02-01", "Ricavi": 12000, "Costi": 7000, "Profitto": 5000},
                {"Data": "2023-03-01", "Ricavi": 15000, "Costi": 8000, "Profitto": 7000}
            ],
            "Sheet2": [
                {"Categoria": "A", "Valore": 100},
                {"Categoria": "B", "Valore": 200},
                {"Categoria": "C", "Valore": 150}
            ]
        },
        "metadata": {
            "file_path": "test_financial_data.xlsx",
            "file_type": "xlsx",
            "import_date": "2025-05-08T18:26:00",
            "total_sheets": 2,
            "validation_passed": True
        },
        "validation_report": {
            "total_rows": 100,
            "total_columns": 5,
            "missing_values": {"Ricavi": 0, "Costi": 0, "Profitto": 0},
            "data_types": {"Data": "datetime64[ns]", "Ricavi": "float64", "Costi": "float64", "Profitto": "float64"},
            "validation_passed": True
        }
    }
    
    st.session_state.financial_data = test_financial_data
    add_financial_tab_to_app()
