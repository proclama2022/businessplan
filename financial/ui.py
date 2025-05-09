#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo per l'interfaccia utente finanziaria nel business plan builder.

Questo modulo implementa i componenti UI per visualizzare i dati finanziari
importati nell'applicazione.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
from datetime import datetime

class FinancialUI:
    """
    Classe che gestisce l'interfaccia utente per i componenti finanziari.
    
    Questa classe fornisce metodi per renderizzare varie visualizzazioni finanziarie
    nell'applicazione Streamlit.
    """
    
    def __init__(self):
        """Inizializza l'interfaccia finanziaria."""
        self.data = None
        print("Interfaccia finanziaria inizializzata.")
    
    def render_financial_summary(self, summary: Dict[str, Any]) -> None:
        """
        Mostra un riepilogo visivo dei dati finanziari.
        
        Args:
            summary: Dict con il riepilogo dei dati
        """
        render_financial_summary(summary)
    
    def render_key_metrics(self, metrics: Dict[str, float]) -> None:
        """
        Mostra le metriche chiave con visualizzazioni interattive.
        
        Args:
            metrics: Dict con le metriche chiave
        """
        render_key_metrics(metrics)
    
    def render_detailed_analysis(self, financial_data: Dict[str, Any]) -> None:
        """
        Mostra un'analisi dettagliata dei dati finanziari.
        
        Args:
            financial_data: Oggetto FinancialData con i dati
        """
        render_detailed_analysis(financial_data)
    
    def setup_financial_tab(self):
        """
        Configura la tab finanziaria nell'applicazione.
        
        Questa funzione può essere usata per impostare lo stato iniziale
        della tab finanziaria.
        """
        # Inizializza lo stato se necessario
        if 'financial_data' not in st.session_state:
            st.session_state.financial_data = None

