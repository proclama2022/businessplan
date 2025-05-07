#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script di test per il modulo direct_generator.
"""

import os
import sys
from datetime import datetime

# Assicurati che la directory principale sia nel path per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa i componenti necessari
try:
    from state import initialize_state
    import direct_generator
except ImportError as e:
    print(f"Errore nell'importare i moduli: {e}")
    sys.exit(1)

def main():
    """Funzione principale per testare il modulo direct_generator"""
    print("=== Test del modulo direct_generator ===")
    
    # Verifica che il modulo sia stato importato correttamente
    print(f"Modulo importato: {direct_generator.__name__}")
    
    # Verifica che le funzioni siano disponibili
    print("\nFunzioni disponibili:")
    for func_name in direct_generator.__all__:
        print(f"- {func_name}")
    
    # Verifica che la funzione sommario_esecutivo sia disponibile
    if hasattr(direct_generator, 'sommario_esecutivo'):
        print("\nLa funzione 'sommario_esecutivo' è disponibile.")
    else:
        print("\nERRORE: La funzione 'sommario_esecutivo' non è disponibile.")
    
    print("\nTest completato.")

if __name__ == "__main__":
    main()
