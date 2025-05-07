#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Business Plan Builder - Sistema avanzato per la gestione di business plan lunghi

Questo script principale coordina tutti i componenti del sistema:
- Chunking gerarchico per suddividere documenti lunghi
- Sistema di memoria persistente con LangGraph e database vettoriale
- Ricerca avanzata con RAG e integrazione Perplexity
- Sistema modulare per revisioni e interventi umani
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Importa i componenti del sistema
from config import Config
from state import BusinessPlanState, initialize_state
from graph_builder import build_business_plan_graph
from database.vector_store import VectorDatabase
from chunking.hierarchical import chunk_document, detect_section_structure
from tools.docx_generator import generate_docx

def parse_arguments():
    """Analizza gli argomenti della riga di comando"""
    parser = argparse.ArgumentParser(description="Business Plan Builder - Sistema avanzato per la gestione di business plan lunghi")
    parser.add_argument("--input", "-i", help="File di input (markdown, docx, pdf)")
    parser.add_argument("--output", "-o", help="File di output (docx)")
    parser.add_argument("--company", "-c", help="Nome dell'azienda")
    parser.add_argument("--interactive", action="store_true", help="Modalità interattiva")
    parser.add_argument("--edit-section", "-e", help="Modifica una sezione specifica")
    parser.add_argument("--search", "-s", help="Esegui ricerche di mercato")
    
    return parser.parse_args()

