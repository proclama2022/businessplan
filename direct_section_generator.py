#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generatore diretto di sezioni del business plan.
Questo script permette di generare direttamente le sezioni del business plan
senza passare attraverso l'interfaccia Streamlit.
"""

import os
import sys
import json
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

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

def generate_section(section_name: str, company_data: Dict[str, Any]) -> str:
    """
    Genera una sezione del business plan.

    Args:
        section_name: Nome della sezione da generare
        company_data: Dati dell'azienda

    Returns:
        str: Testo generato
    """
    # Normalizza il nome della sezione (diverse varianti per gestire apostrofi e spazi)
    normalized_name = section_name.lower()

    # Mappa dei nomi delle sezioni in italiano ai nomi delle funzioni in inglese
    section_map = {
        # Sommario Esecutivo
        "sommario_esecutivo": "executive_summary",
        "sommario esecutivo": "executive_summary",

        # Descrizione dell'Azienda (con diverse varianti per gestire l'apostrofo)
        "descrizione_dellazienda": "company_description",
        "descrizione dell'azienda": "company_description",
        "descrizione_dell_azienda": "company_description",
        "descrizione_dellazienda": "company_description",
        "descrizione_della_azienda": "company_description",
        "descrizione dell azienda": "company_description",
        "descrizione della azienda": "company_description",

        # Prodotti e Servizi
        "prodotti_e_servizi": "products_and_services",
        "prodotti e servizi": "products_and_services",

        # Analisi di Mercato
        "analisi_di_mercato": "market_analysis",
        "analisi di mercato": "market_analysis",

        # Analisi Competitiva
        "analisi_competitiva": "competitor_analysis",
        "analisi competitiva": "competitor_analysis",

        # Strategia di Marketing
        "strategia_di_marketing": "marketing_strategy",
        "strategia di marketing": "marketing_strategy",

        # Piano Operativo
        "piano_operativo": "operational_plan",
        "piano operativo": "operational_plan",

        # Organizzazione e Team di Gestione
        "organizzazione_e_team_di_gestione": "organization_and_management",
        "organizzazione e team di gestione": "organization_and_management",

        # Analisi dei Rischi
        "analisi_dei_rischi": "risk_analysis",
        "analisi dei rischi": "risk_analysis",

        # Piano Finanziario
        "piano_finanziario": "financial_plan",
        "piano finanziario": "financial_plan"
    }

    # Prova diverse normalizzazioni per trovare una corrispondenza
    node_name = None
    variants = [
        normalized_name,
        normalized_name.replace(" ", "_"),
        normalized_name.replace("'", "").replace(" ", "_"),
        normalized_name.replace("'", "_").replace(" ", "_"),
        normalized_name.replace("'", "").replace("-", "_").replace(" ", "_"),
        normalized_name.replace("'", " ").replace("-", " "),
        normalized_name.replace("'", "").replace("-", " ")
    ]

    # Cerca una corrispondenza nella mappa
    for variant in variants:
        if variant in section_map:
            node_name = section_map[variant]
            break

    # Se non è stata trovata una corrispondenza, usa la normalizzazione standard
    if node_name is None:
        # Normalizzazione standard come fallback
        node_name = normalized_name.replace(" ", "_").replace("'", "").replace("-", "_")

    # Verifica se la funzione del nodo esiste
    if node_name not in node_functions:
        return f"Errore: Funzione per '{section_name}' ('{node_name}') non trovata."

    try:
        # Ottieni la funzione del nodo
        node_func = node_functions[node_name]

        # Ottieni la lunghezza desiderata
        length_type = company_data.get('length_type', 'media')  # Default a 'media' se non specificato
        print(f"Utilizzando lunghezza: {length_type}")

        # Esegui la funzione
        print(f"Generazione della sezione '{section_name}' con OpenAI in corso...")
        
        # Assicurati che la funzione del nodo esista e chiamala direttamente.
        # Le node_functions sono state aggiornate per usare OpenAI.
        result = node_func(company_data)
        # La gestione della lunghezza e altri parametri specifici dovrebbe essere gestita
        # all'interno della node_func stessa o passata come parte di company_data se necessario.

        # Estrai il contenuto dal risultato
        if isinstance(result, dict) and 'messages' in result and result['messages']:
            last_message = result['messages'][-1]
            if isinstance(last_message, dict) and 'content' in last_message:
                content = last_message['content']
            else:
                content = str(last_message)
        else:
            content = str(result)

        return content
    except Exception as e:
        traceback.print_exc()
        return f"Errore durante la generazione: {str(e)}"

def extract_pure_content(text: str) -> str:
    """
    Estrae il contenuto pulito dal testo generato.

    Args:
        text: Testo da pulire

    Returns:
        str: Testo pulito
    """
    import re

    # Se è già un testo pulito, restituiscilo direttamente
    if not any(marker in text for marker in ["content=", "token_usage", "additional_kwargs", "Si è verificato un errore"]):
        clean_text = text
    else:
        # Gestisci i messaggi di errore
        if "Si è verificato un errore durante la generazione del contenuto" in text:
            # Estrai solo il messaggio di errore senza dettagli tecnici
            error_match = re.search(r"Si è verificato un errore durante la generazione del contenuto\. Dettagli: (.*?)(?:\n|$)", text)
            if error_match:
                return f"Errore: {error_match.group(1)}"
            else:
                return "Errore durante la generazione del contenuto. Riprova."

        # Prova a estrarre il contenuto dal pattern content='...'
        if "content='" in text:
            content_match = re.search(r"content='(.*?)(?:'(?:\s+additional_kwargs|\s+response_metadata))", text, re.DOTALL)
            if content_match:
                clean_text = content_match.group(1)
            else:
                clean_text = text
        # Se non ha funzionato, prova un altro approccio per formati diversi
        elif "content=\"" in text:
            content_match = re.search(r'content="(.*?)"', text, re.DOTALL)
            if content_match:
                clean_text = content_match.group(1)
            else:
                clean_text = text
        # Fallback: rimuovi tutto dopo i marker di metadati noti
        else:
            for marker in ["additional_kwargs=", "response_metadata=", "usage_metadata="]:
                if marker in text:
                    parts = text.split(marker)
                    if parts and parts[0]:
                        # Pulisci la fine della parte di contenuto
                        clean_end = re.sub(r"'\s*$", "", parts[0])
                        # Se ha ancora content= all'inizio, rimuovilo
                        if "content='" in clean_end:
                            clean_end = clean_end.split("content='", 1)[1]
                        clean_text = clean_end
                        break
            else:
                clean_text = text

    # Post-processing: gestisci newline escapate e rimuovi formattazione markdown
    # Sostituisci \n letterali con newline effettive
    clean_text = clean_text.replace('\\n', '\n')

    # Rimuovi formattazione markdown
    # Rimuovi caratteri # dalle righe di intestazione
    clean_text = re.sub(r'^#+\s+', '', clean_text, flags=re.MULTILINE)

    # Rimuovi ** e * per grassetto e corsivo
    clean_text = re.sub(r'\*\*|\*', '', clean_text)

    # Rimuovi altra formattazione markdown comune
    clean_text = re.sub(r'__', '', clean_text)  # Grassetto con underscore
    clean_text = re.sub(r'_', '', clean_text)   # Corsivo con underscore
    clean_text = re.sub(r'`', '', clean_text)   # Blocchi di codice

    # Rimuovi eventuali istruzioni o meta-commenti che potrebbero essere stati generati
    clean_text = re.sub(r'^(Ecco il testo per la sezione|Ecco la sezione|Ecco il contenuto|Ecco un|Di seguito).*?:\s*', '', clean_text, flags=re.IGNORECASE)

    # Rimuovi eventuali note o commenti alla fine
    clean_text = re.sub(r'\n\s*Nota:.*?$', '', clean_text, flags=re.IGNORECASE | re.MULTILINE)
    clean_text = re.sub(r'\n\s*N\.B\..*?$', '', clean_text, flags=re.IGNORECASE | re.MULTILINE)

    return clean_text

def main():
    """Funzione principale per generare le sezioni del business plan"""
    print("=== Generatore di Sezioni del Business Plan ===")

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
        "section_documents_text": "",
        "temperature": Config.TEMPERATURE,
        "max_tokens": Config.MAX_TOKENS
    })

    # Lista delle sezioni disponibili
    available_sections = [
        "Sommario Esecutivo",
        "Descrizione dell'Azienda",
        "Prodotti e Servizi",
        "Analisi di Mercato",
        "Analisi Competitiva",
        "Strategia di Marketing",
        "Piano Operativo",
        "Organizzazione e Team di Gestione",
        "Analisi dei Rischi",
        "Piano Finanziario"
    ]

    # Mostra le sezioni disponibili
    print("\nSezioni disponibili:")
    for i, section in enumerate(available_sections, 1):
        print(f"{i}. {section}")

    # Chiedi all'utente quale sezione generare
    try:
        choice = int(input("\nScegli una sezione (1-10): "))
        if choice < 1 or choice > len(available_sections):
            print("Scelta non valida.")
            return

        selected_section = available_sections[choice - 1]

        # Genera la sezione
        content = generate_section(selected_section, state)

        # Pulisci il contenuto
        clean_content = extract_pure_content(content)

        # Mostra il risultato
        print("\n=== Contenuto Generato ===")
        print(clean_content)

        # Salva il risultato su file
        filename = f"{selected_section.lower().replace(' ', '_').replace("'", '')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(clean_content)

        print(f"\nContenuto salvato nel file: {filename}")

    except ValueError:
        print("Inserisci un numero valido.")
    except Exception as e:
        print(f"Errore: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
