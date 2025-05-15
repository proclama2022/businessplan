#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script di test per la funzionalità di adattamento automatico della lunghezza
"""

import os
import sys
from typing import Dict, Any
from datetime import datetime

# Assicurati che la directory principale sia nel path per importare i moduli
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importa i moduli necessari
try:
    from state import initialize_state
    from tools.gemini_generator import generate_section, adjust_text_length
except ImportError as e:
    print(f"Errore nell'importare i moduli: {e}")
    sys.exit(1)

def test_length_adjustment():
    """Testa la funzione di adattamento automatico della lunghezza"""
    print("=== Test di Adattamento Automatico della Lunghezza ===")
    
    # Inizializza lo stato di test
    state = initialize_state(
        document_title="Test di Lunghezza",
        company_name="Azienda Test",
        creation_date=datetime.now().strftime("%Y-%m-%d"),
        version=1
    )
    
    # Aggiungi campi di base allo stato
    state.update({
        "business_sector": "Tecnologia",
        "company_description": "Un'azienda innovativa nel settore tecnologico",
        "year_founded": "2022",
        "num_employees": "10",
        "main_products": "Software di intelligenza artificiale",
        "target_market": "PMI",
        "area": "Internazionale",
        "plan_objectives": "Espansione internazionale",
        "time_horizon": "3 anni"
    })
    
    # Test con diverse lunghezze
    test_lengths = [
        ("breve", 300, True),   # Breve con adattamento automatico
        ("media", 800, True),   # Media con adattamento automatico
        ("dettagliata", 2000, True),  # Lunga con adattamento automatico
        ("media", 800, False)   # Media senza adattamento automatico
    ]
    
    section_name = "Sommario Esecutivo"
    
    for length_type, word_count, length_auto in test_lengths:
        print(f"\n--- Test con lunghezza: {length_type}, {word_count} parole, auto: {length_auto} ---")
        
        # Imposta i parametri di lunghezza
        test_state = state.copy()
        test_state["length_type"] = length_type
        test_state["length_auto"] = length_auto
        
        try:
            # Genera la sezione
            result = generate_section(section_name, test_state, word_count=word_count)
            
            # Estrai il testo generato
            if isinstance(result, dict) and 'messages' in result and result['messages']:
                generated_text = result['messages'][-1]['content']
            else:
                generated_text = str(result)
            
            # Conta le parole
            word_count_actual = len(generated_text.split())
            
            # Mostra i risultati
            print(f"Parole richieste: {word_count}")
            print(f"Parole generate: {word_count_actual}")
            print(f"Differenza: {abs(word_count - word_count_actual)} parole ({abs(word_count - word_count_actual) / word_count * 100:.1f}%)")
            
            # Verifica se la lunghezza è corretta
            if length_auto:
                # Con adattamento automatico, dovrebbe essere entro il 10%
                if abs(word_count - word_count_actual) / word_count <= 0.1:
                    print("✅ Test superato: La lunghezza è stata adattata correttamente")
                else:
                    print("❌ Test fallito: La lunghezza non è stata adattata correttamente")
            else:
                # Senza adattamento automatico, non controlliamo la precisione
                print("ℹ️ Test solo informativo (senza adattamento automatico)")
            
            # Mostra un estratto del testo generato
            print(f"\nEstratto del testo generato ({min(100, word_count_actual)} parole):")
            print(f"{' '.join(generated_text.split()[:100])}...")
            
        except Exception as e:
            print(f"Errore durante il test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_length_adjustment() 