def main():
    """Funzione principale del programma"""
    args = parse_arguments()
    
    print("\n===== Business Plan Builder =====\n")
    print("Sistema avanzato per la gestione di business plan lunghi")
    print("Versione 1.0.0\n")
    
    # Verifica le chiavi API necessarie
    if not os.getenv("OPENAI_API_KEY"):
        print("Errore: Chiave API OpenAI non trovata. Aggiungi OPENAI_API_KEY al file .env")
        sys.exit(1)
    
    # Inizializza il database vettoriale
    vector_db = VectorDatabase()
    
    # Inizializza lo stato del business plan
    state = initialize_state(
        document_title=f"Business Plan - {args.company if args.company else 'Nuova Azienda'}",
        company_name=args.company if args.company else "Nuova Azienda",
        creation_date=datetime.now().strftime("%Y-%m-%d"),
        version=1
    )
    
    # Costruisci il grafo LangGraph
    graph = build_business_plan_graph(vector_db).compile()
    
    if args.input:
        # Carica e suddividi il documento esistente
        print(f"Caricamento del documento: {args.input}")
        # Implementazione del caricamento del documento
        # ...
    
    if args.interactive:
        # Avvia la modalità interattiva
        print("Avvio della modalità interattiva...")

        from tabulate import tabulate
        import json
        from pypdf import PdfReader
        from docx import Document
        import importlib

        DOCUMENTI_PATH = "documenti_estratti.json"

        def estrai_testo_da_pdf(percorso):
            reader = PdfReader(percorso)
            testo = ""
            for pagina in reader.pages:
                testo += pagina.extract_text() or ""
            return testo

        def estrai_testo_da_docx(percorso):
            doc = Document(percorso)
            testo = "\n".join([par.text for par in doc.paragraphs])
            return testo

        def carica_documento():
            percorso = input("Percorso del file da caricare (PDF/DOCX): ")
            if not os.path.isfile(percorso):
                print("File non trovato.")
                return None
            tipo = input("Tipo documento (visura, bilancio, altro): ")
            estensione = os.path.splitext(percorso)[1].lower()
            if estensione == ".pdf":
                testo = estrai_testo_da_pdf(percorso)
            elif estensione == ".docx":
                testo = estrai_testo_da_docx(percorso)
            else:
                print("Formato non supportato.")
                return None
            documento = {
                "nome_file": os.path.basename(percorso),
                "tipo": tipo,
                "testo": testo
            }
            print(f"Documento '{documento['nome_file']}' caricato e estratto ({len(testo)} caratteri).")
            return documento

        def salva_documento(documento):
            documenti = carica_tutti_documenti()
            documenti.append(documento)
            with open(DOCUMENTI_PATH, "w", encoding="utf-8") as f:
                json.dump(documenti, f, ensure_ascii=False, indent=2)

        def carica_tutti_documenti():
            if not os.path.isfile(DOCUMENTI_PATH):
                return []
            with open(DOCUMENTI_PATH, "r", encoding="utf-8") as f:
                return json.load(f)

        def input_lista(prompt):
            print(f"Inserisci {prompt} (scrivi 'fine' per terminare):")
            items = []
            while True:
                item = input(f"- {prompt} #{len(items)+1}: ")
                if item.lower() == "fine":
                    break
                items.append(item)
            return items

        def input_tabella(colonne, prompt="riga"):
            print(f"Inserisci {prompt} (scrivi 'fine' in una colonna per terminare):")
            righe = []
            while True:
                riga = {}
                for col in colonne:
                    val = input(f"{col}: ")
                    if val.lower() == "fine":
                        return righe
                    riga[col] = val
                righe.append(riga)
                print("Riga aggiunta.")
            return righe

        # Importa le funzioni dei nodi dal modulo graph_builder
        from graph_builder import (
            initial_planning,
            executive_summary,
            market_analysis,
            competitor_analysis,
            financial_plan,
            human_review,
            document_generation,
        )

        # Routing functions (copiate da graph_builder)
        def route_after_planning(state):
            return "executive_summary"
        def route_after_summary(state):
            return "market_analysis"
        def route_after_market_analysis(state):
            return "competitor_analysis"
        def route_after_competitor_analysis(state):
            return "financial_plan"
        def route_after_financial_plan(state):
            return "human_review"
        def route_after_human_review(state):
            if state.get("human_feedback", {}).get("requires_changes", False):
                section_to_modify = state["human_feedback"].get("section_to_modify", "")
                if section_to_modify == "Sommario Esecutivo":
                    return "executive_summary"
                elif section_to_modify == "Analisi di Mercato":
                    return "market_analysis"
                elif section_to_modify == "Analisi Competitiva":
                    return "competitor_analysis"
                elif section_to_modify == "Piano Finanziario":
                    return "financial_plan"
                else:
                    return "document_generation"
            else:
                return "document_generation"
        def route_after_document_generation(state):
            return None  # END

        node_functions = {
            "initial_planning": initial_planning,
            "executive_summary": executive_summary,
            "market_analysis": market_analysis,
            "competitor_analysis": competitor_analysis,
            "financial_plan": financial_plan,
            "human_review": human_review,
            "document_generation": document_generation,
        }
        routing_functions = {
            "initial_planning": route_after_planning,
            "executive_summary": route_after_summary,
            "market_analysis": route_after_market_analysis,
            "competitor_analysis": route_after_competitor_analysis,
            "financial_plan": route_after_financial_plan,
            "human_review": route_after_human_review,
            "document_generation": route_after_document_generation,
        }

        # --- Fase 1: Caricamento documenti ---
        print("\n--- Caricamento documenti iniziali ---")
        documenti = []
        while True:
            scelta = input("Vuoi caricare un documento? (s/n): ").strip().lower()
            if scelta == "s":
                doc = carica_documento()
                if doc:
                    salva_documento(doc)
                    documenti.append(doc)
            elif scelta == "n":
                break
            else:
                print("Risposta non valida. Scrivi 's' per sì o 'n' per no.")

        print(f"\nHai caricato {len(documenti)} documenti.")
        print("Analisi e indicizzazione dei documenti in corso... (placeholder)")

        # Passa il testo dei documenti come contesto nello stato
        if documenti:
            state["documents_text"] = "\n\n".join(doc["testo"] for doc in documenti if doc.get("testo"))
        else:
            state["documents_text"] = ""

        # --- Fase 1.5: Raccolta informazioni base obbligatorie ---
        print("\n--- Inserisci le informazioni di base sull'azienda (premi INVIO per usare i valori predefiniti) ---")
        def chiedi_con_default(prompt, default=""):
            while True:
                val = input(f"{prompt} [{default}] ").strip()
                if val:
                    return val
                elif default:
                    return default
                print("Questo campo è obbligatorio (non c'è un valore predefinito).")

        defaults = {
            "company_name": "Azienda Demo S.r.l.",
            "business_sector": "Software e Consulenza IT",
            "company_description": "Sviluppo di soluzioni software personalizzate e servizi di consulenza tecnologica per PMI.",
            "year_founded": "2023",
            "num_employees": "5",
            "main_products": "Software gestionale, App mobile, Consulenza strategica IT",
            "target_market": "B2B",
            "area": "Italia",
            "plan_objectives": "Ottenere finanziamento seed da 100k€, raggiungere 10 clienti entro 1 anno",
            "time_horizon": "3 anni",
            "funding_needs": "Seed, 100.000€"
        }

        state["company_name"] = chiedi_con_default("Nome completo dell'azienda:", defaults["company_name"])
        state["business_sector"] = chiedi_con_default("Settore/industria:", defaults["business_sector"])
        state["company_description"] = chiedi_con_default("Descrizione breve dell'attività (max 2-3 frasi):", defaults["company_description"])
        state["year_founded"] = chiedi_con_default("Anno di fondazione (o 'startup'):", defaults["year_founded"])
        state["num_employees"] = chiedi_con_default("Numero di dipendenti (attuale o previsto):", defaults["num_employees"])
        state["main_products"] = chiedi_con_default("Prodotti/servizi principali:", defaults["main_products"])
        state["target_market"] = chiedi_con_default("Mercato target (B2B, B2C, ecc.):", defaults["target_market"])
        state["area"] = chiedi_con_default("Area geografica di riferimento:", defaults["area"])
        state["plan_objectives"] = chiedi_con_default("Obiettivi principali del business plan:", defaults["plan_objectives"])
        state["time_horizon"] = chiedi_con_default("Orizzonte temporale (1 anno, 3 anni, 5 anni):", defaults["time_horizon"])
        state["funding_needs"] = chiedi_con_default("Se cerchi finanziamento, di che tipo e importo (o 'nessuno'):", defaults["funding_needs"])

        print("\nInformazioni di base raccolte con successo.")

        # --- Fase 2: Flusso interattivo controllato dall'utente ---
        current_node = "initial_planning"
        history = []
        while current_node:
            print(f"\n--- Nodo corrente: {current_node} ---")

            # Se ci sono documenti caricati, chiedi quali includere per questa sezione
            section_docs_text = ""
            if documenti:
                print("\nDocumenti disponibili per il contesto di questa sezione:")
                for idx, doc in enumerate(documenti):
                    anteprima = (doc.get("testo", "")[:120] + "...") if doc.get("testo") and len(doc.get("testo", "")) > 120 else doc.get("testo", "")
                    print(f"  [{idx+1}] {doc.get('nome_file', 'Documento')} ({doc.get('tipo', 'tipo sconosciuto')}): {anteprima}")
                print("Seleziona i numeri dei documenti da includere separati da virgola (es: 1,3), oppure lascia vuoto per nessuno:")
                scelta = input("Documenti da includere: ").strip()
                if scelta:
                    try:
                        indices = [int(x.strip())-1 for x in scelta.split(",") if x.strip().isdigit()]
                        section_docs = [documenti[i] for i in indices if 0 <= i < len(documenti)]
                        section_docs_text = "\n\n".join(doc.get("testo", "") for doc in section_docs if doc.get("testo"))
                    except Exception as e:
                        print(f"Errore nella selezione: {e}")
                        section_docs_text = ""
                else:
                    section_docs_text = ""
            # Passa il contesto selezionato nello stato
            state["section_documents_text"] = section_docs_text

            node_fn = node_functions[current_node]
            # Store the state *before* calling the node for potential re-runs/edits
            current_state_snapshot = state.copy() 
            result = node_fn(current_state_snapshot)
            # Store node name, input state, and result in history
            history.append((current_node, current_state_snapshot, result)) 
            # --- Visualizzazione migliorata del testo generato ---
            from textwrap import fill
            try:
                from colorama import Fore, Style, init as colorama_init
                colorama_init()
                COLOR_ENABLED = True
            except ImportError:
                COLOR_ENABLED = False

            def print_boxed(text, color=None):
                lines = text.splitlines()
                width = max(len(line) for line in lines) if lines else 0
                border = "+" + "-" * (width + 2) + "+"
                if color and COLOR_ENABLED:
                    print(getattr(Fore, color.upper(), ""), end="")
                print(border)
                for line in lines:
                    print(f"| {line.ljust(width)} |")
                print(border)
                if color and COLOR_ENABLED:
                    print(Style.RESET_ALL, end="")

            def page_output(text, lines_per_page=20):
                lines = text.splitlines()
                for i in range(0, len(lines), lines_per_page):
                    chunk = lines[i:i+lines_per_page]
                    print("\n".join(chunk))
                    if i + lines_per_page < len(lines):
                        input("-- Premi INVIO per continuare --")

            # Visualizza tutti i messaggi generati dal nodo
            for msg in result.get("messages", []):
                content = msg.get("content", str(msg)) if isinstance(msg, dict) else (msg.content if hasattr(msg, "content") else str(msg))
                print_boxed(fill(content, width=100), color="cyan")
                # page_output(content)  # Uncomment for paging if needed

            # Menu interattivo
            while True:
                print("\nAzioni disponibili:")
                print("  [avanti]  Vai al prossimo nodo")
                print("  [indietro] Torna al nodo precedente")
                print("  [modifica] Modifica l'output corrente")
                print("  [salva]   Salva lo stato attuale")
                print("  [aiuto]   Mostra questo menu")
                print("  [esci]    Termina il programma")
                scelta = input("Cosa vuoi fare? ").strip().lower()
                if scelta == "avanti":
                    if current_node == "human_review":
                        next_node = routing_functions["human_review"](state)
                    else:
                        next_node = routing_functions[current_node](state)
                    if next_node is None or next_node == "END":
                        print("Flusso completato.")
                        current_node = None
                    else:
                        current_node = next_node
                    break
                elif scelta == "indietro":
                    if len(history) > 1:
                        history.pop()
                        current_node, _ = history[-1]
                        print(f"Tornato al nodo: {current_node}")
                        break
                    else:
                        print("Sei già all'inizio del flusso.")
                elif scelta == "modifica":
                    # Permetti modifica del testo generato per qualsiasi nodo precedente
                    print("\n--- Modifica testo generato ---")
                    if not history:
                        print("Nessun nodo da modificare.")
                        continue
                    print("Seleziona il nodo da modificare:")
                    for idx, (node_name, _, node_result) in enumerate(history): # Adjusted history tuple
                        print(f"  [{idx+1}] {node_name}")
                    try:
                        idx_sel = input(f"Inserisci il numero del nodo (1-{len(history)}) o premi INVIO per il corrente: ").strip()
                        if idx_sel == "":
                            idx_mod = len(history) - 1
                        else:
                            idx_mod = int(idx_sel) - 1
                        if not (0 <= idx_mod < len(history)):
                            print("Indice non valido.")
                            continue
                    except Exception:
                        print("Input non valido.")
                        continue
                    
                    node_name, original_state, original_result = history[idx_mod]
                    
                    # Recupera il testo originale generato
                    original_text = None
                    for msg in original_result.get("messages", []):
                        original_text = msg.get("content", str(msg)) if isinstance(msg, dict) else (msg.content if hasattr(msg, "content") else str(msg))
                    if not original_text:
                        print("Nessun testo originale da modificare.")
                        continue
                        
                    print(f"\nNodo selezionato: {node_name}")
                    print("Testo attuale (puoi copiarlo e modificarlo):\n")
                    print_boxed(fill(original_text, width=100), color="yellow")
                    print("\nInserisci le tue modifiche o istruzioni (es: 'aggiungi dettagli su X', 'rendilo più formale', 'sostituisci Y con Z'). Termina con una riga contenente solo 'FINE':")
                    
                    edit_instructions_lines = []
                    while True:
                        try:
                            line = input("> ") 
                            if line.strip().upper() == "FINE":
                                break
                            edit_instructions_lines.append(line)
                        except EOFError:
                            print("\nInput terminato.")
                            break
                        except KeyboardInterrupt:
                            print("\nModifica annullata.")
                            edit_instructions_lines = None
                            break
                    
                    if edit_instructions_lines is not None:
                        edit_instructions = "\n".join(edit_instructions_lines).strip()
                        if edit_instructions:
                            print("Applico le modifiche con LLM...")
                            # Prepara lo stato per la rigenerazione (usa lo stato originale del nodo)
                            regen_state = original_state.copy()
                            regen_state["edit_instructions"] = edit_instructions
                            regen_state["original_text"] = original_text # Passa il testo originale per il contesto
                            
                            # Chiama una funzione di rigenerazione (potrebbe essere la stessa node_fn o una dedicata)
                            # Assumiamo che le node_fn possano gestire 'edit_instructions' e 'original_text'
                            try:
                                regen_fn = node_functions[node_name] # Usa la stessa funzione del nodo
                                new_result = regen_fn(regen_state)
                                
                                # Aggiorna la history con il nuovo risultato
                                history[idx_mod] = (node_name, original_state, new_result) # Mantiene lo stato originale, aggiorna il risultato
                                print("Testo rigenerato con successo.")
                                
                                # Mostra il nuovo testo
                                for msg in new_result.get("messages", []):
                                    content = msg.get("content", str(msg)) if isinstance(msg, dict) else (msg.content if hasattr(msg, "content") else str(msg))
                                    print_boxed(fill(content, width=100), color="green")

                            except Exception as e:
                                print(f"Errore durante la rigenerazione: {e}")
                        else:
                            print("Nessuna istruzione di modifica fornita.")
                elif scelta == "salva":
                    print("Funzione di salvataggio non ancora implementata. (TODO)")
                elif scelta == "aiuto":
                    print("Comandi disponibili: avanti, indietro, modifica, salva, aiuto, esci")
                elif scelta == "esci":
                    print("Uscita dal programma.")
                    sys.exit(0)
                else:
                    print("Comando non riconosciuto. Scrivi 'aiuto' per vedere i comandi disponibili.")
    
    if args.edit_section:
        # Modifica una sezione specifica
        print(f"Modifica della sezione: {args.edit_section}")
        # Implementazione della modifica della sezione
        # ...
    
    if args.search:
        # Esegui ricerche di mercato
        print(f"Ricerca di mercato per: {args.search}")
        # Implementazione della ricerca di mercato
        # ...
    
    if args.output:
        # Genera il documento finale
        print(f"Generazione del documento finale: {args.output}")
        generate_docx(state, args.output)
        print(f"Business plan generato con successo: {args.output}")

if __name__ == "__main__":
    main()
