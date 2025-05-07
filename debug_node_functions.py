#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script di debug per testare le funzioni dei nodi del business plan.
Questo script verifica che tutte le funzioni dei nodi siano disponibili e funzionanti.
"""

import os
import sys
import traceback
from typing import Dict, Any

# Assicurati che la directory principale sia nel path per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa i componenti necessari
try:
    from config import Config
    from state import initialize_state
    from graph_builder import node_functions
except ImportError as e:
    print(f"Errore nell'importare i moduli: {e}")
    sys.exit(1)

def test_node_function(node_name: str, state: Dict[str, Any]) -> bool:
    """
    Testa una funzione di nodo specifica.
    
    Args:
        node_name: Nome del nodo da testare
        state: Stato da passare alla funzione
        
    Returns:
        bool: True se il test è riuscito, False altrimenti
    """
    print(f"\n=== Test della funzione '{node_name}' ===")
    
    if node_name not in node_functions:
        print(f"ERRORE: Funzione '{node_name}' non trovata in node_functions")
        return False
    
    try:
        # Ottieni la funzione del nodo
        node_func = node_functions[node_name]
        
        # Esegui la funzione
        print(f"Esecuzione di {node_name}...")
        result = node_func(state)
        
        # Verifica il risultato
        if result is None:
            print(f"ERRORE: La funzione '{node_name}' ha restituito None")
            return False
            
        # Verifica che il risultato sia un dizionario con 'messages'
        if not isinstance(result, dict) or 'messages' not in result:
            print(f"ERRORE: La funzione '{node_name}' non ha restituito un dizionario con 'messages'")
            print(f"Tipo restituito: {type(result)}")
            print(f"Contenuto: {result}")
            return False
            
        # Verifica che 'messages' contenga almeno un messaggio
        if not result['messages']:
            print(f"ERRORE: La funzione '{node_name}' ha restituito 'messages' vuoto")
            return False
            
        # Estrai il contenuto del messaggio
        message = result['messages'][-1]
        if isinstance(message, dict) and 'content' in message:
            content = message['content']
        else:
            content = str(message)
            
        # Mostra un'anteprima del contenuto
        print(f"Contenuto generato (primi 200 caratteri): {content[:200]}...")
        
        print(f"Test di '{node_name}' completato con successo")
        return True
        
    except Exception as e:
        print(f"ERRORE durante l'esecuzione di '{node_name}': {e}")
        traceback.print_exc()
        return False

def main():
    """Funzione principale per testare tutte le funzioni dei nodi"""
    print("=== Test delle funzioni dei nodi del business plan ===")
    
    # Inizializza lo stato di test
    state = initialize_state(
        document_title="Business Plan di Test",
        company_name="Azienda di Test",
        creation_date="2023-01-01",
        version=1
    )
    
    # Aggiungi campi aggiuntivi allo stato
    state.update({
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
    
    # Lista dei nodi da testare
    nodes_to_test = [
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
    
    # Testa ogni nodo
    results = {}
    for node_name in nodes_to_test:
        results[node_name] = test_node_function(node_name, state)
    
    # Mostra il riepilogo
    print("\n=== Riepilogo dei test ===")
    success_count = sum(1 for success in results.values() if success)
    print(f"Test completati: {len(results)}")
    print(f"Test riusciti: {success_count}")
    print(f"Test falliti: {len(results) - success_count}")
    
    # Mostra i dettagli dei test falliti
    if len(results) - success_count > 0:
        print("\nDettagli dei test falliti:")
        for node_name, success in results.items():
            if not success:
                print(f"- {node_name}")
    
    # Verifica se tutti i nodi sono disponibili
    all_nodes = set(node_functions.keys())
    missing_nodes = set(nodes_to_test) - all_nodes
    if missing_nodes:
        print("\nNodi mancanti in node_functions:")
        for node in missing_nodes:
            print(f"- {node}")
    
    # Nodi aggiuntivi non testati
    extra_nodes = all_nodes - set(nodes_to_test)
    if extra_nodes:
        print("\nNodi aggiuntivi non testati:")
        for node in extra_nodes:
            print(f"- {node}")

if __name__ == "__main__":
    main()
