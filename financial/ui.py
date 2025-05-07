#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Componenti UI per la gestione dei dati finanziari nel business plan builder.

Questo modulo fornisce componenti Streamlit per importare, visualizzare e
analizzare dati finanziari, con particolare attenzione ai bilanci CEE italiani.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any, Tuple
import json
import os
import tempfile

from .cee_schema import FinancialStatement
from .cee_parser import CEEParseError
from .financial_importer import import_financial_data, FinancialImportError
from .financial_analyzer import analyze_financial_data, generate_financial_plan_section, FinancialAnalysisError

def financial_data_uploader() -> Dict[str, Any]:
    """
    Componente Streamlit per caricare dati finanziari.
    
    Returns:
        Dict[str, Any]: Dati finanziari importati o None se non caricati
    """
    st.subheader("Carica Dati Finanziari")
    
    # Opzioni di caricamento
    upload_option = st.radio(
        "Seleziona la fonte dei dati finanziari:",
        ["Carica file", "Usa dati di esempio"],
        horizontal=True
    )
    
    financial_data = None
    
    if upload_option == "Carica file":
        uploaded_file = st.file_uploader(
            "Carica un file di bilancio CEE (CSV, Excel, JSON)",
            type=["csv", "xlsx", "xls", "json"]
        )
        
        if uploaded_file is not None:
            try:
                with st.spinner("Importazione dei dati finanziari in corso..."):
                    # Determina il tipo di file
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                    
                    # Opzioni specifiche per tipo di file
                    if file_extension == ".csv":
                        delimiter = st.selectbox("Delimitatore CSV:", [",", ";", "\t"], index=1)
                        encoding = st.selectbox("Encoding:", ["utf-8", "latin1", "iso-8859-1"], index=0)
                        financial_data = import_financial_data(
                            uploaded_file, 
                            file_name=uploaded_file.name,
                            delimiter=delimiter,
                            encoding=encoding
                        )
                    elif file_extension in [".xlsx", ".xls"]:
                        # Leggi il file Excel per ottenere i nomi dei fogli
                        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        
                        try:
                            xls = pd.ExcelFile(tmp_path)
                            sheet_names = xls.sheet_names
                            
                            # Permetti all'utente di selezionare un foglio
                            sheet_name = st.selectbox("Seleziona il foglio Excel:", sheet_names)
                            
                            financial_data = import_financial_data(
                                uploaded_file,
                                file_name=uploaded_file.name,
                                sheet_name=sheet_name
                            )
                        finally:
                            # Rimuovi il file temporaneo
                            if os.path.exists(tmp_path):
                                os.unlink(tmp_path)
                    else:  # JSON
                        financial_data = import_financial_data(
                            uploaded_file,
                            file_name=uploaded_file.name
                        )
                
                if financial_data:
                    st.success("Dati finanziari importati con successo!")
                    
                    # Mostra informazioni di base
                    st.write(f"**Azienda:** {financial_data.get('company_name', 'N/A')}")
                    st.write(f"**Anno:** {financial_data.get('year', 'N/A')}")
                    
                    # Mostra eventuali errori di validazione
                    validation = financial_data.get("validation", {})
                    if not validation.get("is_valid", True):
                        st.warning("Il bilancio contiene alcune incongruenze:")
                        for error in validation.get("errors", []):
                            st.write(f"- {error}")
            except (CEEParseError, FinancialImportError) as e:
                st.error(f"Errore nell'importazione dei dati finanziari: {str(e)}")
            except Exception as e:
                st.error(f"Errore imprevisto: {str(e)}")
    else:  # Usa dati di esempio
        st.info("Caricamento dei dati di esempio...")
        
        # Carica i dati di esempio
        try:
            # Percorso relativo al file di esempio
            example_path = os.path.join(os.path.dirname(__file__), "example_data", "example_financial_statement.json")
            
            if os.path.exists(example_path):
                financial_data = import_financial_data_from_path(example_path)
                st.success("Dati di esempio caricati con successo!")
            else:
                st.error("File di esempio non trovato.")
        except Exception as e:
            st.error(f"Errore nel caricamento dei dati di esempio: {str(e)}")
    
    return financial_data

