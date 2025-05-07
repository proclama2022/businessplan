#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script di test per la funzione sommario_esecutivo.
"""

import os
import sys
from datetime import datetime

# Assicurati che la directory principale sia nel path per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa i componenti necessari
try:
    from state import initialize_state
    from direct_generator import sommario_esecutivo
except ImportError as e:
    print(f"Errore nell'importare i moduli: {e}")
    sys.exit(1)

def main():
    """Funzione principale per testare la funzione sommario_esecutivo"""
    print("=== Test della funzione sommario_esecutivo ===")
    
    # Inizializza lo stato di test
    state = initialize_state(
        document_title="Business Plan di Test",
        company_name="Azienda di Test",
        creation_date=datetime.now().strftime("%Y-%m-%d"),
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
        "section_documents_text": ""
    })
    
    # Esegui la funzione
    try:
        print("Esecuzione della funzione sommario_esecutivo...")
        result = sommario_esecutivo(state)
        print(f"Risultato: {result[:100]}...")  # Mostra solo i primi 100 caratteri
        print("Test completato con successo!")
    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
