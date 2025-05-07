#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integrazione del modulo finanziario con il business plan builder.

Questo modulo fornisce funzioni per integrare il modulo finanziario
con il business plan builder, permettendo di utilizzare i dati finanziari
importati per generare il piano finanziario.
"""

import os
import sys
import streamlit as st
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

def add_financial_tab():
    """
    Aggiunge una tab per la gestione dei dati finanziari nell'app Streamlit.
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

def convert_financial_data_for_business_plan(analyzed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte i dati finanziari analizzati in un formato utilizzabile dal business plan.
    
    Args:
        analyzed_data: Dati finanziari analizzati
        
    Returns:
        Dict[str, Any]: Dati finanziari per il business plan
    """
    # Estrai i dati necessari
    projections = analyzed_data.get("projections", {})
    insights = analyzed_data.get("insights", {})
    recommendations = analyzed_data.get("recommendations", [])
    
    # Crea la struttura per il business plan
    financial_data_for_bp = {
        "projections": {},
        "startup_costs": {},
        "revenue_streams": [],
        "cashflow": {},
        "break_even": {},
        "funding_requirements": {}
    }
    
    # Popola le proiezioni
    if "revenue" in projections:
        financial_data_for_bp["projections"]["revenue"] = projections["revenue"]
    
    if "net_profit" in projections:
        financial_data_for_bp["projections"]["profit"] = projections["net_profit"]
    
    if "expenses" in projections:
        financial_data_for_bp["projections"]["expenses"] = projections["expenses"]
    
    # Popola i costi di avviamento
    raw_data = analyzed_data.get("raw_data", {})
    balance_sheet = raw_data.get("balance_sheet", {})
    
    # Estrai i costi di avviamento dalle immobilizzazioni
    for code, account in balance_sheet.get("assets", {}).items():
        if code.startswith("B."):  # Immobilizzazioni
            financial_data_for_bp["startup_costs"][account.get("name", code)] = account.get("value", 0)
    
    # Popola i flussi di ricavi
    income_statement = raw_data.get("income_statement", {})
    for code, account in income_statement.get("revenues", {}).items():
        if code == "A.1":  # Ricavi delle vendite e delle prestazioni
            financial_data_for_bp["revenue_streams"].append({
                "name": account.get("name", "Ricavi principali"),
                "value": account.get("value", 0),
                "percentage": 100.0
            })
    
    # Popola il flusso di cassa
    if "cash_flow" in projections:
        financial_data_for_bp["cashflow"] = projections["cash_flow"]
    
    # Popola il break-even
    if "assumptions" in projections:
        financial_data_for_bp["break_even"] = {
            "fixed_costs": sum(financial_data_for_bp["startup_costs"].values()) * 0.1,  # Stima
            "variable_costs_percentage": 0.6,  # Stima
            "revenue_at_break_even": 0,  # Sarà calcolato dal business plan
            "time_to_break_even": 0  # Sarà calcolato dal business plan
        }
    
    # Popola i requisiti di finanziamento
    financial_data_for_bp["funding_requirements"] = {
        "total_required": sum(financial_data_for_bp["startup_costs"].values()),
        "sources": [
            {"name": "Capitale proprio", "amount": balance_sheet.get("equity", {}).get("A.I.P", {}).get("value", 0)},
            {"name": "Finanziamento bancario", "amount": 0},  # Da calcolare
            {"name": "Investitori", "amount": 0}  # Da calcolare
        ]
    }
    
    return financial_data_for_bp

def generate_financial_plan_from_data(state: Dict[str, Any]) -> str:
    """
    Genera il piano finanziario utilizzando i dati finanziari importati.
    
    Args:
        state: Stato del business plan
        
    Returns:
        str: Testo del piano finanziario
    """
    # Verifica se ci sono dati finanziari analizzati nella sessione
    if "financial_analysis" in st.session_state and st.session_state.financial_analysis:
        # Usa i dati analizzati per generare il piano finanziario
        company_name = state.get("company_name", "Azienda")
        return generate_financial_plan_section(st.session_state.financial_analysis, company_name)
    
    # Altrimenti, genera un piano finanziario generico
    return generate_generic_financial_plan(state)

def generate_generic_financial_plan(state: Dict[str, Any]) -> str:
    """
    Genera un piano finanziario generico senza dati finanziari importati.
    
    Args:
        state: Stato del business plan
        
    Returns:
        str: Testo del piano finanziario
    """
    company_name = state.get("company_name", "Azienda")
    business_sector = state.get("business_sector", "")
    
    return f"""# Piano Finanziario - {company_name}

## Panoramica Finanziaria

Il piano finanziario di {company_name} è stato sviluppato per fornire una visione chiara delle prospettive economiche dell'azienda nel settore {business_sector}. Questo piano include proiezioni finanziarie, analisi dei costi, strategie di finanziamento e indicatori chiave di performance.

## Proiezioni Finanziarie

Le proiezioni finanziarie sono state elaborate considerando le condizioni attuali del mercato e le potenzialità di crescita dell'azienda. Si prevede un incremento progressivo dei ricavi nei prossimi anni, accompagnato da un controllo attento dei costi per garantire una redditività sostenibile.

### Ricavi Previsti

| Anno | Ricavi Previsti |
|------|----------------|
| 2024 | € 500.000 |
| 2025 | € 750.000 |
| 2026 | € 1.125.000 |

### Utile Netto Previsto

| Anno | Utile Netto Previsto |
|------|---------------------|
| 2024 | € 50.000 |
| 2025 | € 112.500 |
| 2026 | € 225.000 |

## Struttura dei Costi

La struttura dei costi è stata progettata per ottimizzare l'efficienza operativa mantenendo alta la qualità dei prodotti/servizi offerti.

### Costi Fissi

- Affitto locali: € 36.000/anno
- Stipendi personale amministrativo: € 120.000/anno
- Assicurazioni: € 15.000/anno
- Utenze: € 24.000/anno

### Costi Variabili

- Materie prime/merci: 30% del fatturato
- Commissioni vendita: 5% del fatturato
- Marketing e pubblicità: 10% del fatturato

## Strategia di Finanziamento

Per sostenere la crescita prevista, {company_name} prevede di utilizzare una combinazione di:

- Capitale proprio: 40%
- Finanziamenti bancari: 30%
- Investitori esterni: 30%

## Indicatori Chiave di Performance

Gli indicatori finanziari che verranno monitorati includono:

- ROI (Return on Investment): obiettivo >15%
- Margine di profitto netto: obiettivo >10%
- Punto di pareggio: previsto entro il 18° mese di attività

## Conclusioni

Il piano finanziario di {company_name} è stato sviluppato con un approccio realistico ma ambizioso. Le proiezioni indicano che entro il terzo anno, l'azienda potrebbe raggiungere ricavi superiori a € 1 milione con un utile netto di circa € 225.000. L'implementazione di un rigoroso controllo finanziario e il monitoraggio costante degli indicatori chiave contribuiranno a garantire la sostenibilità economica a lungo termine dell'azienda.
"""