def financial_data_analyzer(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Componente Streamlit per analizzare dati finanziari.
    
    Args:
        financial_data: Dati finanziari importati
        
    Returns:
        Dict[str, Any]: Dati finanziari analizzati
    """
    st.subheader("Analisi Finanziaria")
    
    analyzed_data = None
    
    if financial_data:
        try:
            with st.spinner("Analisi dei dati finanziari in corso..."):
                analyzed_data = analyze_financial_data(financial_data)
            
            st.success("Analisi completata!")
        except FinancialAnalysisError as e:
            st.error(f"Errore nell'analisi dei dati finanziari: {str(e)}")
        except Exception as e:
            st.error(f"Errore imprevisto: {str(e)}")
    
    return analyzed_data

def display_balance_sheet(financial_data: Dict[str, Any]) -> None:
    """
    Visualizza lo stato patrimoniale.
    
    Args:
        financial_data: Dati finanziari importati
    """
    st.subheader("Stato Patrimoniale")
    
    balance_sheet = financial_data.get("balance_sheet", {})
    
    # Crea due colonne per attivo e passivo
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### ATTIVO")
        
        # Crea un DataFrame per le attività
        assets_data = []
        for code, account in balance_sheet.get("assets", {}).items():
            assets_data.append({
                "Codice": code,
                "Voce": account.get("name", ""),
                "Valore": account.get("value", 0),
                "Anno Precedente": account.get("previous_value", None)
            })
        
        if assets_data:
            assets_df = pd.DataFrame(assets_data)
            st.dataframe(assets_df, use_container_width=True)
            
            # Visualizza il totale
            st.write(f"**Totale Attivo:** {balance_sheet.get('total_assets', 0):,.2f} €")
        else:
            st.info("Nessun dato disponibile per l'attivo.")
    
    with col2:
        st.write("### PASSIVO E PATRIMONIO NETTO")
        
        # Crea un DataFrame per le passività
        liabilities_data = []
        for code, account in balance_sheet.get("liabilities", {}).items():
            liabilities_data.append({
                "Codice": code,
                "Voce": account.get("name", ""),
                "Valore": account.get("value", 0),
                "Anno Precedente": account.get("previous_value", None)
            })
        
        # Aggiungi il patrimonio netto
        equity_data = []
        for code, account in balance_sheet.get("equity", {}).items():
            equity_data.append({
                "Codice": code,
                "Voce": account.get("name", ""),
                "Valore": account.get("value", 0),
                "Anno Precedente": account.get("previous_value", None)
            })
        
        # Combina passività e patrimonio netto
        passivo_data = equity_data + liabilities_data
        
        if passivo_data:
            passivo_df = pd.DataFrame(passivo_data)
            st.dataframe(passivo_df, use_container_width=True)
            
            # Visualizza il totale
            st.write(f"**Totale Passivo e Patrimonio Netto:** {balance_sheet.get('total_liabilities_equity', 0):,.2f} €")
        else:
            st.info("Nessun dato disponibile per il passivo e patrimonio netto.")

def display_income_statement(financial_data: Dict[str, Any]) -> None:
    """
    Visualizza il conto economico.
    
    Args:
        financial_data: Dati finanziari importati
    """
    st.subheader("Conto Economico")
    
    income_statement = financial_data.get("income_statement", {})
    
    # Crea un DataFrame per i ricavi
    revenues_data = []
    for code, account in income_statement.get("revenues", {}).items():
        revenues_data.append({
            "Codice": code,
            "Voce": account.get("name", ""),
            "Valore": account.get("value", 0),
            "Anno Precedente": account.get("previous_value", None)
        })
    
    # Crea un DataFrame per i costi
    expenses_data = []
    for code, account in income_statement.get("expenses", {}).items():
        expenses_data.append({
            "Codice": code,
            "Voce": account.get("name", ""),
            "Valore": account.get("value", 0),
            "Anno Precedente": account.get("previous_value", None)
        })
    
    # Visualizza i ricavi
    st.write("### RICAVI")
    if revenues_data:
        revenues_df = pd.DataFrame(revenues_data)
        st.dataframe(revenues_df, use_container_width=True)
    else:
        st.info("Nessun dato disponibile per i ricavi.")
    
    # Visualizza i costi
    st.write("### COSTI")
    if expenses_data:
        expenses_df = pd.DataFrame(expenses_data)
        st.dataframe(expenses_df, use_container_width=True)
    else:
        st.info("Nessun dato disponibile per i costi.")
    
    # Visualizza i risultati
    st.write("### RISULTATI")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Risultato Operativo", f"{income_statement.get('operating_result', 0):,.2f} €")
        st.metric("Risultato Ante Imposte", f"{income_statement.get('pre_tax_result', 0):,.2f} €")
    with col2:
        st.metric("Risultato Finanziario", f"{income_statement.get('financial_result', 0):,.2f} €")
        st.metric("Risultato Netto", f"{income_statement.get('net_result', 0):,.2f} €")

def display_financial_insights(analyzed_data: Dict[str, Any]) -> None:
    """
    Visualizza gli insights finanziari.
    
    Args:
        analyzed_data: Dati finanziari analizzati
    """
    st.subheader("Insights Finanziari")
    
    insights = analyzed_data.get("insights", {})
    
    # Visualizza il sommario
    if insights.get("summary"):
        st.write("### Sommario")
        for insight in insights["summary"]:
            st.write(f"- {insight}")
    
    # Crea tabs per le diverse categorie di insights
    tabs = st.tabs(["Redditività", "Liquidità", "Solvibilità", "Efficienza", "Crescita"])
    
    # Tab Redditività
    with tabs[0]:
        profitability = insights.get("profitability", {})
        
        # Crea metriche con valutazione colorata
        col1, col2, col3 = st.columns(3)
        
        with col1:
            net_profit_margin = profitability.get("net_profit_margin", 0)
            assessment = profitability.get("net_profit_margin_assessment", "neutral")
            delta_color = "normal" if assessment == "neutral" else ("off" if assessment == "negative" else "normal")
            st.metric("Margine di Profitto Netto", f"{net_profit_margin:.2%}", delta=assessment, delta_color=delta_color)
        
        with col2:
            roa = profitability.get("return_on_assets", 0)
            assessment = profitability.get("return_on_assets_assessment", "neutral")
            delta_color = "normal" if assessment == "neutral" else ("off" if assessment == "negative" else "normal")
            st.metric("Return on Assets (ROA)", f"{roa:.2%}", delta=assessment, delta_color=delta_color)
        
        with col3:
            roe = profitability.get("return_on_equity", 0)
            assessment = profitability.get("return_on_equity_assessment", "neutral")
            delta_color = "normal" if assessment == "neutral" else ("off" if assessment == "negative" else "normal")
            st.metric("Return on Equity (ROE)", f"{roe:.2%}", delta=assessment, delta_color=delta_color)
    
    # Tab Liquidità
    with tabs[1]:
        liquidity = insights.get("liquidity", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            current_ratio = liquidity.get("current_ratio", 0)
            assessment = liquidity.get("current_ratio_assessment", "neutral")
            delta_color = "normal" if assessment == "neutral" else ("off" if assessment == "negative" else "normal")
            st.metric("Indice di Liquidità Corrente", f"{current_ratio:.2f}", delta=assessment, delta_color=delta_color)
        
        with col2:
            quick_ratio = liquidity.get("quick_ratio", 0)
            assessment = liquidity.get("quick_ratio_assessment", "neutral")
            delta_color = "normal" if assessment == "neutral" else ("off" if assessment == "negative" else "normal")
            st.metric("Indice di Liquidità Immediata", f"{quick_ratio:.2f}", delta=assessment, delta_color=delta_color)
    
    # Tab Solvibilità
    with tabs[2]:
        solvency = insights.get("solvency", {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            debt_to_equity = solvency.get("debt_to_equity", 0)
            assessment = solvency.get("debt_to_equity_assessment", "neutral")
            delta_color = "normal" if assessment == "neutral" else ("off" if assessment == "negative" else "normal")
            st.metric("Rapporto Debito/Capitale", f"{debt_to_equity:.2f}", delta=assessment, delta_color=delta_color)
        
        with col2:
            debt_to_assets = solvency.get("debt_to_assets", 0)
            assessment = solvency.get("debt_to_assets_assessment", "neutral")
            delta_color = "normal" if assessment == "neutral" else ("off" if assessment == "negative" else "normal")
            st.metric("Rapporto Debito/Asset", f"{debt_to_assets:.2f}", delta=assessment, delta_color=delta_color)
        
        with col3:
            interest_coverage = solvency.get("interest_coverage", 0)
            assessment = solvency.get("interest_coverage_assessment", "neutral")
            delta_color = "normal" if assessment == "neutral" else ("off" if assessment == "negative" else "normal")
            st.metric("Copertura Interessi", f"{interest_coverage:.2f}", delta=assessment, delta_color=delta_color)
    
    # Tab Efficienza
    with tabs[3]:
        efficiency = insights.get("efficiency", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            asset_turnover = efficiency.get("asset_turnover", 0)
            assessment = efficiency.get("asset_turnover_assessment", "neutral")
            delta_color = "normal" if assessment == "neutral" else ("off" if assessment == "negative" else "normal")
            st.metric("Rotazione degli Asset", f"{asset_turnover:.2f}", delta=assessment, delta_color=delta_color)
        
        with col2:
            inventory_turnover = efficiency.get("inventory_turnover", 0)
            assessment = efficiency.get("inventory_turnover_assessment", "neutral")
            delta_color = "normal" if assessment == "neutral" else ("off" if assessment == "negative" else "normal")
            st.metric("Rotazione delle Scorte", f"{inventory_turnover:.2f}", delta=assessment, delta_color=delta_color)
    
    # Tab Crescita
    with tabs[4]:
        growth = insights.get("growth", {})
        
        if "revenue_growth" in growth:
            revenue_growth = growth.get("revenue_growth", 0)
            assessment = growth.get("revenue_growth_assessment", "neutral")
            delta_color = "normal" if assessment == "neutral" else ("off" if assessment == "negative" else "normal")
            st.metric("Crescita dei Ricavi", f"{revenue_growth:.2%}", delta=assessment, delta_color=delta_color)
        else:
            st.info("Dati insufficienti per calcolare la crescita dei ricavi.")

def display_financial_projections(analyzed_data: Dict[str, Any]) -> None:
    """
    Visualizza le proiezioni finanziarie.
    
    Args:
        analyzed_data: Dati finanziari analizzati
    """
    st.subheader("Proiezioni Finanziarie")
    
    projections = analyzed_data.get("projections", {})
    
    if not projections:
        st.info("Nessuna proiezione finanziaria disponibile.")
        return
    
    # Visualizza le assunzioni
    assumptions = projections.get("assumptions", {})
    if assumptions:
        st.write("### Assunzioni")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tasso di Crescita dei Ricavi", f"{assumptions.get('revenue_growth_rate', 0):.2%}")
        with col2:
            st.metric("Margine di Profitto", f"{assumptions.get('profit_margin', 0):.2%}")
    
    # Crea tabs per le diverse proiezioni
    tabs = st.tabs(["Ricavi e Profitti", "Stato Patrimoniale", "Flusso di Cassa"])
    
    # Tab Ricavi e Profitti
    with tabs[0]:
        # Prepara i dati per il grafico
        years = list(projections.get("revenue", {}).keys())
        revenues = list(projections.get("revenue", {}).values())
        net_profits = list(projections.get("net_profit", {}).values())
        
        if years and revenues and net_profits:
            # Crea un DataFrame
            df = pd.DataFrame({
                "Anno": years,
                "Ricavi": revenues,
                "Utile Netto": net_profits
            })
            
            # Crea il grafico
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df["Anno"], y=df["Ricavi"], name="Ricavi", marker_color="blue"))
            fig.add_trace(go.Scatter(x=df["Anno"], y=df["Utile Netto"], name="Utile Netto", marker_color="green", mode="lines+markers"))
            
            fig.update_layout(
                title="Proiezione Ricavi e Utile Netto",
                xaxis_title="Anno",
                yaxis_title="Valore (€)",
                legend_title="Legenda",
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Visualizza i dati in tabella
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Dati insufficienti per visualizzare le proiezioni di ricavi e profitti.")
    
    # Tab Stato Patrimoniale
    with tabs[1]:
        # Prepara i dati per il grafico
        years = list(projections.get("assets", {}).keys())
        assets = list(projections.get("assets", {}).values())
        liabilities = list(projections.get("liabilities", {}).values())
        equity = list(projections.get("equity", {}).values())
        
        if years and assets and liabilities and equity:
            # Crea un DataFrame
            df = pd.DataFrame({
                "Anno": years,
                "Asset": assets,
                "Passività": liabilities,
                "Patrimonio Netto": equity
            })
            
            # Crea il grafico
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df["Anno"], y=df["Asset"], name="Asset", marker_color="blue"))
            fig.add_trace(go.Bar(x=df["Anno"], y=df["Passività"], name="Passività", marker_color="red"))
            fig.add_trace(go.Bar(x=df["Anno"], y=df["Patrimonio Netto"], name="Patrimonio Netto", marker_color="green"))
            
            fig.update_layout(
                title="Proiezione Stato Patrimoniale",
                xaxis_title="Anno",
                yaxis_title="Valore (€)",
                legend_title="Legenda",
                template="plotly_white",
                barmode="group"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Visualizza i dati in tabella
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Dati insufficienti per visualizzare le proiezioni dello stato patrimoniale.")
    
    # Tab Flusso di Cassa
    with tabs[2]:
        # Prepara i dati per il grafico
        years = list(projections.get("cash_flow", {}).keys())
        cash_flows = list(projections.get("cash_flow", {}).values())
        
        if years and cash_flows:
            # Crea un DataFrame
            df = pd.DataFrame({
                "Anno": years,
                "Flusso di Cassa": cash_flows
            })
            
            # Crea il grafico
            fig = px.line(
                df, x="Anno", y="Flusso di Cassa",
                title="Proiezione Flusso di Cassa",
                markers=True,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Visualizza i dati in tabella
            st.dataframe(df, use_container_width=True)
            
            # Calcola il flusso di cassa cumulativo
            df["Flusso di Cassa Cumulativo"] = df["Flusso di Cassa"].cumsum()
            
            # Crea il grafico del flusso di cassa cumulativo
            fig = px.line(
                df, x="Anno", y="Flusso di Cassa Cumulativo",
                title="Proiezione Flusso di Cassa Cumulativo",
                markers=True,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dati insufficienti per visualizzare le proiezioni del flusso di cassa.")

def display_financial_recommendations(analyzed_data: Dict[str, Any]) -> None:
    """
    Visualizza le raccomandazioni finanziarie.
    
    Args:
        analyzed_data: Dati finanziari analizzati
    """
    st.subheader("Raccomandazioni Finanziarie")
    
    recommendations = analyzed_data.get("recommendations", [])
    
    if not recommendations:
        st.info("Nessuna raccomandazione finanziaria disponibile.")
        return
    
    # Raggruppa le raccomandazioni per area
    areas = {}
    for rec in recommendations:
        area = rec.get("area", "Generale")
        if area not in areas:
            areas[area] = []
        areas[area].append(rec)
    
    # Crea un expander per ogni area
    for area, recs in areas.items():
        with st.expander(f"{area} ({len(recs)})", expanded=True):
            for rec in recs:
                st.write(f"**{rec.get('issue', '')}**")
                st.write(rec.get("recommendation", ""))
                st.divider()

def generate_financial_plan(analyzed_data: Dict[str, Any]) -> str:
    """
    Genera il piano finanziario per il business plan.
    
    Args:
        analyzed_data: Dati finanziari analizzati
        
    Returns:
        str: Testo del piano finanziario
    """
    company_name = analyzed_data.get("company_name", "Azienda")
    
    return generate_financial_plan_section(analyzed_data, company_name)

def financial_dashboard(financial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Dashboard completa per la gestione dei dati finanziari.
    
    Args:
        financial_data: Dati finanziari precaricati (opzionale)
        
    Returns:
        Dict[str, Any]: Dati finanziari analizzati
    """
    st.title("Dashboard Finanziaria")
    
    # Se non ci sono dati precaricati, mostra l'uploader
    if financial_data is None:
        financial_data = financial_data_uploader()
    
    # Se ci sono dati, mostra le visualizzazioni
    if financial_data:
        # Crea tabs per le diverse sezioni
        tabs = st.tabs(["Stato Patrimoniale", "Conto Economico", "Analisi", "Proiezioni", "Raccomandazioni", "Piano Finanziario"])
        
        # Analizza i dati
        analyzed_data = financial_data_analyzer(financial_data)
        
        # Tab Stato Patrimoniale
        with tabs[0]:
            display_balance_sheet(financial_data)
        
        # Tab Conto Economico
        with tabs[1]:
            display_income_statement(financial_data)
        
        # Tab Analisi
        with tabs[2]:
            if analyzed_data:
                display_financial_insights(analyzed_data)
            else:
                st.info("Analizza i dati finanziari per visualizzare gli insights.")
        
        # Tab Proiezioni
        with tabs[3]:
            if analyzed_data:
                display_financial_projections(analyzed_data)
            else:
                st.info("Analizza i dati finanziari per visualizzare le proiezioni.")
        
        # Tab Raccomandazioni
        with tabs[4]:
            if analyzed_data:
                display_financial_recommendations(analyzed_data)
            else:
                st.info("Analizza i dati finanziari per visualizzare le raccomandazioni.")
        
        # Tab Piano Finanziario
        with tabs[5]:
            if analyzed_data:
                financial_plan = generate_financial_plan(analyzed_data)
                st.markdown(financial_plan)
                
                # Pulsante per scaricare il piano finanziario
                st.download_button(
                    label="Scarica Piano Finanziario",
                    data=financial_plan,
                    file_name="piano_finanziario.md",
                    mime="text/markdown"
                )
            else:
                st.info("Analizza i dati finanziari per generare il piano finanziario.")
        
        return analyzed_data
    
    return None

if __name__ == "__main__":
    # Test della dashboard
    financial_dashboard()
