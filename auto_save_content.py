#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo per il salvataggio automatico del contenuto generato in app_streamlit.py.

Questo modulo fornisce funzioni per assicurare che il testo generato in una
sezione venga sempre salvato nella cronologia e sia disponibile quando si naviga
avanti e indietro tra le sezioni.
"""

import streamlit as st
from typing import List, Dict, Any, Tuple, Optional

def save_current_section_output(
    section_key: str,
    output: str,
    history: List[Tuple[str, Dict, str]]
) -> None:
    """
    Salva l'output corrente di una sezione nella cronologia.
    Utile per salvare manualmente il testo generato in qualsiasi momento.
    
    Args:
        section_key: Chiave della sezione da salvare
        output: Testo di output da salvare
        history: Lista della cronologia
    """
    if not output:
        return  # Non salvare output vuoti
    
    # Cerca se esiste già un entry per questo nodo
    existing_entry = False
    for i, (node, ctx, _) in enumerate(history):
        if node == section_key:
            # Prendi il contesto esistente
            existing_ctx = ctx
            # Aggiorna l'entry esistente
            history[i] = (node, existing_ctx, output)
            existing_entry = True
            break

    # Se non esiste, aggiungi una nuova entry
    if not existing_entry:
        try:
            from app_streamlit import prepare_generation_context
            context = prepare_generation_context()
        except:
            if 'state_dict' in st.session_state:
                context = st.session_state.state_dict.copy()
            else:
                context = {}
        history.append((section_key, context, output))
    
    return

def apply_autosave_patch():
    """
    Applica la patch di autosalvataggio all'app Streamlit.
    Questa funzione deve essere chiamata all'avvio dell'applicazione.
    """
    # Salva lo stato corrente se disponibile
    if 'current_output' in st.session_state and st.session_state.current_output and 'current_node' in st.session_state:
        save_current_section_output(
            st.session_state.current_node,
            st.session_state.current_output,
            st.session_state.history
        )
    return

def monkey_patch_app():
    """
    Applica il monkey patch alle funzioni di generazione e navigazione.
    Questo è un modo più invasivo per assicurare che il salvataggio funzioni.
    """
    # Qui è dove potremmo sostituire funzioni originali con versioni patched
    # Attualmente non implementato perché richiede accesso al codice sorgente
    # dell'app in fase di esecuzione
    pass

if __name__ == "__main__":
    # Per test
    print("Questo modulo dovrebbe essere importato, non eseguito direttamente.") 