def render_financial_summary(summary: Dict[str, Any]) -> None:
    """
    Mostra un riepilogo visivo dei dati finanziari.
    
    Args:
        summary: Dict con il riepilogo dei dati
    """
    # Informazioni principali
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tipo di File", summary["metadata"]["file_type"].upper())
    with col2:
        st.metric("Data di Importazione", summary["metadata"]["import_date"][:10])
    with col3:
        st.metric("Sheet Disponibili", summary["metadata"]["total_sheets"])
    
    # Validazione
    if summary["validation"]["validation_passed"]:
        st.success("✅ Validazione dei dati completata con successo")
    else:
        st.warning("⚠️ Alcuni dati non hanno superato la validazione")
    
    # Tabella delle informazioni dettagliate
    with st.expander("📊 Dettagli Validazione", expanded=False):
        val_col1, val_col2 = st.columns(2)
        
        with val_col1:
            st.markdown("**Valori Mancanti**")
            missing_data = {k: v for k, v in summary["validation"]["missing_values"].items() if v > 0}
            if missing_data:
                st.dataframe(
                    pd.DataFrame(list(missing_data.items()), columns=["Campo", "Valori Mancanti"]),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.success("Nessun valore mancante rilevato")
        
        with val_col2:
            st.markdown("**Tipi di Dati**")
            st.dataframe(
                pd.DataFrame(list(summary["validation"]["data_types"].items()), columns=["Campo", "Tipo"]),
                hide_index=True,
                use_container_width=True
            )
    
    # Anteprima dei dati
    st.markdown("### 📄 Anteprima dei Dati")
    for sheet_name, data in summary["data_preview"].items():
        with st.expander(f"Sheet: {sheet_name}", expanded=(sheet_name == next(iter(summary["data_preview"].keys())))):
            if data:
                st.dataframe(
                    pd.DataFrame(data),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("Nessun dato disponibile per questa sezione")

def render_key_metrics(metrics: Dict[str, float]) -> None:
    """
    Mostra le metriche chiave con visualizzazioni interattive.
    
    Args:
        metrics: Dict con le metriche chiave
    """
    if not metrics:
        st.info("ℹ️ Nessuna metrica chiave disponibile")
        return
    
    # Dividi le metriche in categorie
    revenue_metrics = {k: v for k, v in metrics.items() if "ricavo" in k.lower()}
    cost_metrics = {k: v for k, v in metrics.items() if "costo" in k.lower()}
    profit_metrics = {k: v for k, v in metrics.items() if any(kw in k.lower() for kw in ["profitto", "utile"])}
    other_metrics = {k: v for k, v in metrics.items() if not any(kw in k.lower() for kw in ["ricavo", "costo", "profitto", "utile"])}

    # Funzione per creare una metrica visiva
    def display_metric(key: str, value: float, col, delta: Optional[float] = None):
        col.metric(
            label=key.replace("_", " ").title(),
            value=f"€{value:,.2f}" if isinstance(value, (int, float)) else value,
            delta=f"€{delta:,.2f}" if delta is not None else None,
            delta_color="normal" if delta is None or delta >= 0 else "inverse"
        )

    # Visualizza le metriche principali
    if revenue_metrics:
        st.markdown("### 📈 Metriche di Ricavo")
        cols = st.columns(len(revenue_metrics))
        for (key, value), col in zip(revenue_metrics.items(), cols):
            display_metric(key, value, col)
    
    if cost_metrics:
        st.markdown("### 📉 Metriche di Costo")
        cols = st.columns(len(cost_metrics))
        for (key, value), col in zip(cost_metrics.items(), cols):
            display_metric(key, value, col)
    
    if profit_metrics:
        st.markdown("### 💰 Metriche di Profitto")
        cols = st.columns(len(profit_metrics))
        for (key, value), col in zip(profit_metrics.items(), cols):
            display_metric(key, value, col)
    
    if other_metrics:
        st.markdown("### 📊 Altre Metriche")
        cols = st.columns(2)
        for i, (key, value) in enumerate(other_metrics.items()):
            display_metric(key, value, cols[i % 2])
    
    # Grafico a torta delle distribuzioni
    if revenue_metrics or cost_metrics:
        st.markdown("### 📊 Distribuzione delle Metriche")
        all_metrics = {**revenue_metrics, **cost_metrics, **profit_metrics, **other_metrics}
        
        # Filtra solo valori numerici positivi
        numeric_metrics = {k: abs(v) for k, v in all_metrics.items() if isinstance(v, (int, float)) and v != 0}
        
        if len(numeric_metrics) > 1:  # Serve almeno 2 metriche per un grafico a torta significativo
            fig = px.pie(
                values=list(numeric_metrics.values()),
                names=[k.replace("_", " ").title() for k in numeric_metrics.keys()],
                title="Distribuzione delle Metriche Finanziarie",
                color_discrete_sequence=px.colors.sequential.Teal
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        elif len(numeric_metrics) == 1:
            key, value = next(iter(numeric_metrics.items()))
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=value,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': key.replace("_", " ").title()},
                gauge={'axis': {'range': [None, value * 1.2]}}
            ))
            st.plotly_chart(fig, use_container_width=True)

def render_detailed_analysis(financial_data: Dict[str, Any]) -> None:
    """
    Mostra un'analisi dettagliata dei dati finanziari.
    
    Args:
        financial_data: Oggetto FinancialData con i dati
    """
    # Estrai i dati strutturati
    structured_data = {k: v for k, v in financial_data["raw_data"].items() if k != "text"}
    
    if not structured_data:
        st.info("ℹ️ Nessun dato strutturato disponibile per l'analisi dettagliata")
        return
    
    # Seleziona il dataset da analizzare
    dataset_options = list(structured_data.keys())
    selected_dataset = st.selectbox("Seleziona il dataset da analizzare", dataset_options)
    
    if not selected_dataset:
        return
    
    df = pd.DataFrame(structured_data[selected_dataset])
    
    if df.empty:
        st.info("ℹ️ Nessun dato disponibile per l'analisi")
        return
    
    # Analisi delle tendenze temporali (se presente una colonna data)
    date_cols = [col for col in df.columns if any(kw in col.lower() for kw in ["data", "data_", "mese", "anno", "giorno"])]
    
    if date_cols:
        date_col = date_cols[0]
        try:
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.sort_values(date_col)
            
            st.markdown(f"### 📅 Analisi delle Tendenze nel Tempo ({date_col})")
            
            # Seleziona la metrica da analizzare
            numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
            if numeric_cols:
                metric_col = st.selectbox("Seleziona la metrica da analizzare", numeric_cols)
                
                # Grafico a linee
                fig = px.line(
                    df,
                    x=date_col,
                    y=metric_col,
                    title=f"Andamento di {metric_col} nel Tempo",
                    labels={date_col: "Data", metric_col: "Valore"}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistiche di base
                col1, col2, col3 = st.columns(3)
                col1.metric("Valore Minimo", f"€{df[metric_col].min():,.2f}")
                col2.metric("Valore Medio", f"€{df[metric_col].mean():,.2f}")
                col3.metric("Valore Massimo", f"€{df[metric_col].max():,.2f}")
                
                # Analisi delle variazioni
                st.markdown("### 📊 Analisi delle Variazioni")
                df["variazione"] = df[metric_col].diff()
                df["variazione_percentuale"] = df[metric_col].pct_change() * 100
                
                change_fig = go.Figure()
                change_fig.add_trace(go.Bar(
                    x=df[date_col],
                    y=df["variazione"],
                    name="Variazione Assoluta",
                    marker_color='lightslategray'
                ))
                change_fig.add_trace(go.Scatter(
                    x=df[date_col],
                    y=df["variazione_percentuale"],
                    name="Variazione Percentuale",
                    yaxis="y2",
                    mode='lines+markers',
                    line=dict(color='firebrick', width=2)
                ))
                
                change_fig.update_layout(
                    title="Variazioni nel Tempo",
                    xaxis_title="Data",
                    yaxis_title="Variazione Assoluta",
                    yaxis2=dict(title="Variazione Percentuale (%)", overlaying="y", side="right"),
                    legend=dict(x=0.1, y=1.1, orientation="h")
                )
                
                st.plotly_chart(change_fig, use_container_width=True)
            else:
                st.info("ℹ️ Nessuna colonna numerica disponibile per l'analisi delle tendenze")
        except Exception as e:
            st.warning(f"❌ Errore nell'analisi delle tendenze temporali: {str(e)}")
    
    # Analisi comparativa tra categorie
    category_cols = [col for col in df.columns if not pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique() < 20]
    
    if category_cols:
        st.markdown("### 📊 Analisi Comparativa tra Categorie")
        category_col = st.selectbox("Seleziona la categoria da analizzare", category_cols)
        
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        if numeric_cols:
            metric_col = st.selectbox("Seleziona la metrica da confrontare", numeric_cols, key="metric_col_2")
            
            # Raggruppa per categoria e calcola la media
            grouped = df.groupby(category_col)[metric_col].mean().sort_values(ascending=False)
            
            # Grafico a barre
            fig = px.bar(
                grouped,
                x=grouped.index,
                y=metric_col,
                title=f"Media di {metric_col} per {category_col}",
                labels={category_col: "Categoria", metric_col: "Valore Medio"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabella dei dati
            with st.expander("📄 Dati Dettagliati", expanded=False):
                st.dataframe(
                    df[[category_col, metric_col]],
                    hide_index=True,
                    use_container_width=True
                )
        else:
            st.info("ℹ️ Nessuna colonna numerica disponibile per l'analisi comparativa")
    
    # Analisi della distribuzione
    st.markdown("### 📊 Distribuzione dei Dati")
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    
    if numeric_cols:
        dist_col = st.selectbox("Seleziona la colonna da analizzare", numeric_cols, key="dist_col")
        
        # Istogramma
        fig = px.histogram(
            df,
            x=dist_col,
            nbins=30,
            title=f"Distribuzione di {dist_col}",
            labels={dist_col: "Valore", "count": "Frequenza"}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistiche di distribuzione
        col1, col2, col3 = st.columns(3)
        col1.metric("Asimmetria", f"{df[dist_col].skew():.2f}")
        col2.metric("Curtosi", f"{df[dist_col].kurtosis():.2f}")
        col3.metric("Deviazione Standard", f"€{df[dist_col].std():,.2f}")
    else:
        st.info("ℹ️ Nessuna colonna numerica disponibile per l'analisi della distribuzione")

if __name__ == "__main__":
    # Test dell'interfaccia utente finanziaria
    st.set_page_config(page_title="Business Plan Builder - UI Finanziaria", layout="wide")
    st.title("Business Plan Builder - UI Finanziaria")
    
    # Esempio di dati di test
    test_summary = {
        "metadata": {
            "file_path": "test_financial_data.xlsx",
            "file_type": "xlsx",
            "import_date": datetime.now().isoformat(),
            "total_sheets": 2,
            "validation_passed": True
        },
        "validation": {
            "total_rows": 100,
            "total_columns": 5,
            "missing_values": {"Ricavi": 0, "Costi": 0, "Profitto": 0},
            "data_types": {"Data": "datetime64[ns]", "Ricavi": "float64", "Costi": "float64", "Profitto": "float64"},
            "validation_passed": True
        },
        "data_preview": {
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
        }
    }
    
    test_metrics = {
        "ricavi_totali": 100000,
        "costi_totali": 60000,
        "profitto_netto": 40000,
        "margine_profitto": 40
    }
    
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
            "import_date": datetime.now().isoformat(),
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
    
    st.markdown("## 📄 Riepilogo Finanziario")
    render_financial_summary(test_summary)
    
    st.markdown("## 📈 Metriche Chiave")
    render_key_metrics(test_metrics)
    
    st.markdown("## 🔍 Analisi Dettagliata")
    render_detailed_analysis(test_financial_data)
