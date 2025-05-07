"""
Modulo per la generazione rapida di un business plan completo.
Questo modulo contiene funzioni per generare rapidamente un business plan completo
utilizzando i dati di esempio e il grafo LangGraph.
"""

import streamlit as st
from typing import Dict, Any, List
from graph_builder import node_functions

def generate_full_business_plan(state_dict: Dict[str, Any]) -> Dict[str, str]:
    """
    Genera un business plan completo utilizzando i dati forniti.
    
    Args:
        state_dict: Dizionario con lo stato iniziale
        
    Returns:
        Dict[str, str]: Dizionario con le sezioni generate
    """
    # Dizionario per memorizzare i risultati
    results = {}
    
    # Ordine delle sezioni da generare
    sections_order = [
        "executive_summary",
        "company_description",
        "products_and_services",
        "market_analysis",
        "competitor_analysis",
        "marketing_strategy",
        "operational_plan",
        "organization_and_management",
        "risk_analysis",
        "financial_plan"
    ]
    
    # Mappa dei nomi dei nodi ai nomi delle sezioni in italiano
    section_names = {
        "executive_summary": "Sommario Esecutivo",
        "company_description": "Descrizione dell'Azienda",
        "products_and_services": "Prodotti e Servizi",
        "market_analysis": "Analisi di Mercato",
        "competitor_analysis": "Analisi Competitiva",
        "marketing_strategy": "Strategia di Marketing",
        "operational_plan": "Piano Operativo",
        "organization_and_management": "Organizzazione e Team di Gestione",
        "risk_analysis": "Analisi dei Rischi",
        "financial_plan": "Piano Finanziario"
    }
    
    # Genera ogni sezione in sequenza
    for section_key in sections_order:
        if section_key in node_functions:
            # Ottieni la funzione del nodo
            node_func = node_functions[section_key]
            
            # Esegui la funzione del nodo
            try:
                result = node_func(state_dict)
                
                # Estrai il contenuto dal risultato
                if isinstance(result, dict) and "messages" in result:
                    message = result["messages"][0]
                    if isinstance(message, dict) and "content" in message:
                        content = message["content"]
                    else:
                        content = str(message)
                else:
                    content = str(result)
                
                # Salva il risultato
                section_name = section_names.get(section_key, section_key)
                results[section_name] = content
                
                # Aggiorna lo stato con il risultato per la prossima sezione
                state_dict[section_key + "_result"] = content
                
            except Exception as e:
                print(f"Errore nella generazione della sezione {section_key}: {e}")
                results[section_names.get(section_key, section_key)] = f"Errore nella generazione: {e}"
    
    return results

def update_session_state_with_results(results: Dict[str, str]) -> None:
    """
    Aggiorna lo stato della sessione con i risultati generati.
    
    Args:
        results: Dizionario con le sezioni generate
    """
    # Aggiorna la cronologia con i risultati
    for section_name, content in results.items():
        # Trova il nodo corrispondente al nome della sezione
        node_name = None
        for key, value in {
            "executive_summary": "Sommario Esecutivo",
            "company_description": "Descrizione dell'Azienda",
            "products_and_services": "Prodotti e Servizi",
            "market_analysis": "Analisi di Mercato",
            "competitor_analysis": "Analisi Competitiva",
            "marketing_strategy": "Strategia di Marketing",
            "operational_plan": "Piano Operativo",
            "organization_and_management": "Organizzazione e Team di Gestione",
            "risk_analysis": "Analisi dei Rischi",
            "financial_plan": "Piano Finanziario"
        }.items():
            if value == section_name:
                node_name = key
                break
        
        if node_name:
            # Crea una voce nella cronologia
            history_entry = (
                node_name,
                st.session_state.state_dict.copy(),
                {"messages": [{"role": "assistant", "content": content}]}
            )
            
            # Aggiungi alla cronologia
            st.session_state.history.append(history_entry)
