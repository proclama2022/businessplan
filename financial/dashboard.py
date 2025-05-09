#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo per la dashboard finanziaria nel business plan builder.

Questo modulo fornisce funzionalità per visualizzare e analizzare i dati finanziari
importati nell'applicazione.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import os

# Importa i moduli necessari
try:
    from financial.financial_importer import (
        import_financial_data, FinancialData, FinancialImportError,
        get_financial_summary, extract_key_financial_metrics
    )
    from financial.ui import render_financial_summary, render_key_metrics, render_detailed_analysis
except ImportError as e:
    print(f"Errore nell'importare i moduli finanziari: {e}")
    # Fallback per evitare errori fatali
    def render_financial_summary(*args, **kwargs): return None
    def render_key_metrics(*args, **kwargs): return None
    def render_detailed_analysis(*args, **kwargs): return None

def financial_dashboard(financial_data: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Dashboard principale per l'analisi finanziaria.
    
    Args:
        financial_data: Dati finanziari esistenti (opzionale)
        
    Returns:
        Dict con i dati finanziari analizzati
    """
    st.subheader("📊 Importazione e Analisi Dati Finanziari")
    
    # Inizializza lo stato della sessione per i dati finanziari
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = None
    
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
                # Crea una directory temporanea se non esiste
                temp_dir = tempfile.mkdtemp()
                file_path = os.path.join(temp_dir, uploaded_file.name)
                
                # Salva il file temporaneamente
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                # Importa i dati
                imported_data = import_financial_data(file_path)
                
                # Aggiorna lo stato della sessione
                st.session_state.financial_data = imported_data
                st.success("✅ Dati finanziari importati con successo!")
                st.rerun()
                
            except FinancialImportError as e:
                st.error(f"❌ Errore nell'importazione dei dati finanziari: {str(e)}")
            except Exception as e:
                st.error(f"❌ Errore imprevisto durante l'importazione: {str(e)}")
    
    # Mostra i dati esistenti se disponibili
    if st.session_state.financial_data:
        st.success("✅ Dati finanziari disponibili")
        
        # Mostra il riepilogo dei dati
        with st.expander("📄 Riepilogo Dati Finanziari", expanded=True):
            summary = get_financial_summary(st.session_state.financial_data)
            render_financial_summary(summary)
            
        # Mostra le metriche chiave
        with st.expander("📈 Metriche Finanziarie Chiave", expanded=True):
            metrics = extract_key_financial_metrics(st.session_state.financial_data)
            render_key_metrics(metrics)
            
        # Mostra l'analisi dettagliata
        with st.expander("🔍 Analisi Dettagliata", expanded=False):
            render_detailed_analysis(st.session_state.financial_data)
            
        # Opzioni di esportazione
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Esporta Riepilogo (.txt)", use_container_width=True):
                export_summary = generate_financial_summary_text(st.session_state.financial_data)
                st.download_button(
                    label="Conferma Esportazione",
                    data=export_summary,
                    file_name=f"riepilogo_finanziario_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
                
        with col2:
            if st.button("📊 Esporta Dati Grezzi (.json)", use_container_width=True):
                st.download_button(
                    label="Conferma Esportazione",
                    data=json.dumps(st.session_state.financial_data.raw_data, indent=2),
                    file_name=f"dati_grezzi_finanziari_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
                
        return st.session_state.financial_data
        
    elif financial_data:
        # Usa i dati forniti come input
        st.session_state.financial_data = financial_data
        st.success("✅ Dati finanziari disponibili")
        return financial_data
        
    else:
        st.info("ℹ️ Nessun dato finanziario disponibile. Carica un file per iniziare.")
        return None

def generate_financial_summary_text(financial_data: FinancialData) -> str:
    """
    Genera un riepilogo testuale dei dati finanziari.
    
    Args:
        financial_data: Oggetto FinancialData con i dati
        
    Returns:
        Stringa con il riepilogo testuale
    """
    summary = f"Riepilogo Dati Finanziari\n"
    summary += f"========================\n\n"
    
    # Informazioni sui metadati
    summary += "Metadati:\n"
    summary += f"  File: {financial_data.metadata['file_path']}\n"
    summary += f"  Tipo: {financial_data.metadata['file_type']}\n"
    summary += f"  Data Importazione: {financial_data.metadata['import_date']}\n"
    summary += f"  Numero di sheet: {financial_data.metadata['total_sheets']}\n"
    summary += f"  Validazione: {'Passata' if financial_data.metadata['validation_passed'] else 'Non passata'}\n\n"
    
    # Report di validazione
    summary += "Report di Validazione:\n"
    summary += f"  Totale righe: {financial_data.validation_report['total_rows']}\n"
    summary += f"  Totale colonne: {financial_data.validation_report['total_columns']}\n"
    
    summary += "  Valori mancanti:\n"
    for col, count in financial_data.validation_report['missing_values'].items():
        summary += f"    {col}: {count} valori mancanti\n"
        
    summary += "  Tipi di dati:\n"
    for col, dtype in financial_data.validation_report['data_types'].items():
        summary += f"    {col}: {dtype}\n"
        
    summary += f"  Validazione completata: {'Sì' if financial_data.validation_report['validation_passed'] else 'No'}\n\n"
    
    # Anteprima dei dati
    summary += "Anteprima dei Dati:\n"
    for sheet_name, data in financial_data.raw_data.items():
        if sheet_name != "text" and isinstance(data, list) and data:
            summary += f"  Sheet: {sheet_name}\n"
            for i, row in enumerate(data[:3]):  # Prime 3 righe
                summary += f"    Riga {i+1}: {row}\n"
    
    return summary

# Funzioni di visualizzazione (da implementare in ui.py)
def render_financial_summary(summary: Dict[str, Any]) -> None:
    """
    Mostra il riepilogo dei dati finanziari.
    
    Args:
        summary: Dict con il riepilogo dei dati
    """
    # Importa l'implementazione completa dalla UI
    from financial.ui import render_financial_summary as real_render
    real_render(summary)

def render_key_metrics(metrics: Dict[str, float]) -> None:
    """
    Mostra le metriche chiave con visualizzazioni interattive.
    
    Args:
        metrics: Dict con le metriche chiave
    """
    # Importa l'implementazione completa dalla UI
    from financial.ui import render_key_metrics as real_render
    real_render(metrics)

def render_detailed_analysis(financial_data: FinancialData) -> None:
    """
    Mostra un'analisi dettagliata dei dati finanziari.
    
    Args:
        financial_data: Oggetto FinancialData con i dati
    """
    # Importa l'implementazione completa dalla UI
    from financial.ui import render_detailed_analysis as real_render
    real_render(financial_data)

if __name__ == "__main__":
    # Test della dashboard finanziaria
    financial_dashboard()
