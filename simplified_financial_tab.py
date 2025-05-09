#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo semplificato per la tab finanziaria nell'applicazione Streamlit.

Questo modulo implementa una versione semplificata della tab finanziaria
per l'integrazione con le funzionalità di analisi finanziaria, ottimizzata
per commercialisti e utenti meno tecnici.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
import os
import tempfile

# Importa i moduli finanziari con gestione degli errori
try:
    from financial.ui import FinancialUI
    from financial.dashboard import financial_dashboard
except ImportError as e:
    # Crea stub per evitare errori
    class FinancialUI:
        def __init__(self):
            self.data = None
        
        def render_financial_summary(self, *args, **kwargs):
            st.info("Funzionalità finanziaria non disponibile")
        
        def render_key_metrics(self, *args, **kwargs):
            st.info("Funzionalità finanziaria non disponibile")
        
        def render_detailed_analysis(self, *args, **kwargs):
            st.info("Funzionalità finanziaria non disponibile")

def add_simplified_financial_tab():
    """
    Aggiunge una tab finanziaria semplificata all'applicazione Streamlit.
    
    Questa funzione crea una tab finanziaria semplificata che permette all'utente di:
    - Caricare file con dati finanziari
    - Visualizzare riepiloghi e metriche chiave in modo semplice
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
    
    # Area per il caricamento del file (semplificata)
    uploaded_file = st.file_uploader(
        "Carica un file Excel o CSV con i tuoi dati finanziari",
        type=['xlsx', 'xls', 'csv'],
        help="Supporta file Excel (.xlsx, .xls) e CSV (.csv)"
    )
    
    # Bottone per importare i dati
    if st.button("📥 Importa Dati", type="primary", use_container_width=True) and uploaded_file:
        with st.spinner("Importazione in corso..."):
            try:
                # Crea una directory temporanea
                temp_dir = tempfile.mkdtemp()
                file_path = os.path.join(temp_dir, uploaded_file.name)
                
                # Salva il file temporaneamente
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                # Importa i dati
                try:
                    from financial.financial_importer import import_financial_data
                    imported_data = import_financial_data(file_path)
                except ImportError:
                    # Fallback semplice se il modulo non è disponibile
                    if uploaded_file.name.endswith(('.xlsx', '.xls')):
                        import_data = pd.read_excel(file_path)
                    else:
                        import_data = pd.read_csv(file_path)
                    
                    # Crea una struttura dati semplificata
                    imported_data = {
                        "raw_data": {
                            "Sheet1": import_data.to_dict('records')
                        },
                        "metadata": {
                            "file_path": file_path,
                            "file_type": uploaded_file.name.split('.')[-1],
                            "import_date": pd.Timestamp.now().isoformat(),
                            "total_sheets": 1,
                            "validation_passed": True
                        },
                        "validation_report": {
                            "total_rows": len(import_data),
                            "total_columns": len(import_data.columns),
                            "missing_values": {col: import_data[col].isna().sum() for col in import_data.columns},
                            "data_types": {col: str(import_data[col].dtype) for col in import_data.columns},
                            "validation_passed": True
                        }
                    }
                
                # Aggiorna lo stato della sessione
                st.session_state.financial_data = imported_data
                st.success("✅ Dati finanziari importati con successo!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Errore nell'importazione dei dati: {str(e)}")
    
    # Se ci sono dati, mostra una visualizzazione semplificata
    if financial_data:
        # Visualizzazione semplificata dei dati
        st.markdown("### 📊 Riepilogo Finanziario")
        
        # Estrai i dati in un formato più semplice
        try:
            sheet_name = next(iter(financial_data["raw_data"].keys()))
            data = financial_data["raw_data"][sheet_name]
            df = pd.DataFrame(data)
            
            # Mostra una tabella semplificata
            st.dataframe(df.head(10), use_container_width=True)
            
            # Identifica colonne numeriche per grafici
            numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
            
            if numeric_cols:
                # Selezione semplificata della colonna da visualizzare
                selected_col = st.selectbox(
                    "Seleziona una colonna da visualizzare nel grafico:",
                    numeric_cols
                )
                
                # Grafico a barre semplice
                fig = px.bar(
                    df,
                    y=selected_col,
                    title=f"Grafico di {selected_col}",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistiche di base
                st.markdown("### 📈 Statistiche di Base")
                col1, col2, col3 = st.columns(3)
                col1.metric("Valore Minimo", f"{df[selected_col].min():,.2f}")
                col2.metric("Valore Medio", f"{df[selected_col].mean():,.2f}")
                col3.metric("Valore Massimo", f"{df[selected_col].max():,.2f}")
            
            # Pulsante per esportare
            if st.button("📥 Esporta Dati", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Scarica CSV",
                    data=csv,
                    file_name=f"dati_finanziari_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        except Exception as e:
            st.error(f"Errore nella visualizzazione dei dati: {str(e)}")
    else:
        # Messaggio semplificato se non ci sono dati
        st.info("👆 Carica un file Excel o CSV per iniziare l'analisi finanziaria")
        
        # Esempio di dati
        with st.expander("🔍 Esempio di formato dati", expanded=False):
            st.markdown("""
            ### Formato consigliato per i dati
            
            Per ottenere i migliori risultati, il tuo file Excel o CSV dovrebbe avere:
            
            - Una riga di intestazione con i nomi delle colonne
            - Colonne per date, ricavi, costi, profitti, ecc.
            - Dati numerici per le analisi finanziarie
            
            **Esempio:**
            
            | Data | Ricavi | Costi | Profitto |
            |------|--------|-------|----------|
            | 2023-01 | 10000 | 6000 | 4000 |
            | 2023-02 | 12000 | 7000 | 5000 |
            | 2023-03 | 15000 | 8000 | 7000 |
            """)

def extract_key_financial_metrics(financial_data):
    """
    Estrae le metriche finanziarie chiave dai dati in modo semplificato.
    """
    # Implementazione semplificata
    try:
        sheet_name = next(iter(financial_data["raw_data"].keys()))
        data = financial_data["raw_data"][sheet_name]
        df = pd.DataFrame(data)
        
        # Cerca colonne comuni
        metrics = {}
        
        # Cerca colonne di ricavi
        revenue_cols = [col for col in df.columns if any(kw in col.lower() for kw in ["ricav", "revenue", "vendite", "sales"])]
        if revenue_cols:
            metrics["ricavi_totali"] = df[revenue_cols[0]].sum()
        
        # Cerca colonne di costi
        cost_cols = [col for col in df.columns if any(kw in col.lower() for kw in ["cost", "spese", "expenses"])]
        if cost_cols:
            metrics["costi_totali"] = df[cost_cols[0]].sum()
        
        # Calcola profitto se possibile
        if revenue_cols and cost_cols:
            metrics["profitto_netto"] = metrics["ricavi_totali"] - metrics["costi_totali"]
            if metrics["ricavi_totali"] > 0:
                metrics["margine_profitto"] = (metrics["profitto_netto"] / metrics["ricavi_totali"]) * 100
        
        return metrics
    
    except Exception as e:
        print(f"Errore nell'estrazione delle metriche: {e}")
        return {
            "roi": "N/A",
            "profitability": "N/A",
            "break_even": "N/A",
            "cash_flow": "N/A",
            "growth_rate": "N/A"
        }

if __name__ == "__main__":
    # Test della tab finanziaria semplificata
    st.set_page_config(page_title="Business Plan Builder - Finanza Semplificata", layout="wide")
    st.title("Business Plan Builder - Tab Finanziaria Semplificata")
    
    add_simplified_financial_tab()
