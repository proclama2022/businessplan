#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Componente per la tab finanziaria nel business plan builder.

Questo modulo fornisce un'interfaccia Streamlit per la gestione dei dati finanziari
nel business plan builder.
"""

import streamlit as st
import os
import sys
from typing import Dict, List, Optional, Any

# Assicurati che la directory principale sia nel path per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa i componenti necessari
try:
    from financial import (
        import_financial_data, analyze_financial_data,
        generate_financial_plan_section, FinancialImportError, FinancialAnalysisError
    )
    from financial.ui import financial_dashboard
    from financial_integration import convert_financial_data_for_business_plan
except ImportError as e:
    print(f"Errore nell'importare i moduli finanziari: {e}")
    # Fallback per evitare errori fatali
    def financial_dashboard(*args, **kwargs):
        return None
    def import_financial_data(*args, **kwargs):
        raise Exception("Modulo finanziario non disponibile")
    def analyze_financial_data(*args, **kwargs):
        raise Exception("Modulo finanziario non disponibile")
    def generate_financial_plan_section(*args, **kwargs):
        return "Piano finanziario non disponibile"
    def convert_financial_data_for_business_plan(*args, **kwargs):
        return {}

def show_financial_tab():
    """
    Mostra la tab finanziaria nell'app Streamlit.
    """
    st.title("Gestione Dati Finanziari")
    
    # Verifica se ci sono dati finanziari nella sessione
    if "financial_data" not in st.session_state:
        st.session_state.financial_data = None
    
    if "financial_analysis" not in st.session_state:
        st.session_state.financial_analysis = None
    
    # Mostra la dashboard finanziaria
    analyzed_data = financial_dashboard(st.session_state.financial_data)
    
    # Aggiorna i dati finanziari nella sessione
    if analyzed_data:
        st.session_state.financial_data = analyzed_data.get("raw_data", st.session_state.financial_data)
        st.session_state.financial_analysis = analyzed_data
        
        # Aggiorna anche lo stato del business plan
        if "state_dict" in st.session_state:
            # Converti i dati finanziari in un formato utilizzabile dal business plan
            financial_data_for_bp = convert_financial_data_for_business_plan(analyzed_data)
            
            # Aggiorna lo stato
            st.session_state.state_dict["financial_data"] = financial_data_for_bp
            
            st.success("Dati finanziari aggiornati nel business plan!")

def update_financial_plan_node():
    """
    Aggiorna il nodo del piano finanziario nel business plan.
    
    Questa funzione viene chiamata quando si vuole aggiornare il piano finanziario
    nel business plan con i dati finanziari importati.
    """
    if "financial_analysis" in st.session_state and st.session_state.financial_analysis:
        # Genera il piano finanziario
        company_name = st.session_state.state_dict.get("company_name", "Azienda")
        financial_plan = generate_financial_plan_section(st.session_state.financial_analysis, company_name)
        
        # Trova il nodo del piano finanziario nella history
        for i, (node, _, _) in enumerate(st.session_state.history):
            if node == "financial_plan":
                # Aggiorna l'output
                st.session_state.history[i] = (node, st.session_state.history[i][1], financial_plan)
                break
        
        # Aggiorna l'output corrente se siamo nel nodo del piano finanziario
        if st.session_state.current_node == "financial_plan":
            st.session_state.current_output = financial_plan
        
        return True
    
    return False

def add_financial_tab_to_app():
    """
    Aggiunge la tab finanziaria all'app Streamlit.
    
    Questa funzione deve essere chiamata nel punto in cui si definiscono le tabs
    nell'app principale.
    """
    # Crea un pulsante per aggiornare il piano finanziario
    if st.button("📊 Aggiorna Piano Finanziario", key="update_financial_plan"):
        if update_financial_plan_node():
            st.success("Piano finanziario aggiornato con successo!")
            # Ricarica la pagina per mostrare i cambiamenti
            st.rerun()
        else:
            st.warning("Nessun dato finanziario disponibile. Importa prima i dati finanziari.")
    
    # Mostra la tab finanziaria
    show_financial_tab()

if __name__ == "__main__":
    # Test della tab finanziaria
    show_financial_tab()
