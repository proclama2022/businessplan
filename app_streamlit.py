#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streamlit Interface for Business Plan Builder
"""

# Import path fix
import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    print(f"Added {current_dir} to Python path")

# Verifica se esiste un file .env e caricalo
try:
    from dotenv import load_dotenv
    # Forza il ricaricamento delle variabili d'ambiente
    load_dotenv(override=True)
    print("File .env caricato con successo")
except ImportError:
    print("dotenv non installato, utilizzo solo variabili d'ambiente esistenti")
except Exception as e:
    print(f"Errore nel caricamento del file .env: {e}")

# Verifica che la chiave OpenAI API sia disponibile
import os
if not os.environ.get("OPENAI_API_KEY"):
    try:
        # Prova a caricare da Streamlit secrets
        import streamlit as st
        # Accedi direttamente alla chiave API in secrets.toml
        if "OPENAI_API_KEY" in st.secrets:
            os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
            print("Chiave OpenAI API caricata da Streamlit secrets")
        else:
            print("ATTENZIONE: Chiave OpenAI API non trovata in Streamlit secrets")
            # Stampa le chiavi disponibili in secrets per debug (senza mostrare i valori)
            if hasattr(st, "secrets") and st.secrets:
                print(f"Chiavi disponibili in secrets: {list(st.secrets.keys())}")
    except Exception as e:
        print(f"Errore nel caricamento della chiave OpenAI API da Streamlit secrets: {e}")
        import traceback
        traceback.print_exc()

import json
from datetime import datetime
from pypdf import PdfReader
from docx import Document
import sys
import traceback # Aggiunto per debug errori ricerca

# Importa streamlit all'inizio
import streamlit as st

# Carica CSS personalizzato
def load_custom_css():
    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".streamlit", "style.css")
    if os.path.exists(css_file):
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        print(f"File CSS non trovato: {css_file}")

# Applica il CSS personalizzato
load_custom_css()

# Assicurati che le variabili d'ambiente dal file .env siano caricate
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Se dotenv non è installato, ignora (ma raccomandato per caricare la chiave API)

# Assicurati che la directory principale sia nel path per importare i moduli
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa i componenti del sistema (potrebbe richiedere aggiustamenti)
try:
    from config import Config
    from state import BusinessPlanState, initialize_state
    from graph_builder import (
        build_business_plan_graph,
        node_functions,
        # Importa o replica le funzioni di routing qui
        route_after_planning, route_after_summary,
        route_after_company_description, route_after_products_and_services,
        route_after_market_analysis, route_after_competitor_analysis,
        route_after_marketing_strategy, route_after_operational_plan,
        route_after_organization_and_management, route_after_risk_analysis,
        route_after_financial_plan, route_after_human_review,
        route_after_document_generation
    )
    from database.vector_store import VectorDatabase # Se necessario
    # from tools.docx_generator import generate_docx # Se necessario
    from search.combined_search import CombinedSearch # Importa la classe per la ricerca combinata

    # Importa il modulo direct_generator per supportare i nomi delle funzioni in italiano
    try:
        import direct_generator
        print("Modulo direct_generator importato con successo")
    except ImportError as e:
        print(f"Errore nell'importare il modulo direct_generator: {e}")

    # Importa il modulo di integrazione finanziaria
    try:
        import financial_integration
        print("Modulo financial_integration importato con successo")
    except ImportError as e:
        print(f"Errore nell'importare il modulo financial_integration: {e}")

    # Inizializza il modulo finanziario
    try:
        from financial.ui import FinancialUI
        # Check if already initialized
        if 'financial_ui' not in st.session_state:
            st.session_state.financial_ui = FinancialUI()
            print("Interfaccia finanziaria inizializzata")
    except ImportError as e:
        print(f"Errore importazione FinancialUI: {e}")
        # Create a stub class as fallback
        class StubFinancialUI:
            def __init__(self):
                self.data = None
                print("Stub FinancialUI inizializzata come fallback")

            def render_financial_summary(self, *args, **kwargs):
                st.info("Funzionalità finanziaria non disponibile")

            def render_key_metrics(self, *args, **kwargs):
                st.info("Funzionalità finanziaria non disponibile")

            def render_detailed_analysis(self, *args, **kwargs):
                st.info("Funzionalità finanziaria non disponibile")

        st.session_state.financial_ui = StubFinancialUI()
        st.warning("Modulo finanziario non disponibile. Usando fallback.")
    except Exception as e:
        st.warning(f"Errore inizializzazione modulo finanziario: {e}")
except ImportError as e:
    st.error(f"Errore nell'importare i moduli: {e}. Assicurati che i file siano nella stessa directory o nel PYTHONPATH.")
    st.stop()

# Mappa dei nomi dei nodi alle funzioni di routing (se non importate direttamente)
# Assicurati che queste funzioni siano definite o importate correttamente
routing_functions = {
    "initial_planning": route_after_planning,
    "executive_summary": route_after_summary,
    "company_description": route_after_company_description,
    "products_and_services": route_after_products_and_services,
    "market_analysis": route_after_market_analysis,
    "competitor_analysis": route_after_competitor_analysis,
    "marketing_strategy": route_after_marketing_strategy,
    "operational_plan": route_after_operational_plan,
    "organization_and_management": route_after_organization_and_management,
    "risk_analysis": route_after_risk_analysis,
    "financial_plan": route_after_financial_plan,
    "human_review": route_after_human_review,
    "document_generation": route_after_document_generation,
}


# --- Funzione per estrarre testo pulito dai risultati AI ---
def extract_pure_content(text):
    """
    Extracts the actual content text from the complex object or string representation.
    Uses aggressive pattern matching to isolate just the business plan text.
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

# --- Funzioni di utilità (adattate da main.py) ---
DOCUMENTI_PATH = "documenti_estratti.json" # Potremmo voler salvare in session_state invece che su file

@st.cache_data # Cache per evitare ricalcoli
def estrai_testo_da_pdf(file_bytes):
    # Streamlit passa bytes, non percorsi
    from io import BytesIO
    try:
        reader = PdfReader(BytesIO(file_bytes))
        testo = ""
        for pagina in reader.pages:
            testo += pagina.extract_text() or ""
        return testo
    except Exception as e:
        st.error(f"Errore nell'estrazione PDF: {e}")
        return ""

@st.cache_data
def estrai_testo_da_docx(file_bytes):
    from io import BytesIO
    try:
        doc = Document(BytesIO(file_bytes))
        testo = "\n".join([par.text for par in doc.paragraphs])
        return testo
    except Exception as e:
        st.error(f"Errore nell'estrazione DOCX: {e}")
        return ""

# --- Inizializzazione Session State ---
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_node = "initial_planning" # Nodo iniziale
    st.session_state.history = [] # Lista di tuple (node_name, input_state, result)
    st.session_state.documents = [] # Lista di dict {nome_file, tipo, testo}
    st.session_state.state_dict = initialize_state( # Stato LangGraph
        document_title="Business Plan - Nuova Azienda",
        company_name="Nuova Azienda",
        creation_date=datetime.now().strftime("%Y-%m-%d"),
        version=1
    )
    # Aggiungi flag per la modalità semplificata
    st.session_state.simplified_mode = False
    # Aggiungi campi per le info base allo stato
    st.session_state.state_dict.update({
        "business_sector": "", "company_description": "", "year_founded": "",
        "num_employees": "", "main_products": "", "target_market": "", "area": "",
        "plan_objectives": "", "time_horizon": "", "funding_needs": "",
        "documents_text": "", "section_documents_text": "",
        "custom_outline": None,  # Struttura personalizzata
        "temperature": Config.TEMPERATURE, # Aggiunto per le impostazioni
        "max_tokens": Config.MAX_TOKENS, # Aggiunto per le impostazioni
        "generation_count": 0, # Contatore per il limite di generazione
        "max_generations": 30 # Limite massimo di generazioni
    })
    st.session_state.current_output = "" # Output del nodo corrente
    st.session_state.edit_instructions = "" # Istruzioni per modifica

    # Inizializza il grafo con i nodi predefiniti
    # Nota: non usiamo custom_outline qui perché vogliamo usare i nodi predefiniti
    try:
        vector_db = VectorDatabase()
        st.session_state.graph = build_business_plan_graph(vector_db).compile() # Compila il grafo una sola volta
        print("Database vettoriale e grafo inizializzati con successo")
        st.session_state.graph_initialized = True
    except Exception as e:
        st.error(f"Errore nell'inizializzazione del database vettoriale: {e}")
        print(f"Errore dettagliato: {e}")
        import traceback
        traceback.print_exc()

        # Crea un grafo vuoto come fallback per evitare errori successivi
        from langgraph.graph import StateGraph
        dummy_graph = StateGraph(BusinessPlanState)
        dummy_graph.add_node("initial_planning", lambda x: x)
        dummy_graph.add_node("executive_summary", lambda x: x)
        dummy_graph.set_entry_point("initial_planning")
        st.session_state.graph = dummy_graph.compile()
        st.session_state.graph_initialized = False

        # Mostra un messaggio di errore all'utente
        st.warning("L'applicazione è in modalità limitata a causa di un errore di inizializzazione. Alcune funzionalità potrebbero non essere disponibili.")

    # --- Inizializzazione Client di Ricerca e Generazione --- (Migliorato)
    try:
        # Inizializza il client di ricerca combinata
        st.session_state.search_client = CombinedSearch(
            perplexity_api_key=st.secrets.get("PERPLEXITY_API_KEY") or os.getenv("PERPLEXITY_API_KEY")
        )
        st.session_state.search_available = True
        print("CombinedSearch inizializzato con successo.")

        # Inizializza anche le statistiche di ricerca
        st.session_state.search_stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "cached_searches": 0,
            "last_search_time": None
        }
    except Exception as e:
        st.session_state.search_available = False
        st.session_state.search_client = None
        print(f"Errore inizializzazione CombinedSearch: {e}")
        # Non mostrare errore all'utente qui, ma loggalo

    # Gemini è disabilitato, imposta lo stato di conseguenza
    st.session_state.gemini_available = False
    print("Supporto Gemini disabilitato in configurazione.")

# --- Funzione per eseguire la ricerca online --- (Migliorata)
def run_online_search(section_name: str, query_context: str):
    """
    Esegue una ricerca online avanzata in base alla sezione del business plan

    Args:
        section_name: Nome della sezione (es. "Analisi di Mercato")
        query_context: Contesto per la ricerca (es. descrizione azienda)
    """
    if not st.session_state.search_available or not st.session_state.search_client:
        st.warning("La funzionalità di ricerca online non è disponibile. Controlla le chiavi API.")
        return

    # Aggiorna statistiche
    if 'search_stats' in st.session_state:
        st.session_state.search_stats["total_searches"] += 1
        st.session_state.search_stats["last_search_time"] = datetime.now().strftime("%H:%M:%S")

    # Estrai informazioni di base dall'azienda
    company = st.session_state.state_dict.get('company_name', 'azienda')
    industry = st.session_state.state_dict.get('business_sector', 'settore sconosciuto')
    target = st.session_state.state_dict.get('target_market', 'mercato sconosciuto')
    region = st.session_state.state_dict.get('area', 'Italia')

    # Normalizza il nome della sezione per il matching
    section_name_lower = section_name.lower().replace('_', ' ')

    # Estrai informazioni aggiuntive utili per le ricerche specializzate
    company_stage = st.session_state.state_dict.get('company_stage', 'startup')
    funding_needs = st.session_state.state_dict.get('funding_needs', '')
    products = st.session_state.state_dict.get('main_products', '')
    company_size = "piccola"
    if st.session_state.state_dict.get('num_employees'):
        try:
            num_employees = int(st.session_state.state_dict.get('num_employees', '0'))
            if num_employees > 50:
                company_size = "media"
            if num_employees > 250:
                company_size = "grande"
        except:
            pass

    # Ottieni le opzioni di ricerca avanzate
    search_options = st.session_state.get('search_options', {})
    use_cache = search_options.get('use_cache', True)
    detailed = search_options.get('detailed', True)
    search_type_override = search_options.get('search_type', None)

    # Mostra informazioni sulla ricerca con badge per le opzioni
    st.info(f"Ricerca online per: '{section_name}' nel settore {industry}...")

    # Mostra le opzioni attive
    option_cols = st.columns(3)
    with option_cols[0]:
        st.caption(f"🔄 Cache: {'Attiva' if use_cache else 'Disattiva'}")
    with option_cols[1]:
        st.caption(f"🔍 Dettaglio: {'Alto' if detailed else 'Standard'}")
    with option_cols[2]:
        st.caption(f"⏱️ Tempo stimato: {'1-2 min' if detailed else '30-60 sec'}")

    with st.spinner("Esecuzione ricerca web in corso..."):
        try:
            # Determina il tipo di ricerca da utilizzare
            if search_type_override:
                # Usa il tipo di ricerca specificato dall'utente
                search_type = search_type_override
            elif "mercato" in section_name_lower or "market" in section_name_lower:
                search_type = "market_analysis"
            elif "competitiv" in section_name_lower or "competitor" in section_name_lower:
                search_type = "competitor_analysis"
            elif "trend" in section_name_lower or "tendenz" in section_name_lower:
                search_type = "trend_analysis"
            elif "finanz" in section_name_lower or "financial" in section_name_lower or "piano finanziario" in section_name_lower:
                search_type = "financial_analysis"
            elif "marketing" in section_name_lower or "commerciale" in section_name_lower or "vendite" in section_name_lower:
                search_type = "marketing_analysis"
            elif "operativ" in section_name_lower or "operation" in section_name_lower or "produzione" in section_name_lower:
                search_type = "operational_analysis"
            elif "swot" in section_name_lower:
                search_type = "swot_analysis"
            else:
                search_type = "generic_search"

            # Esegui la ricerca in base al tipo
            if search_type == "market_analysis":
                # Ricerca di mercato approfondita
                results = st.session_state.search_client.comprehensive_market_analysis(
                    company_name=company,
                    industry=industry,
                    target_market=target,
                    region=region,
                    detailed=detailed,
                    use_cache=use_cache
                )

            elif search_type == "competitor_analysis":
                # Analisi competitiva
                results = st.session_state.search_client.comprehensive_competitor_analysis(
                    company_name=company,
                    industry=industry,
                    target_market=target,
                    use_cache=use_cache
                )

            elif search_type == "trend_analysis":
                # Analisi dei trend di settore
                results = st.session_state.search_client.trend_analysis(
                    industry=industry,
                    timeframe=st.session_state.state_dict.get('time_horizon', 'prossimi 3 anni'),
                    use_cache=use_cache
                )

            elif search_type == "financial_analysis":
                # Analisi finanziaria
                results = st.session_state.search_client.financial_analysis(
                    company_name=company,
                    industry=industry,
                    company_stage=company_stage,
                    funding_needs=funding_needs,
                    use_cache=use_cache
                )

            elif search_type == "marketing_analysis":
                # Analisi di marketing
                results = st.session_state.search_client.marketing_strategy_analysis(
                    company_name=company,
                    industry=industry,
                    target_market=target,
                    products=products,
                    use_cache=use_cache
                )

            elif search_type == "operational_analysis":
                # Analisi operativa
                results = st.session_state.search_client.operational_plan_analysis(
                    company_name=company,
                    industry=industry,
                    company_size=company_size,
                    location=region,
                    use_cache=use_cache
                )

            elif search_type == "swot_analysis":
                # Analisi SWOT (usa l'analisi competitiva come base)
                query = f"Analisi SWOT dettagliata per {company}, azienda nel settore {industry} con target {target}. Includi punti di forza, debolezze, opportunità e minacce con esempi concreti."
                results = st.session_state.search_client.perplexity.search(
                    query=query,
                    model_size="pro" if detailed else "medium",
                    temperature=0.3,
                    max_tokens=2500 if detailed else 1800
                )

            else:
                # Ricerca generica per altre sezioni
                # Costruisci una query specifica
                query = f"Informazioni aggiornate per la sezione '{section_name}' di un business plan per un'azienda nel settore {industry}, mercato target {target}. {query_context}"

                # Usa il metodo di ricerca base
                results = st.session_state.search_client.perplexity.search(
                    query=query,
                    model_size="pro" if detailed else "medium",
                    temperature=0.3,
                    max_tokens=2500 if detailed else 1800
                )

            # Verifica se la ricerca ha avuto successo
            if results and "error" not in results:
                # Aggiorna statistiche
                if 'search_stats' in st.session_state:
                    st.session_state.search_stats["successful_searches"] += 1

                # Salva i risultati nello stato della sessione per visualizzarli
                st.session_state.last_search_results = results
                st.session_state.last_search_type = search_type

                # Salva anche i risultati nello stato principale per il generatore
                st.session_state.state_dict['perplexity_results'] = results

                st.success("✅ Ricerca completata con successo!")
            else:
                error_msg = results.get("error", "Errore sconosciuto nella ricerca")
                st.error(f"La ricerca non ha prodotto risultati validi: {error_msg}")
                st.session_state.last_search_results = {"error": error_msg, "status": "error"}

        except Exception as e:
            st.error(f"Errore durante la ricerca online: {e}")
            traceback.print_exc()  # Stampa traceback per debug
            st.session_state.last_search_results = {"error": str(e), "status": "error"}

# Ottieni la lista ordinata dei nodi/sezioni
node_keys = list(node_functions.keys())

# Verifica che tutte le sezioni necessarie siano presenti
required_sections = [
    "executive_summary", "company_description", "products_and_services",
    "market_analysis", "competitor_analysis", "marketing_strategy",
    "operational_plan", "organization_and_management", "risk_analysis",
    "financial_plan"
]

# Log per debug
print("Nodi disponibili:", node_keys)
missing_sections = [section for section in required_sections if section not in node_keys]
if missing_sections:
    print(f"ATTENZIONE: Sezioni mancanti in node_functions: {missing_sections}")

current_index = -1
if st.session_state.current_node in node_keys:
    current_index = node_keys.index(st.session_state.current_node)
else:
    # Prova a convertire il nome del nodo da italiano a inglese
    italian_node_name = st.session_state.current_node
    english_node_name = None

    # Mappa dei nomi dei nodi in italiano ai nomi in inglese
    italian_to_english = {
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
    normalized_variants = [
        italian_node_name,
        italian_node_name.replace(" ", "_"),
        italian_node_name.replace("'", "").replace(" ", "_"),
        italian_node_name.replace("'", "_").replace(" ", "_"),
        italian_node_name.replace("'", "").replace("-", "_").replace(" ", "_"),
        italian_node_name.replace("'", " ").replace("-", " "),
        italian_node_name.replace("'", "").replace("-", " ")
    ]

    # Cerca una corrispondenza nella mappa
    found_match = False
    for variant in normalized_variants:
        if variant in italian_to_english:
            english_node_name = italian_to_english[variant]
            if english_node_name in node_keys:
                current_index = node_keys.index(english_node_name)
                # Aggiorna il nodo corrente con il nome inglese
                st.session_state.current_node = english_node_name
                print(f"Nodo convertito da '{italian_node_name}' a '{english_node_name}' (variante: '{variant}')")
                found_match = True
                break

    if not found_match:
        if italian_node_name in italian_to_english:
            english_node_name = italian_to_english[italian_node_name]
            print(f"ATTENZIONE: Nodo convertito '{english_node_name}' non trovato in node_keys")
        else:
            print(f"ATTENZIONE: Nodo corrente '{st.session_state.current_node}' non trovato in node_keys")

# Verifica se siamo nella schermata iniziale
is_initial_screen = st.session_state.current_node == "initial_planning" and not st.session_state.current_output

# Importa i moduli per la modalità semplificata
try:
    from simplified_financial_tab import add_simplified_financial_tab
    from simplified_navigation import simplified_navigation_bar, add_context_help, simplified_section_selector
    simplified_modules_available = True
except ImportError as e:
    print(f"Errore nell'importazione dei moduli semplificati: {e}")
    simplified_modules_available = False

# --- Barra Laterale ---
with st.sidebar:
    # Logo e titolo
    if 'simplified_mode' in st.session_state and st.session_state.simplified_mode:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem;">
            <h1 style="color: #0066cc; margin-bottom: 0.5rem;">Business Plan</h1>
            <p style="color: #6c757d; font-size: 0.9rem;">Strumento semplificato</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem;">
            <h1 style="color: #0066cc; margin-bottom: 0.5rem;">Business Plan Builder</h1>
            <p style="color: #6c757d; font-size: 0.9rem;">Crea il tuo business plan in pochi passi</p>
        </div>
        """, unsafe_allow_html=True)

    # Pulsante per cambiare modalità
    if 'simplified_mode' in st.session_state and st.session_state.simplified_mode:
        if st.sidebar.button("🔄 Passa alla Modalità Completa", help="Torna all'interfaccia completa"):
            st.session_state.simplified_mode = False
            st.rerun()
    else:
        if st.sidebar.button("🔄 Passa alla Modalità Semplificata", help="Interfaccia più semplice per commercialisti"):
            st.session_state.simplified_mode = True
            st.rerun()

    # Separatore
    st.markdown('<hr style="margin: 0.5rem 0 1.5rem 0;">', unsafe_allow_html=True)

    # Contatore utilizzo
    if 'generation_count' in st.session_state.state_dict:
        gen_count = st.session_state.state_dict['generation_count']
        max_gen = st.session_state.state_dict['max_generations']

        # Calcola percentuale di utilizzo
        usage_pct = min(gen_count / max_gen, 1.0)

        # Mostra barra di avanzamento
        st.caption("📊 Utilizzo generazione")
        st.progress(usage_pct)

        # Mostra contatore testuale
        if usage_pct < 0.75:
            st.caption(f"Hai utilizzato {gen_count} di {max_gen} messaggi disponibili")
        elif usage_pct < 0.9:
            st.caption(f"⚠️ Hai utilizzato {gen_count} di {max_gen} messaggi disponibili")
        else:
            st.caption(f"🚨 Hai utilizzato {gen_count} di {max_gen} messaggi disponibili")

    # --- Navigazione tra le sezioni ---
    if not is_initial_screen:
        st.sidebar.divider()

        # Versione semplificata della navigazione
        if 'simplified_mode' in st.session_state and st.session_state.simplified_mode and simplified_modules_available:
            # Lista semplificata delle sezioni
            simplified_sections = [
                ("executive_summary", "Sommario Esecutivo"),
                ("company_description", "Descrizione Azienda"),
                ("products_and_services", "Prodotti e Servizi"),
                ("market_analysis", "Analisi di Mercato"),
                ("financial_plan", "Piano Finanziario"),
                ("document_generation", "Genera Documento")
            ]

            # Usa il selettore di sezioni semplificato
            simplified_section_selector(
                simplified_sections,
                st.session_state.current_node,
                st.session_state.history
            )
        else:
            # Navigazione standard
            st.sidebar.subheader("🧭 Navigazione")

        # Ottieni l'elenco dei nodi dal grafo
        try:
            # Verifica se il grafo è stato inizializzato correttamente
            if hasattr(st.session_state, 'graph_initialized') and not st.session_state.graph_initialized:
                # Usa una lista predefinita di nodi se il grafo non è stato inizializzato correttamente
                node_keys = [
                    "initial_planning", "executive_summary", "company_description",
                    "products_and_services", "market_analysis", "competitor_analysis",
                    "marketing_strategy", "operational_plan", "organization_and_management",
                    "risk_analysis", "financial_plan", "human_review", "document_generation"
                ]
                print("Usando lista predefinita di nodi perché il grafo non è stato inizializzato correttamente")
            else:
                # Usa i nodi dal grafo
                node_keys = list(st.session_state.graph.nodes.keys())
                # Rimuovi i nodi speciali (END, etc.)
                node_keys = [k for k in node_keys if not k.startswith("__")]
        except Exception as e:
            # Fallback a una lista predefinita di nodi in caso di errore
            print(f"Errore nell'accesso ai nodi del grafo: {e}")
            node_keys = [
                "initial_planning", "executive_summary", "company_description",
                "products_and_services", "market_analysis", "competitor_analysis",
                "marketing_strategy", "operational_plan", "organization_and_management",
                "risk_analysis", "financial_plan", "human_review", "document_generation"
            ]

        # Crea un dizionario per mappare i nomi dei nodi a nomi più leggibili
        node_display_names = {
            "initial_planning": "Pianificazione Iniziale",
            "executive_summary": "Sommario Esecutivo",
            "company_description": "Descrizione dell'Azienda",
            "products_and_services": "Prodotti e Servizi",
            "market_analysis": "Analisi di Mercato",
            "competitor_analysis": "Analisi Competitiva",
            "marketing_strategy": "Strategia di Marketing",
            "operational_plan": "Piano Operativo",
            "organization_and_management": "Organizzazione e Team",
            "risk_analysis": "Analisi dei Rischi",
            "financial_plan": "Piano Finanziario",
            "human_review": "Revisione Umana",
            "document_generation": "Generazione Documento"
        }

        # Crea pulsanti per ogni nodo con stile migliorato
        for i, node_key in enumerate(node_keys):
            display_name = node_display_names.get(node_key, node_key.replace("_", " ").title())

            # Evidenzia il nodo corrente
            is_current = node_key == st.session_state.current_node
            button_style = "primary" if is_current else "secondary"

            # Verifica se questa sezione ha già contenuto
            has_content = False
            for node_name, _, output in st.session_state.history:
                if node_name == node_key and output:
                    has_content = True
                    break

            # Aggiungi un'icona per indicare lo stato
            icon = "✅ " if has_content else "📝 "
            if is_current:
                icon = "🔍 "

            if st.sidebar.button(f"{icon}{display_name}", key=f"nav_{node_key}", type=button_style, use_container_width=True):
                st.session_state.current_node = node_key
                st.session_state.current_output = ""
                for node_name, _, output in st.session_state.history:
                    if node_name == node_key:
                        st.session_state.current_output = output
                        break
                st.rerun()

    # --- Dati di Esempio ---
    st.markdown("### 📊 Dati di Esempio")
    st.caption("Seleziona un esempio predefinito per testare l'applicazione rapidamente")

    # Importa il modulo per i dati di esempio
    from example_data_loader import get_example_names, get_example_by_id

    # Ottieni la lista degli esempi disponibili
    example_options = get_example_names()
    example_names = ["Nessun esempio"] + [ex["name"] for ex in example_options]
    example_ids = ["none"] + [ex["id"] for ex in example_options]

    # Crea un dizionario per mappare i nomi agli ID
    example_map = dict(zip(example_names, example_ids))

    # Selettore di esempi
    selected_example = st.selectbox(
        "Seleziona un esempio",
        example_names,
        index=0,
        help="Seleziona un esempio predefinito per popolare automaticamente i campi"
    )

    # Pulsante per caricare l'esempio selezionato
    if st.button("Carica Esempio", key="load_example_btn"):
        if selected_example != "Nessun esempio":
            example_id = example_map[selected_example]
            example_data = get_example_by_id(example_id)

            if example_data:
                # Aggiorna lo stato con i dati dell'esempio
                for key, value in example_data.items():
                    if key in st.session_state.state_dict:
                        st.session_state.state_dict[key] = value

                st.success(f"Dati di esempio '{selected_example}' caricati con successo!")
                st.rerun()

    st.markdown("---")

    # --- Informazioni Azienda (Essenziali) ---
    st.markdown("### 🏢 Informazioni Azienda")
    st.caption("Inserisci le informazioni essenziali della tua azienda")

    # Solo i campi più importanti
    st.session_state.state_dict['company_name'] = st.text_input(
        "Nome Azienda",
        st.session_state.state_dict.get('company_name', ''),
        help="Il nome della tua azienda"
    )

    st.session_state.state_dict['business_sector'] = st.text_input(
        "Settore",
        st.session_state.state_dict.get('business_sector', ''),
        help="Il settore in cui opera l'azienda"
    )

    st.session_state.state_dict['company_description'] = st.text_area(
        "Descrizione Breve",
        st.session_state.state_dict.get('company_description', ''),
        help="Una breve descrizione dell'azienda e della sua missione",
        height=100
    )

    # Separatore
    st.markdown('<hr style="margin: 1.5rem 0;">', unsafe_allow_html=True)

    # --- Impostazioni Essenziali ---
    st.markdown("### ⚙️ Impostazioni")

    # Checkbox per ricerca online con Perplexity
    st.session_state.state_dict['online_search_enabled'] = st.checkbox(
        "Abilita Ricerca Online",
        value=st.session_state.state_dict.get('online_search_enabled', True),
        key="online_search_enabled_toggle",
        help="Usa Perplexity per cercare informazioni aggiornate"
    )

    # --- Informazioni Aggiuntive (Opzionali) ---
    with st.expander("➕ Informazioni Aggiuntive", expanded=False):
        st.caption("Queste informazioni sono opzionali ma aiutano a personalizzare meglio il business plan")

        col1, col2 = st.columns(2)
        with col1:
            st.session_state.state_dict['year_founded'] = st.text_input(
                "Anno Fondazione",
                st.session_state.state_dict.get('year_founded', ''),
                help="L'anno in cui è stata fondata l'azienda"
            )
        with col2:
            st.session_state.state_dict['num_employees'] = st.text_input(
                "Numero Dipendenti",
                st.session_state.state_dict.get('num_employees', ''),
                help="Il numero attuale di dipendenti"
            )

        st.session_state.state_dict['area'] = st.text_input(
            "Area Geografica",
            st.session_state.state_dict.get('area', 'Italia'),
            help="L'area geografica in cui opera l'azienda"
        )

        st.session_state.state_dict['target_market'] = st.text_input(
            "Mercato Target",
            st.session_state.state_dict.get('target_market', ''),
            help="Descrivi il mercato target dell'azienda"
        )

        st.session_state.state_dict['main_products'] = st.text_input(
            "Prodotti/Servizi",
            st.session_state.state_dict.get('main_products', ''),
            help="I principali prodotti o servizi offerti"
        )

        # Imposta automaticamente il titolo del documento
        st.session_state.state_dict['document_title'] = f"Business Plan - {st.session_state.state_dict.get('company_name', 'Nuova Azienda')}"

    # --- Struttura del Business Plan ---
    with st.expander("🏗️ Struttura del Piano", expanded=False):
        # Inizializza la struttura personalizzata se non esiste
        if 'custom_outline' not in st.session_state.state_dict or st.session_state.state_dict['custom_outline'] is None:
            # Carica le sezioni standard dal file di configurazione
            try:
                with open('business_plan_config.json', 'r') as f:
                    config_data = json.load(f)
                    sezioni_standard = config_data.get('sezioni_standard', [])

                    # Crea un dizionario con tutte le sezioni standard
                    st.session_state.state_dict['custom_outline'] = {
                        sezione: [] for sezione in sezioni_standard
                    }

                    # Se il dizionario è vuoto (in caso di errore), usa le sezioni predefinite
                    if not st.session_state.state_dict['custom_outline']:
                        raise Exception("Nessuna sezione standard trovata")

            except Exception as e:
                print(f"Errore nel caricamento delle sezioni standard: {e}")
                # Fallback alle sezioni predefinite
                st.session_state.state_dict['custom_outline'] = {
                    "Sommario Esecutivo": [],
                    "Descrizione dell'Azienda": [],
                    "Prodotti e Servizi": [],
                    "Analisi di Mercato": [],
                    "Strategia di Marketing": [],
                    "Piano Operativo": [],
                    "Organizzazione e Team di Gestione": [],
                    "Analisi dei Rischi": [],
                    "Piano Finanziario": []
                }

        # Mostra la struttura attuale
        current_outline = st.session_state.state_dict['custom_outline']

        st.markdown("### Struttura Attuale")

        # Visualizzazione semplificata della struttura senza numeri
        for section, subsections in current_outline.items():
            st.markdown(f"**{section}**")
            if subsections:
                for subsection in subsections:
                    st.markdown(f"   • {subsection}")

        # Opzione semplificata per aggiungere una sezione
        st.markdown("---")
        st.markdown("### Aggiungi Sezione")

        new_section = st.text_input("Nome nuova sezione:", key="new_section_input")
        if st.button("Aggiungi Sezione", key="add_section_btn") and new_section:
            if new_section not in current_outline:
                current_outline[new_section] = []
                st.success(f"Sezione '{new_section}' aggiunta")
                st.rerun()
            else:
                st.warning(f"La sezione '{new_section}' esiste già")

        # Pulsante per resettare la struttura
        if st.button("Reset alla Struttura Predefinita", key="reset_structure_btn"):
            # Carica le sezioni standard dal file di configurazione
            try:
                with open('business_plan_config.json', 'r') as f:
                    config_data = json.load(f)
                    sezioni_standard = config_data.get('sezioni_standard', [])

                    # Crea un dizionario con tutte le sezioni standard
                    st.session_state.state_dict['custom_outline'] = {
                        sezione: [] for sezione in sezioni_standard
                    }

                    # Se il dizionario è vuoto (in caso di errore), usa le sezioni predefinite
                    if not st.session_state.state_dict['custom_outline']:
                        raise Exception("Nessuna sezione standard trovata")

            except Exception as e:
                print(f"Errore nel caricamento delle sezioni standard: {e}")
                # Fallback alle sezioni predefinite
                st.session_state.state_dict['custom_outline'] = {
                    "Sommario Esecutivo": [],
                    "Descrizione dell'Azienda": [],
                    "Prodotti e Servizi": [],
                    "Analisi di Mercato": [],
                    "Strategia di Marketing": [],
                    "Piano Operativo": [],
                    "Organizzazione e Team di Gestione": [],
                    "Analisi dei Rischi": [],
                    "Piano Finanziario": []
                }
            st.success("Struttura resettata alla configurazione predefinita")
            st.rerun()

    # --- Gestione Documenti ---
    with st.expander("📄 Documenti di Riferimento"):
        uploaded_files = st.file_uploader("Carica documenti (PDF, DOCX)", accept_multiple_files=True, type=['pdf', 'docx'])
        if uploaded_files:
            for uploaded_file in uploaded_files:
                # Evita duplicati basati sul nome
                if not any(doc['nome_file'] == uploaded_file.name for doc in st.session_state.documents):
                    file_bytes = uploaded_file.getvalue()
                    testo = ""
                    if uploaded_file.type == "application/pdf":
                        testo = estrai_testo_da_pdf(file_bytes)
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        testo = estrai_testo_da_docx(file_bytes)

                    if testo:
                        doc_info = {
                            "nome_file": uploaded_file.name,
                            "tipo": "Caricato", # Potremmo chiedere il tipo all'utente
                            "testo": testo
                        }
                        st.session_state.documents.append(doc_info)
                        st.success(f"'{uploaded_file.name}' caricato ed estratto.")
                    else:
                        st.warning(f"Impossibile estrarre testo da '{uploaded_file.name}'.")
            # Aggiorna il contesto generale dei documenti nello stato
            st.session_state.state_dict['documents_text'] = "\n\n---\n\n".join([doc['testo'] for doc in st.session_state.documents])

        st.write("Documenti Caricati:")
        if st.session_state.documents:
            for i, doc in enumerate(st.session_state.documents):
                st.markdown(f"- {doc['nome_file']} ({len(doc['testo'])} caratteri)")
        else:
            st.write("Nessun documento caricato.")

    # --- Impostazioni di Generazione ---
    with st.expander("🔧 Impostazioni Generazione"):
        st.session_state.state_dict['temperature'] = st.slider("Temperatura (Creatività)", 0.0, 1.0, st.session_state.state_dict.get('temperature', Config.TEMPERATURE), 0.1)
        st.session_state.state_dict['max_tokens'] = st.slider("Lunghezza Massima (Token)", 100, 4000, st.session_state.state_dict.get('max_tokens', Config.MAX_TOKENS), 100)

        # Opzione per regolare il limite di generazioni
        st.markdown("### Limite Generazioni")
        current_max = st.session_state.state_dict.get('max_generations', 30)
        current_count = st.session_state.state_dict.get('generation_count', 0)

        # Mostra il contatore attuale
        st.caption(f"Generazioni utilizzate: {current_count}/{current_max}")

        # Slider per regolare il limite
        new_max = st.number_input(
            "Limite massimo messaggi",
            min_value=current_count,
            max_value=100,
            value=current_max,
            step=5,
            help="Imposta il numero massimo di messaggi che possono essere generati"
        )

        # Aggiorna il limite se cambiato
        if new_max != current_max:
            st.session_state.state_dict['max_generations'] = new_max
            st.success(f"Limite di generazione aggiornato a {new_max} messaggi")

        # Pulsante per resettare il contatore (solo per scopi di test)
        if st.button("🔄 Reset Contatore (Test)", key="reset_gen_counter"):
            st.session_state.state_dict['generation_count'] = 0
            st.success("Contatore di generazione resettato")
            st.rerun()

        # Aggiungere altre impostazioni se necessario (modello, ecc.)

# --- Area Principale ---
st.title("🚀 Business Plan Builder")

# Importa il modulo per la tab finanziaria
try:
    import financial_tab
    print("Modulo financial_tab importato con successo")
except ImportError as e:
    print(f"Errore nell'importare il modulo financial_tab: {e}")

# Mostra un messaggio di benvenuto solo nella schermata iniziale
if is_initial_screen:
    # Crea un container con stile per il messaggio di benvenuto
    welcome_container = st.container(border=True)
    with welcome_container:
        st.markdown("### 👋 Benvenuto nel Business Plan Builder!")
        st.markdown("""
        Questo strumento ti aiuta a creare un business plan professionale utilizzando l'intelligenza artificiale.

        **Come iniziare:**
        1. Inserisci le informazioni sulla tua azienda nella barra laterale
        2. Naviga tra le diverse sezioni del business plan
        3. Utilizza la ricerca online per ottenere dati aggiornati
        4. Genera e personalizza il contenuto di ogni sezione
        5. Esporta il business plan completo quando hai finito

        Buon lavoro! 🚀
        """)

        # Aggiungi opzione per generare rapidamente un business plan completo
        st.markdown("### ⚡ Generazione Rapida")
        st.caption("Genera un business plan completo con un solo clic")

        # Importa il modulo per i dati di esempio
        from example_data_loader import get_example_names, get_example_by_id
        from quick_generator import generate_full_business_plan, update_session_state_with_results

        # Ottieni la lista degli esempi disponibili
        example_options = get_example_names()
        example_names = ["Seleziona un esempio..."] + [ex["name"] for ex in example_options]
        example_ids = ["none"] + [ex["id"] for ex in example_options]

        # Crea un dizionario per mappare i nomi agli ID
        example_map = dict(zip(example_names, example_ids))

        # Layout a colonne per il selettore e il pulsante di generazione rapida
        col1, col2 = st.columns([3, 1])

        with col1:
            quick_example = st.selectbox(
                "Seleziona un esempio",
                example_names,
                index=0,
                key="quick_example_select"
            )

        with col2:
            generate_quick = st.button("Genera", key="quick_generate", type="primary")

        if generate_quick and quick_example != "Seleziona un esempio...":
            example_id = example_map[quick_example]
            example_data = get_example_by_id(example_id)

            if example_data:
                # Verifica il limite di generazione
                gen_count = st.session_state.state_dict.get('generation_count', 0)
                max_gen = st.session_state.state_dict.get('max_generations', 30)

                # Il business plan completo genererà più sezioni
                remaining_gen = max_gen - gen_count
                sezioni_da_generare = 10  # Stima del numero di sezioni che verranno generate

                if remaining_gen < sezioni_da_generare:
                    st.error(f"⛔ Non hai abbastanza generazioni disponibili. Hai {remaining_gen} generazioni rimanenti, ma la generazione rapida ne richiede circa {sezioni_da_generare}.")
                    st.info("Puoi aumentare il limite nelle impostazioni o generare manualmente le sezioni più importanti.")
                else:
                    # Aggiorna lo stato con i dati dell'esempio
                    temp_state = st.session_state.state_dict.copy()
                    for key, value in example_data.items():
                        if key in temp_state:
                            temp_state[key] = value

                    # Genera il business plan completo
                    with st.spinner("Generazione del business plan completo in corso..."):
                        results = generate_full_business_plan(temp_state)

                        # Aggiorna lo stato della sessione con i risultati
                        for key, value in example_data.items():
                            if key in st.session_state.state_dict:
                                st.session_state.state_dict[key] = value

                        # Aggiorna la cronologia con i risultati
                        update_session_state_with_results(results)

                        # Aggiorna il contatore di generazione
                        # Conta il numero di sezioni generate
                        sections_generated = len(results) if results else 0
                        st.session_state.state_dict['generation_count'] = gen_count + sections_generated

                    st.success(f"Business plan completo generato con successo per '{quick_example}'!")
                    st.rerun()

        # Pulsante per iniziare con la navigazione delle sezioni
        if st.button("Iniziamo!", type="primary", key="welcome_dismiss"):
            # Passa alla prima sezione effettiva (salta initial_planning)
            try:
                # Ottieni i nodi dal grafo se disponibile
                if hasattr(st.session_state, 'graph') and st.session_state.graph:
                    try:
                        welcome_node_keys = list(st.session_state.graph.nodes.keys())
                        welcome_node_keys = [k for k in welcome_node_keys if not k.startswith("__")]
                    except:
                        # Fallback a una lista predefinita
                        welcome_node_keys = [
                            "initial_planning", "executive_summary", "company_description",
                            "products_and_services", "market_analysis", "competitor_analysis"
                        ]
                else:
                    # Usa una lista predefinita
                    welcome_node_keys = [
                        "initial_planning", "executive_summary", "company_description",
                        "products_and_services", "market_analysis", "competitor_analysis"
                    ]

                if len(welcome_node_keys) > 1:
                    st.session_state.current_node = welcome_node_keys[1]  # Passa alla seconda sezione (la prima è initial_planning)
                else:
                    # Fallback a una sezione predefinita
                    st.session_state.current_node = "executive_summary"

                st.session_state.current_output = ""  # Resetta l'output corrente
                st.rerun()
            except Exception as e:
                print(f"Errore nel passaggio alla prima sezione: {e}")
                # Fallback a una sezione predefinita
                st.session_state.current_node = "executive_summary"
                st.session_state.current_output = ""
                st.rerun()

# Non mostrare la navigazione nella schermata iniziale
if not is_initial_screen:
    # Verifica se siamo in modalità semplificata
    if 'simplified_mode' in st.session_state and st.session_state.simplified_mode and simplified_modules_available:
        # Usa la barra di navigazione semplificata
        current_node_name = st.session_state.current_node.replace('_', ' ').title()
        st.header(current_node_name, anchor=False)

        # Lista semplificata delle sezioni
        simplified_sections = [
            ("executive_summary", "Sommario Esecutivo"),
            ("company_description", "Descrizione Azienda"),
            ("products_and_services", "Prodotti e Servizi"),
            ("market_analysis", "Analisi di Mercato"),
            ("financial_plan", "Piano Finanziario"),
            ("document_generation", "Genera Documento")
        ]

        # Usa la barra di navigazione semplificata
        simplified_navigation_bar(
            simplified_sections,
            st.session_state.current_node
        )

        # Aggiungi aiuto contestuale
        add_context_help(st.session_state.current_node)
    else:
        # Interfaccia di navigazione standard
        with st.container(border=True):
            # Mostra il titolo della sezione corrente in modo più prominente
            current_node_name = st.session_state.current_node.replace('_', ' ').title()
            st.header(current_node_name, anchor=False)

            # Barra di progresso semplificata
            total_steps = len(node_keys)

            # Trova l'indice del nodo corrente
            try:
                current_index = node_keys.index(st.session_state.current_node)
            except (ValueError, AttributeError):
                # Se il nodo corrente non è nella lista, usa 0 come fallback
                current_index = 0

            progress_percentage = ((current_index + 1) / total_steps) * 100

            # Mostra il progresso in modo più chiaro
            st.progress(progress_percentage / 100)
            st.caption(f"Sezione {current_index + 1} di {total_steps}")

            # Pulsanti di navigazione
            cols = st.columns([1, 1, 1])

            with cols[0]:
                # Pulsante per la sezione precedente
                if current_index > 0:
                    prev_node = node_keys[current_index - 1]
                    prev_node_name = prev_node.replace('_', ' ').title()
                    if st.button(f"◀️ {prev_node_name}", use_container_width=True):
                        st.session_state.current_node = prev_node
                        # Carica l'output esistente se disponibile
                        st.session_state.current_output = ""
                        for node, _, output in reversed(st.session_state.history):
                            if node == prev_node and output and not output.startswith("Errore"):
                                st.session_state.current_output = output
                                break
                        st.rerun()

            with cols[2]:
                # Pulsante per la sezione successiva
                if current_index < len(node_keys) - 1:
                    next_node = node_keys[current_index + 1]
                    next_node_name = next_node.replace('_', ' ').title()
                    if st.button(f"{next_node_name} ▶️", use_container_width=True):
                        # Salva l'output corrente prima di passare alla sezione successiva
                        if st.session_state.current_output:
                            # Cerca se esiste già un entry per questo nodo
                            existing_entry = False
                            for i, (node, ctx, _) in enumerate(st.session_state.history):
                                if node == st.session_state.current_node:
                                    # Aggiorna l'entry esistente
                                    st.session_state.history[i] = (node, ctx, st.session_state.current_output)
                                    existing_entry = True
                                    break

                            # Se non esiste, aggiungi una nuova entry
                            if not existing_entry:
                                try:
                                    context = prepare_generation_context()
                                except:
                                    context = st.session_state.state_dict.copy()
                                st.session_state.history.append((st.session_state.current_node, context, st.session_state.current_output))

                        # Passa alla sezione successiva
                        st.session_state.current_node = next_node
                        # Carica l'output esistente se disponibile
                        st.session_state.current_output = ""
                        for node, _, output in reversed(st.session_state.history):
                            if node == next_node and output and not output.startswith("Errore"):
                                st.session_state.current_output = output
                                break
                        st.rerun()

# La sezione di ricerca è stata spostata nella tab Ricerca

# --- Visualizzazione Risultati Ricerca ---
if not is_initial_screen and 'last_search_results' in st.session_state and st.session_state.last_search_results:
    results_data = st.session_state.last_search_results
    search_type = st.session_state.get('last_search_type', 'generic')

    # Contenitore per i risultati
    with st.expander("📊 Risultati della Ricerca", expanded=True):
        st.caption("Informazioni trovate online che puoi utilizzare nel tuo business plan")

    # Verifica se ci sono errori
    if isinstance(results_data, dict) and "error" in results_data:
        st.error(f"Errore dalla ricerca: {results_data['error']}")
    else:
        # Mostra i risultati senza titolo duplicato

        # Visualizzazione in base al tipo di ricerca
        if search_type == "market_analysis":
            # Visualizzazione per analisi di mercato
            tabs = st.tabs(["Panoramica", "Dimensione Mercato", "Trend", "Competitor", "Opportunità", "Fonti"])

            with tabs[0]:
                # Panoramica generale
                if "raw_text" in results_data and results_data["raw_text"]:
                    st.markdown("### Sintesi dell'Analisi di Mercato")
                    # Mostra solo i primi 500 caratteri con espansione
                    raw_text = results_data["raw_text"]
                    st.markdown(raw_text[:500] + "..." if len(raw_text) > 500 else raw_text)
                    if len(raw_text) > 500:
                        with st.expander("Mostra testo completo"):
                            st.markdown(raw_text)

            with tabs[1]:
                # Dimensione del mercato
                if "market_size" in results_data and results_data["market_size"]:
                    st.markdown("### Dimensione del Mercato")
                    market_size = results_data["market_size"]
                    if isinstance(market_size, dict):
                        if "description" in market_size:
                            st.markdown(market_size["description"])
                        if "value" in market_size:
                            st.metric("Valore stimato", market_size["value"])
                        if "cagr" in market_size:
                            st.metric("CAGR", market_size["cagr"])
                    else:
                        st.write(market_size)
                else:
                    st.info("Nessun dato sulla dimensione del mercato disponibile")

            with tabs[2]:
                # Trend di mercato
                if "trends" in results_data and results_data["trends"]:
                    st.markdown("### Trend di Mercato")
                    for i, trend in enumerate(results_data["trends"]):
                        if isinstance(trend, dict) and "description" in trend:
                            st.markdown(f"**{i+1}.** {trend['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {trend}")
                        st.markdown("---")
                else:
                    st.info("Nessun trend di mercato disponibile")

            with tabs[3]:
                # Competitor
                if "competitors" in results_data and results_data["competitors"]:
                    st.markdown("### Competitor Principali")
                    for i, comp in enumerate(results_data["competitors"]):
                        if isinstance(comp, dict):
                            name = comp.get("name", f"Competitor {i+1}")
                            desc = comp.get("description", "")
                            with st.expander(name):
                                st.markdown(desc if desc else "Nessuna descrizione disponibile")
                        else:
                            st.markdown(f"**Competitor {i+1}:** {comp}")
                else:
                    st.info("Nessun dato sui competitor disponibile")

            with tabs[4]:
                # Opportunità
                if "opportunities" in results_data and results_data["opportunities"]:
                    st.markdown("### Opportunità di Mercato")
                    for i, opp in enumerate(results_data["opportunities"]):
                        if isinstance(opp, dict) and "description" in opp:
                            st.markdown(f"**{i+1}.** {opp['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {opp}")
                        st.markdown("---")
                else:
                    st.info("Nessuna opportunità di mercato disponibile")

            with tabs[5]:
                # Fonti
                if "sources" in results_data and results_data["sources"]:
                    st.markdown("### Fonti")
                    for i, source in enumerate(results_data["sources"]):
                        if isinstance(source, dict):
                            desc = source.get("description", f"Fonte {i+1}")
                            url = source.get("url", "")
                            if url:
                                st.markdown(f"**{i+1}.** [{desc}]({url})")
                            else:
                                st.markdown(f"**{i+1}.** {desc}")
                        else:
                            st.markdown(f"**{i+1}.** {source}")
                else:
                    st.info("Nessuna fonte disponibile")

        elif search_type == "competitor_analysis":
            # Visualizzazione per analisi competitiva
            tabs = st.tabs(["Panoramica", "Competitor", "Analisi SWOT", "Fonti"])

            with tabs[0]:
                # Panoramica generale
                if "raw_text" in results_data and results_data["raw_text"]:
                    st.markdown("### Sintesi dell'Analisi Competitiva")
                    raw_text = results_data["raw_text"]
                    st.markdown(raw_text[:500] + "..." if len(raw_text) > 500 else raw_text)
                    if len(raw_text) > 500:
                        with st.expander("Mostra testo completo"):
                            st.markdown(raw_text)

            with tabs[1]:
                # Competitor
                if "competitors" in results_data and results_data["competitors"]:
                    st.markdown("### Competitor Principali")
                    for i, comp in enumerate(results_data["competitors"]):
                        if isinstance(comp, dict):
                            name = comp.get("name", f"Competitor {i+1}")
                            desc = comp.get("description", "")
                            with st.expander(name):
                                st.markdown(desc if desc else "Nessuna descrizione disponibile")
                        else:
                            st.markdown(f"**Competitor {i+1}:** {comp}")
                else:
                    st.info("Nessun dato sui competitor disponibile")

            with tabs[2]:
                # Analisi SWOT
                if "swot" in results_data and results_data["swot"]:
                    swot = results_data["swot"]
                    st.markdown("### Analisi SWOT")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### Punti di Forza")
                        if "strengths" in swot and swot["strengths"]:
                            for s in swot["strengths"]:
                                if isinstance(s, dict) and "description" in s:
                                    st.markdown(f"- {s['description']}")
                                else:
                                    st.markdown(f"- {s}")
                        else:
                            st.info("Nessun punto di forza identificato")

                    with col2:
                        st.markdown("#### Punti Deboli")
                        if "weaknesses" in swot and swot["weaknesses"]:
                            for w in swot["weaknesses"]:
                                if isinstance(w, dict) and "description" in w:
                                    st.markdown(f"- {w['description']}")
                                else:
                                    st.markdown(f"- {w}")
                        else:
                            st.info("Nessun punto debole identificato")

                    col3, col4 = st.columns(2)
                    with col3:
                        st.markdown("#### Opportunità")
                        if "opportunities" in swot and swot["opportunities"]:
                            for o in swot["opportunities"]:
                                if isinstance(o, dict) and "description" in o:
                                    st.markdown(f"- {o['description']}")
                                else:
                                    st.markdown(f"- {o}")
                        else:
                            st.info("Nessuna opportunità identificata")

                    with col4:
                        st.markdown("#### Minacce")
                        if "threats" in swot and swot["threats"]:
                            for t in swot["threats"]:
                                if isinstance(t, dict) and "description" in t:
                                    st.markdown(f"- {t['description']}")
                                else:
                                    st.markdown(f"- {t}")
                        else:
                            st.info("Nessuna minaccia identificata")
                else:
                    st.info("Nessuna analisi SWOT disponibile")

            with tabs[3]:
                # Fonti
                if "sources" in results_data and results_data["sources"]:
                    st.markdown("### Fonti")
                    for i, source in enumerate(results_data["sources"]):
                        if isinstance(source, dict):
                            desc = source.get("description", f"Fonte {i+1}")
                            url = source.get("url", "")
                            if url:
                                st.markdown(f"**{i+1}.** [{desc}]({url})")
                            else:
                                st.markdown(f"**{i+1}.** {desc}")
                        else:
                            st.markdown(f"**{i+1}.** {source}")
                else:
                    st.info("Nessuna fonte disponibile")

        elif search_type == "trend_analysis":
            # Visualizzazione per analisi dei trend
            tabs = st.tabs(["Panoramica", "Trend", "Fonti"])

            with tabs[0]:
                # Panoramica generale
                if "raw_text" in results_data and results_data["raw_text"]:
                    st.markdown("### Sintesi dell'Analisi dei Trend")
                    raw_text = results_data["raw_text"]
                    st.markdown(raw_text[:500] + "..." if len(raw_text) > 500 else raw_text)
                    if len(raw_text) > 500:
                        with st.expander("Mostra testo completo"):
                            st.markdown(raw_text)

            with tabs[1]:
                # Trend
                if "trends" in results_data and results_data["trends"]:
                    st.markdown("### Trend Principali")
                    for i, trend in enumerate(results_data["trends"]):
                        if isinstance(trend, dict) and "description" in trend:
                            st.markdown(f"**{i+1}.** {trend['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {trend}")
                        st.markdown("---")
                else:
                    st.info("Nessun trend disponibile")

            with tabs[2]:
                # Fonti
                if "sources" in results_data and results_data["sources"]:
                    st.markdown("### Fonti")
                    for i, source in enumerate(results_data["sources"]):
                        if isinstance(source, dict):
                            desc = source.get("description", f"Fonte {i+1}")
                            url = source.get("url", "")
                            if url:
                                st.markdown(f"**{i+1}.** [{desc}]({url})")
                            else:
                                st.markdown(f"**{i+1}.** {desc}")
                        else:
                            st.markdown(f"**{i+1}.** {source}")
                else:
                    st.info("Nessuna fonte disponibile")

        elif search_type == "financial_analysis":
            # Visualizzazione per analisi finanziaria
            tabs = st.tabs(["Panoramica", "Struttura Costi", "Metriche", "Finanziamento", "Rischi", "Fonti"])

            with tabs[0]:
                # Panoramica generale
                if "raw_text" in results_data and results_data["raw_text"]:
                    st.markdown("### Sintesi dell'Analisi Finanziaria")
                    raw_text = results_data["raw_text"]
                    st.markdown(raw_text[:500] + "..." if len(raw_text) > 500 else raw_text)
                    if len(raw_text) > 500:
                        with st.expander("Mostra testo completo"):
                            st.markdown(raw_text)

            with tabs[1]:
                # Struttura dei costi
                if "costs" in results_data and results_data["costs"]:
                    st.markdown("### Struttura dei Costi")
                    for i, cost in enumerate(results_data["costs"]):
                        if isinstance(cost, dict) and "description" in cost:
                            st.markdown(f"**{i+1}.** {cost['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {cost}")
                        st.markdown("---")
                else:
                    st.info("Nessun dato sulla struttura dei costi disponibile")

            with tabs[2]:
                # Metriche finanziarie
                if "metrics" in results_data and results_data["metrics"]:
                    st.markdown("### Metriche Finanziarie")
                    for i, metric in enumerate(results_data["metrics"]):
                        if isinstance(metric, dict) and "description" in metric:
                            st.markdown(f"**{i+1}.** {metric['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {metric}")
                        st.markdown("---")
                else:
                    st.info("Nessuna metrica finanziaria disponibile")

            with tabs[3]:
                # Fonti di finanziamento
                if "funding" in results_data and results_data["funding"]:
                    st.markdown("### Fonti di Finanziamento")
                    for i, fund in enumerate(results_data["funding"]):
                        if isinstance(fund, dict) and "description" in fund:
                            st.markdown(f"**{i+1}.** {fund['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {fund}")
                        st.markdown("---")
                else:
                    st.info("Nessuna fonte di finanziamento disponibile")

            with tabs[4]:
                # Rischi finanziari
                if "risks" in results_data and results_data["risks"]:
                    st.markdown("### Rischi Finanziari")
                    for i, risk in enumerate(results_data["risks"]):
                        if isinstance(risk, dict) and "description" in risk:
                            st.markdown(f"**{i+1}.** {risk['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {risk}")
                        st.markdown("---")
                else:
                    st.info("Nessun rischio finanziario disponibile")

            with tabs[5]:
                # Fonti
                if "sources" in results_data and results_data["sources"]:
                    st.markdown("### Fonti")
                    for i, source in enumerate(results_data["sources"]):
                        if isinstance(source, dict):
                            desc = source.get("description", f"Fonte {i+1}")
                            url = source.get("url", "")
                            if url:
                                st.markdown(f"**{i+1}.** [{desc}]({url})")
                            else:
                                st.markdown(f"**{i+1}.** {desc}")
                        else:
                            st.markdown(f"**{i+1}.** {source}")
                else:
                    st.info("Nessuna fonte disponibile")

        elif search_type == "marketing_analysis":
            # Visualizzazione per analisi di marketing
            tabs = st.tabs(["Panoramica", "Canali", "Pricing", "Posizionamento", "Acquisizione", "Budget", "Fonti"])

            with tabs[0]:
                # Panoramica generale
                if "raw_text" in results_data and results_data["raw_text"]:
                    st.markdown("### Sintesi della Strategia di Marketing")
                    raw_text = results_data["raw_text"]
                    st.markdown(raw_text[:500] + "..." if len(raw_text) > 500 else raw_text)
                    if len(raw_text) > 500:
                        with st.expander("Mostra testo completo"):
                            st.markdown(raw_text)

            with tabs[1]:
                # Canali di marketing
                if "channels" in results_data and results_data["channels"]:
                    st.markdown("### Canali di Marketing")
                    for i, channel in enumerate(results_data["channels"]):
                        if isinstance(channel, dict) and "description" in channel:
                            st.markdown(f"**{i+1}.** {channel['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {channel}")
                        st.markdown("---")
                else:
                    st.info("Nessun canale di marketing disponibile")

            with tabs[2]:
                # Strategie di pricing
                if "pricing" in results_data and results_data["pricing"]:
                    st.markdown("### Strategie di Pricing")
                    for i, price in enumerate(results_data["pricing"]):
                        if isinstance(price, dict) and "description" in price:
                            st.markdown(f"**{i+1}.** {price['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {price}")
                        st.markdown("---")
                else:
                    st.info("Nessuna strategia di pricing disponibile")

            with tabs[3]:
                # Posizionamento
                if "positioning" in results_data and results_data["positioning"]:
                    st.markdown("### Posizionamento")
                    for i, pos in enumerate(results_data["positioning"]):
                        if isinstance(pos, dict) and "description" in pos:
                            st.markdown(f"**{i+1}.** {pos['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {pos}")
                        st.markdown("---")
                else:
                    st.info("Nessuna strategia di posizionamento disponibile")

            with tabs[4]:
                # Acquisizione clienti
                if "acquisition" in results_data and results_data["acquisition"]:
                    st.markdown("### Tattiche di Acquisizione Clienti")
                    for i, acq in enumerate(results_data["acquisition"]):
                        if isinstance(acq, dict) and "description" in acq:
                            st.markdown(f"**{i+1}.** {acq['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {acq}")
                        st.markdown("---")
                else:
                    st.info("Nessuna tattica di acquisizione clienti disponibile")

            with tabs[5]:
                # Budget di marketing
                if "budget" in results_data and results_data["budget"]:
                    st.markdown("### Budget di Marketing")
                    budget = results_data["budget"]

                    if "percentage" in budget:
                        st.metric("Percentuale sul fatturato", budget["percentage"])

                    if "value" in budget:
                        st.metric("Valore stimato", budget["value"])

                    if "description" in budget:
                        st.markdown(budget["description"])
                else:
                    st.info("Nessuna informazione sul budget di marketing disponibile")

            with tabs[6]:
                # Fonti
                if "sources" in results_data and results_data["sources"]:
                    st.markdown("### Fonti")
                    for i, source in enumerate(results_data["sources"]):
                        if isinstance(source, dict):
                            desc = source.get("description", f"Fonte {i+1}")
                            url = source.get("url", "")
                            if url:
                                st.markdown(f"**{i+1}.** [{desc}]({url})")
                            else:
                                st.markdown(f"**{i+1}.** {desc}")
                        else:
                            st.markdown(f"**{i+1}.** {source}")
                else:
                    st.info("Nessuna fonte disponibile")

        elif search_type == "operational_analysis":
            # Visualizzazione per analisi operativa
            tabs = st.tabs(["Panoramica", "Struttura", "Processi", "Risorse", "Partner", "Tecnologie", "Fonti"])

            with tabs[0]:
                # Panoramica generale
                if "raw_text" in results_data and results_data["raw_text"]:
                    st.markdown("### Sintesi del Piano Operativo")
                    raw_text = results_data["raw_text"]
                    st.markdown(raw_text[:500] + "..." if len(raw_text) > 500 else raw_text)
                    if len(raw_text) > 500:
                        with st.expander("Mostra testo completo"):
                            st.markdown(raw_text)

            with tabs[1]:
                # Struttura organizzativa
                if "structure" in results_data and results_data["structure"]:
                    st.markdown("### Struttura Organizzativa")
                    for i, struct in enumerate(results_data["structure"]):
                        if isinstance(struct, dict) and "description" in struct:
                            st.markdown(f"**{i+1}.** {struct['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {struct}")
                        st.markdown("---")
                else:
                    st.info("Nessuna informazione sulla struttura organizzativa disponibile")

            with tabs[2]:
                # Processi operativi
                if "processes" in results_data and results_data["processes"]:
                    st.markdown("### Processi Operativi")
                    for i, proc in enumerate(results_data["processes"]):
                        if isinstance(proc, dict) and "description" in proc:
                            st.markdown(f"**{i+1}.** {proc['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {proc}")
                        st.markdown("---")
                else:
                    st.info("Nessuna informazione sui processi operativi disponibile")

            with tabs[3]:
                # Risorse necessarie
                if "resources" in results_data and results_data["resources"]:
                    st.markdown("### Risorse Necessarie")
                    for i, res in enumerate(results_data["resources"]):
                        if isinstance(res, dict) and "description" in res:
                            st.markdown(f"**{i+1}.** {res['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {res}")
                        st.markdown("---")
                else:
                    st.info("Nessuna informazione sulle risorse necessarie disponibile")

            with tabs[4]:
                # Partner e fornitori
                if "partners" in results_data and results_data["partners"]:
                    st.markdown("### Partner e Fornitori")
                    for i, partner in enumerate(results_data["partners"]):
                        if isinstance(partner, dict) and "description" in partner:
                            st.markdown(f"**{i+1}.** {partner['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {partner}")
                        st.markdown("---")
                else:
                    st.info("Nessuna informazione su partner e fornitori disponibile")

            with tabs[5]:
                # Tecnologie
                if "technologies" in results_data and results_data["technologies"]:
                    st.markdown("### Tecnologie e Sistemi")
                    for i, tech in enumerate(results_data["technologies"]):
                        if isinstance(tech, dict) and "description" in tech:
                            st.markdown(f"**{i+1}.** {tech['description']}")
                        else:
                            st.markdown(f"**{i+1}.** {tech}")
                        st.markdown("---")
                else:
                    st.info("Nessuna informazione sulle tecnologie disponibile")

            with tabs[6]:
                # Fonti
                if "sources" in results_data and results_data["sources"]:
                    st.markdown("### Fonti")
                    for i, source in enumerate(results_data["sources"]):
                        if isinstance(source, dict):
                            desc = source.get("description", f"Fonte {i+1}")
                            url = source.get("url", "")
                            if url:
                                st.markdown(f"**{i+1}.** [{desc}]({url})")
                            else:
                                st.markdown(f"**{i+1}.** {desc}")
                        else:
                            st.markdown(f"**{i+1}.** {source}")
                else:
                    st.info("Nessuna fonte disponibile")

        elif search_type == "swot_analysis":
            # Visualizzazione per analisi SWOT
            if "raw_text" in results_data and results_data["raw_text"]:
                raw_text = results_data["raw_text"]

                # Estrai le sezioni SWOT dal testo
                import re
                strengths = []
                weaknesses = []
                opportunities = []
                threats = []

                # Cerca punti di forza
                strengths_section = re.search(r"(?:punti\s+di\s+forza|strengths|forza).*?(?=\n\n|\n#|debol|weakn|\Z)",
                                            raw_text, re.IGNORECASE | re.DOTALL)
                if strengths_section:
                    strength_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", strengths_section.group(0))
                    strengths = [item.strip() for item in strength_items if len(item.strip()) > 5]

                # Cerca debolezze
                weaknesses_section = re.search(r"(?:punti\s+deboli|debolezze|weaknesses).*?(?=\n\n|\n#|opport|\Z)",
                                             raw_text, re.IGNORECASE | re.DOTALL)
                if weaknesses_section:
                    weakness_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", weaknesses_section.group(0))
                    weaknesses = [item.strip() for item in weakness_items if len(item.strip()) > 5]

                # Cerca opportunità
                opportunities_section = re.search(r"(?:opportunità|opportunita|opportunities).*?(?=\n\n|\n#|minac|threat|\Z)",
                                                raw_text, re.IGNORECASE | re.DOTALL)
                if opportunities_section:
                    opportunity_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", opportunities_section.group(0))
                    opportunities = [item.strip() for item in opportunity_items if len(item.strip()) > 5]

                # Cerca minacce
                threats_section = re.search(r"(?:minacce|threats|rischi).*?(?=\n\n|\n#|\Z)",
                                          raw_text, re.IGNORECASE | re.DOTALL)
                if threats_section:
                    threat_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", threats_section.group(0))
                    threats = [item.strip() for item in threat_items if len(item.strip()) > 5]

                # Visualizza la matrice SWOT con un layout migliorato
                st.markdown("## 📊 Analisi SWOT")

                # Usa un layout a griglia per la matrice SWOT
                swot_container = st.container()
                with swot_container:
                    # Crea una griglia 2x2 con colori diversi
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("### 💪 Punti di Forza (Strengths)")
                        strengths_container = st.container(border=True)
                        with strengths_container:
                            if strengths:
                                for i, s in enumerate(strengths):
                                    st.markdown(f"**S{i+1}:** {s}")
                            else:
                                st.info("Nessun punto di forza identificato")

                    with col2:
                        st.markdown("### 🔄 Punti Deboli (Weaknesses)")
                        weaknesses_container = st.container(border=True)
                        with weaknesses_container:
                            if weaknesses:
                                for i, w in enumerate(weaknesses):
                                    st.markdown(f"**W{i+1}:** {w}")
                            else:
                                st.info("Nessun punto debole identificato")

                    col3, col4 = st.columns(2)

                    with col3:
                        st.markdown("### 🚀 Opportunità (Opportunities)")
                        opportunities_container = st.container(border=True)
                        with opportunities_container:
                            if opportunities:
                                for i, o in enumerate(opportunities):
                                    st.markdown(f"**O{i+1}:** {o}")
                            else:
                                st.info("Nessuna opportunità identificata")

                    with col4:
                        st.markdown("### ⚠️ Minacce (Threats)")
                        threats_container = st.container(border=True)
                        with threats_container:
                            if threats:
                                for i, t in enumerate(threats):
                                    st.markdown(f"**T{i+1}:** {t}")
                            else:
                                st.info("Nessuna minaccia identificata")

                # Mostra il testo completo in un expander
                with st.expander("Mostra analisi SWOT completa"):
                    st.markdown(raw_text)

                # Estrai fonti se presenti
                sources = []
                sources_section = re.search(r"(?:fonti|bibliografia|references|sources).*?(?=\n\n|\n#|\Z)",
                                          raw_text, re.IGNORECASE | re.DOTALL)
                if sources_section:
                    source_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", sources_section.group(0))
                    sources = [item.strip() for item in source_items if len(item.strip()) > 5]

                if sources:
                    st.markdown("### Fonti")
                    for i, source in enumerate(sources):
                        # Cerca URL nella fonte
                        url_match = re.search(r"https?://[^\s]+", source)
                        url = url_match.group(0) if url_match else ""

                        if url:
                            st.markdown(f"**{i+1}.** [{source}]({url})")
                        else:
                            st.markdown(f"**{i+1}.** {source}")
            else:
                st.warning("Nessun dato di analisi SWOT disponibile")

        else:
            # Visualizzazione generica per altri tipi di ricerca
            if "extracted_text" in results_data:
                st.markdown("### Risultati della Ricerca")
                st.markdown(results_data["extracted_text"])
            elif "choices" in results_data and len(results_data["choices"]) > 0:
                st.markdown("### Risultati della Ricerca")
                st.markdown(results_data["choices"][0]["message"]["content"])
            elif "raw_text" in results_data:
                st.markdown("### Risultati della Ricerca")
                st.markdown(results_data["raw_text"])
            else:
                # Fallback: mostra i dati grezzi in formato JSON
                with st.expander("Dati Grezzi"):
                    st.json(results_data)

        # Pulsante per utilizzare i risultati nella generazione
        if st.button("📝 Utilizza questi risultati nella generazione"):
            st.session_state.state_dict['perplexity_results'] = results_data
            st.session_state.state_dict['online_search_enabled'] = True
            st.success("✅ I risultati della ricerca saranno utilizzati nella prossima generazione!")

        # Pulsante per cancellare i risultati
        if st.button("🗑️ Cancella risultati"):
            if 'last_search_results' in st.session_state:
                del st.session_state.last_search_results
            if 'perplexity_results' in st.session_state.state_dict:
                del st.session_state.state_dict['perplexity_results']
            st.rerun()

# Aggiungi una tab per la gestione dei dati finanziari
if not is_initial_screen:
    # Verifica se siamo in modalità semplificata
    if 'simplified_mode' in st.session_state and st.session_state.simplified_mode and simplified_modules_available:
        # In modalità semplificata, mostra direttamente l'editor senza tab
        with st.container(border=True):
            # Mostra istruzioni contestuali in base alla sezione corrente
            section_instructions = {
                "initial_planning": "Pianifica la struttura del tuo business plan",
                "executive_summary": "Riassumi i punti chiave del tuo business plan",
                "company_description": "Descrivi la tua azienda, la sua missione e visione",
                "products_and_services": "Descrivi i prodotti o servizi offerti",
                "market_analysis": "Analizza il mercato di riferimento",
                "competitor_analysis": "Identifica e analizza i principali concorrenti",
                "marketing_strategy": "Definisci la strategia di marketing",
                "operational_plan": "Descrivi come opererà l'azienda",
                "organization_and_management": "Descrivi la struttura organizzativa",
                "risk_analysis": "Identifica e analizza i potenziali rischi",
                "financial_plan": "Presenta le proiezioni finanziarie",
                "human_review": "Rivedi il business plan completo",
                "document_generation": "Genera il documento finale"
            }

            current_instruction = section_instructions.get(
                st.session_state.current_node,
                "Compila questa sezione del business plan"
            )

            # Mostra le istruzioni
            st.caption(current_instruction)

            # Area di output semplificata
            output_area = st.text_area(
                "",  # Rimuovi l'etichetta
                value=st.session_state.current_output,
                height=350,
                key=f"output_{st.session_state.current_node}",
                placeholder="Il contenuto generato apparirà qui..."
            )

            # Pulsanti di azione semplificati
            col1, col2 = st.columns(2)

            with col1:
                # Bottone per generare contenuto
                generate_btn = st.button(
                    "✨ Genera Contenuto",
                    key="generate",
                    use_container_width=True,
                    type="primary"
                )

            with col2:
                # Bottone per salvare modifiche
                save_btn = st.button(
                    "💾 Salva Modifiche",
                    key="save",
                    use_container_width=True
                )

            # Logica per la generazione del contenuto
            if generate_btn:
                # Verifica se è stato raggiunto il limite di generazione
                gen_count = st.session_state.state_dict.get('generation_count', 0)
                max_gen = st.session_state.state_dict.get('max_generations', 30)

                if gen_count >= max_gen:
                    st.error(f"⛔ Hai raggiunto il limite massimo di {max_gen} messaggi. Non è possibile generare ulteriore contenuto.")
                else:
                    with st.spinner("Generazione in corso..."):
                        # Qui andrebbe la logica di generazione del contenuto
                        # Per ora usiamo un placeholder
                        current_node_name = st.session_state.current_node.replace('_', ' ').title()
                        st.session_state.current_output = f"Contenuto di esempio per la sezione {current_node_name}."
                        st.rerun()

            # Logica per il salvataggio delle modifiche
            if save_btn and output_area:
                st.session_state.current_output = output_area

                # Aggiorna la cronologia
                history_updated = False
                for i, (node_name, input_state, _) in enumerate(st.session_state.history):
                    if node_name == st.session_state.current_node:
                        st.session_state.history[i] = (node_name, input_state, output_area)
                        history_updated = True
                        break

                if not history_updated:
                    st.session_state.history.append((st.session_state.current_node, {}, output_area))

                st.success("✅ Modifiche salvate con successo!")

        # Se siamo nella sezione finanziaria, mostra la tab finanziaria semplificata
        if st.session_state.current_node == "financial_plan":
            st.markdown("---")
            add_simplified_financial_tab()
    else:
        # In modalità standard, mostra le tab complete
        tabs = st.tabs([
            "📝 Editor",
            "💰 Finanza",
            "🔍 Ricerca",
            "⚙️ Impostazioni"
        ])

    # Tab Editor
    if not ('simplified_mode' in st.session_state and st.session_state.simplified_mode and simplified_modules_available):
        with tabs[0]:
            # Contenuto della sezione
            with st.container(border=True):
                # Mostra istruzioni contestuali in base alla sezione corrente
                section_instructions = {
                    "initial_planning": "Pianifica la struttura del tuo business plan",
                    "executive_summary": "Riassumi i punti chiave del tuo business plan",
                    "company_description": "Descrivi la tua azienda, la sua missione e visione",
                    "products_and_services": "Descrivi i prodotti o servizi offerti",
                    "market_analysis": "Analizza il mercato di riferimento",
                    "competitor_analysis": "Identifica e analizza i principali concorrenti",
                    "marketing_strategy": "Definisci la strategia di marketing",
                    "operational_plan": "Descrivi come opererà l'azienda",
                    "organization_and_management": "Descrivi la struttura organizzativa",
                    "risk_analysis": "Identifica e analizza i potenziali rischi",
                    "financial_plan": "Presenta le proiezioni finanziarie",
                    "human_review": "Rivedi il business plan completo",
                    "document_generation": "Genera il documento finale"
                }

                current_instruction = section_instructions.get(
                    st.session_state.current_node,
                    "Compila questa sezione del business plan"
                )

            # Mostra il titolo e le istruzioni
            st.subheader("📝 Contenuto della Sezione")
            st.caption(current_instruction)

            # Area di output con stile migliorato
            output_area = st.text_area(
                "",  # Rimuovi l'etichetta per semplificare
                value=st.session_state.current_output,
                height=350,
                key=f"output_{st.session_state.current_node}",
                placeholder="Il contenuto generato apparirà qui..."
            )

            # Pulsanti di azione
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                # Bottone per generare contenuto (metodo standard)
                generate_btn = st.button(
                    "✨ Genera Contenuto",
                    key="generate",
                    use_container_width=True,
                    type="primary"
                )

            with col2:
                # Bottone per generare contenuto (metodo alternativo)
                generate_alt_btn = st.button(
                    "🔄 Genera Alternativo",
                    key="generate_alt",
                    use_container_width=True,
                    help="Usa un metodo alternativo per generare la sezione"
                )

            with col3:
                # Bottone per modificare il contenuto esistente
                edit_btn = st.button(
                    "✏️ Modifica Contenuto",
                    key="edit",
                    use_container_width=True,
                    disabled=not st.session_state.current_output  # Disabilitato se non c'è contenuto
                )

            with col4:
                # Bottone per aggiornare con le impostazioni correnti
                update_btn = st.button(
                    "🔄 Aggiorna",
                    key="update",
                    use_container_width=True,
                    disabled=not st.session_state.current_output,
                    help="Aggiorna il contenuto con le impostazioni correnti"
                )

            # Controlli per lunghezza e tono
            st.markdown("### 🎯 Impostazioni di Generazione")
            length_col, tone_col = st.columns(2)

            with length_col:
                # Slider per la lunghezza
                st.session_state.length = st.select_slider(
                    "Lunghezza",
                    options=["Breve", "Medio", "Lungo"],
                    value=st.session_state.get("length", "Medio"),
                    help="Seleziona la lunghezza del contenuto: Breve (300 parole), Medio (800), Lungo (2000)"
                )

            with tone_col:
                # Dropdown per il tono
                st.session_state.tone = st.selectbox(
                    "Tono",
                    ["Formale", "Accademico", "Creativo", "Tecnico"],
                    index=["Formale", "Accademico", "Creativo", "Tecnico"].index(
                        st.session_state.get("tone", "Formale")
                    ) if st.session_state.get("tone") in ["Formale", "Accademico", "Creativo", "Tecnico"] else 0,
                    help="Seleziona il tono del contenuto: Formale, Accademico, Creativo o Tecnico"
                )

            # Gestione della generazione del contenuto con metodo standard
            if generate_btn:
                # Verifica se è stato raggiunto il limite di generazione
                gen_count = st.session_state.state_dict.get('generation_count', 0)
                max_gen = st.session_state.state_dict.get('max_generations', 30)

                if gen_count >= max_gen:
                    st.error(f"⛔ Hai raggiunto il limite massimo di {max_gen} messaggi. Non è possibile generare ulteriore contenuto.")
                    # Suggerimento per l'utente
                    st.info("Puoi modificare il contenuto esistente, ma non puoi generare nuove sezioni.")
                else:
                    current_node_name = st.session_state.current_node

                    # Gestione speciale per "descrizione_dell'azienda"
                    if current_node_name == "descrizione_dell'azienda":
                        current_node_name = "company_description"
                        st.session_state.current_node = current_node_name

                    # Log per debug
                    print(f"Pulsante Genera Contenuto premuto per il nodo: {current_node_name}")
                    print(f"Nodi disponibili: {list(node_functions.keys())}")

                    if current_node_name in node_functions:
                        # Log per debug
                        print(f"Funzione trovata per il nodo: {current_node_name}")

                        node_func = node_functions[current_node_name]

                        # Log per debug
                        print(f"Tipo della funzione: {type(node_func)}")

                        # Prepara lo stato per il nodo
                        current_state = st.session_state.state_dict.copy()
                        current_state['edit_instructions'] = None  # Assicura che non sia in modalità modifica
                        current_state['original_text'] = None
                        
                        # Aggiungi la lunghezza desiderata al current_state
                        if 'length' in st.session_state:
                            length_map = {
                                "Breve": "breve",
                                "Medio": "media",
                                "Lungo": "dettagliata"
                            }
                            current_state['length_type'] = length_map.get(st.session_state.length, "media")
                            print(f"Impostata lunghezza: {current_state['length_type']} da {st.session_state.length}")

                        # Log per debug
                        print(f"Stato preparato con chiavi: {list(current_state.keys())}")

                        # Aggiungi il contesto delle sezioni precedenti
                        previous_sections_context = ""
                        for node, _, output in st.session_state.history:
                            if node != current_node_name and output and isinstance(output, str) and not output.startswith("Errore"):
                                node_title = node.replace('_', ' ').title()
                                previous_sections_context += f"\n\n## {node_title}\n{output[:500]}...\n"

                        if previous_sections_context:
                            current_state['previous_sections'] = previous_sections_context
                            print(f"Aggiunto contesto delle sezioni precedenti: {len(previous_sections_context)} caratteri")

                        with st.spinner(f"Generazione della sezione '{current_node_name.replace('_', ' ').title()}' in corso..."):
                            try:
                                # Mostra un messaggio di debug
                                st.info(f"Generazione in corso per '{current_node_name}'... Questo potrebbe richiedere alcuni secondi.")

                                # Log per debug
                                print(f"Esecuzione della funzione per il nodo: {current_node_name}")

                                # Metodo standard: esegui il nodo
                                result = node_func(current_state)

                                # Log per debug
                                print(f"Risultato ottenuto di tipo: {type(result)}")
                                if isinstance(result, dict):
                                    print(f"Chiavi nel risultato: {list(result.keys())}")
                                    if 'messages' in result:
                                        print(f"Numero di messaggi: {len(result['messages'])}")

                                # Estrai l'output significativo
                                if isinstance(result, dict) and 'messages' in result and result['messages']:
                                    last_message = result['messages'][-1]
                                    if isinstance(last_message, dict) and 'content' in last_message:
                                        raw_output = last_message['content']
                                        print(f"Contenuto estratto dal messaggio (primi 100 caratteri): {raw_output[:100]}...")
                                    else:
                                        raw_output = str(last_message)
                                        print(f"Messaggio convertito in stringa (primi 100 caratteri): {raw_output[:100]}...")
                                else:
                                    raw_output = str(result)
                                    print(f"Risultato convertito in stringa (primi 100 caratteri): {raw_output[:100]}...")

                                # Log per debug
                                print(f"Generazione completata per {current_node_name}")

                                # Pulisci e salva l'output
                                clean_output = extract_pure_content(raw_output)
                                print(f"Output pulito (primi 100 caratteri): {clean_output[:100]}...")

                                st.session_state.current_output = clean_output
                                st.session_state.history.append((current_node_name, current_state, st.session_state.current_output))

                                # Incrementa il contatore di generazione
                                st.session_state.state_dict['generation_count'] = gen_count + 1

                                st.success(f"Sezione '{current_node_name.replace('_', ' ').title()}' generata con successo!")
                                st.rerun()
                            except Exception as e:
                                error_msg = f"Errore durante la generazione: {e}"
                                print(error_msg)
                                traceback.print_exc()  # Per debug

                                # Mostra un messaggio di errore più dettagliato
                                st.error(error_msg)
                                with st.expander("Dettagli dell'errore"):
                                    st.code(traceback.format_exc())
                    else:
                        error_msg = f"Funzione per '{current_node_name}' non trovata."
                        print(f"ERRORE: {error_msg}")
                        print(f"Nodi disponibili: {list(node_functions.keys())}")
                        st.warning(error_msg)

                        # Suggerisci possibili soluzioni
                        st.info("Prova a selezionare un'altra sezione dalla barra laterale o a utilizzare il pulsante di test nella scheda Debug.")

            # Gestione della generazione alternativa
            if generate_alt_btn:
                # Verifica se è stato raggiunto il limite di generazione
                gen_count = st.session_state.state_dict.get('generation_count', 0)
                max_gen = st.session_state.state_dict.get('max_generations', 30)

                if gen_count >= max_gen:
                    st.error(f"⛔ Hai raggiunto il limite massimo di {max_gen} messaggi. Non è possibile generare ulteriore contenuto.")
                    # Suggerimento per l'utente
                    st.info("Puoi modificare il contenuto esistente, ma non puoi generare nuove sezioni.")
                else:
                    current_node_name = st.session_state.current_node
                    section_name = current_node_name.replace('_', ' ').title()

                    with st.spinner(f"Generazione alternativa della sezione '{section_name}' in corso..."):
                        try:
                            # Mostra un messaggio di debug
                            st.info(f"Utilizzando il metodo alternativo per generare '{section_name}'...")

                            # Prepara lo stato per la generazione
                            current_state = st.session_state.state_dict.copy()
                            
                            # Mappa la lunghezza selezionata al conteggio parole
                            word_count = 800  # Default
                            if 'length' in st.session_state:
                                word_count_map = {
                                    "Breve": 300,
                                    "Medio": 800,
                                    "Lungo": 2000
                                }
                                word_count = word_count_map.get(st.session_state.length, 800)
                                print(f"Impostato conteggio parole: {word_count} da {st.session_state.length}")

                            # Crea un prompt personalizzato per la sezione
                            prompt = f"""
                            Sei un esperto consulente di business plan. Scrivi SOLO il testo completo e pronto da incollare della sezione '{section_name}' del business plan per l'azienda {current_state.get('company_name', 'Azienda')}.

                            NON includere meta-informazioni, intestazioni, ruoli, parentesi graffe, markdown, né alcuna spiegazione tecnica.
                            Il testo deve essere scorrevole, professionale, coerente e adatto a un documento finale.
                            Se la sezione è molto lunga, concludi la frase e non troncare a metà.
                            Se necessario, suddividi in paragrafi ma senza titoli o numerazioni.

                            Informazioni sull'azienda:
                            - Nome: {current_state.get('company_name', 'Azienda')}
                            - Settore: {current_state.get('business_sector', '')}
                            - Descrizione: {current_state.get('company_description', '')}
                            - Anno fondazione: {current_state.get('year_founded', '')}
                            - Dipendenti: {current_state.get('num_employees', '')}
                            - Prodotti/Servizi: {current_state.get('main_products', '')}
                            - Mercato target: {current_state.get('target_market', '')}
                            - Area geografica: {current_state.get('area', 'Italia')}

                            La risposta deve essere di circa {word_count} parole.
                            Scrivi in italiano con stile professionale e formale.
                            """

                            # Aggiungi istruzioni specifiche per sezione
                            if section_name.lower() in ["sommario esecutivo", "executive summary"]:
                                prompt += """
                                Per questa sezione di sommario esecutivo, includi:
                                - Breve descrizione dell'azienda e della sua missione
                                - Prodotti o servizi offerti
                                - Mercato target e opportunità di mercato
                                - Vantaggio competitivo
                                - Obiettivi finanziari principali
                                - Eventuali richieste di finanziamento
                                """
                            elif section_name.lower() in ["descrizione dell'azienda", "company description"]:
                                prompt += """
                                Per questa sezione di descrizione dell'azienda, includi:
                                - Storia e background dell'azienda
                                - Missione e visione
                                - Obiettivi a breve e lungo termine
                                - Struttura legale
                                - Localizzazione e infrastrutture
                                """
                            elif section_name.lower() in ["prodotti e servizi", "products and services"]:
                                prompt += """
                                Per questa sezione di prodotti e servizi, includi:
                                - Descrizione dettagliata dei prodotti/servizi
                                - Benefici e valore per i clienti
                                - Stato di sviluppo (esistente, in sviluppo)
                                - Proprietà intellettuale o brevetti
                                - Ricerca e sviluppo futuri
                                """
                            elif section_name.lower() in ["analisi di mercato", "market analysis"]:
                                prompt += """
                                Per questa sezione di analisi di mercato, includi:
                                - Dimensione attuale del mercato con dati numerici
                                - Tasso di crescita previsto (CAGR)
                                - Segmentazione del mercato
                                - Tendenze principali
                                - Opportunità e sfide
                                """
                            elif section_name.lower() in ["analisi competitiva", "competitor analysis"]:
                                prompt += """
                                Per questa sezione di analisi competitiva, includi:
                                - Panoramica dei principali concorrenti
                                - Punti di forza e debolezza dei concorrenti
                                - Posizionamento dell'azienda rispetto ai concorrenti
                                - Vantaggi competitivi dell'azienda
                                - Analisi SWOT sintetica
                                """

                            # Usa il modello OpenAI per generare il contenuto
                            from langchain_openai import ChatOpenAI
                            from langchain.prompts import ChatPromptTemplate

                            # Crea il modello
                            llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)

                            # Crea il prompt
                            prompt_template = ChatPromptTemplate.from_template(prompt)

                            # Genera il contenuto
                            response = llm.invoke(prompt_template.format())

                            # Estrai il testo
                            if hasattr(response, 'content'):
                                raw_output = response.content
                            else:
                                raw_output = str(response)

                            # Pulisci e salva l'output
                            st.session_state.current_output = extract_pure_content(raw_output)
                            st.session_state.history.append((current_node_name, current_state, st.session_state.current_output))

                            # Incrementa il contatore di generazione
                            st.session_state.state_dict['generation_count'] = gen_count + 1

                            st.success(f"Sezione '{section_name}' generata con successo usando il metodo alternativo!")
                            st.rerun()
                        except Exception as e:
                            error_msg = f"Errore durante la generazione alternativa: {e}"
                            print(error_msg)
                            traceback.print_exc()  # Per debug

                            # Mostra un messaggio di errore più dettagliato
                            st.error(error_msg)
                            with st.expander("Dettagli dell'errore"):
                                st.code(traceback.format_exc())

            # Gestione della modifica del contenuto
            if edit_btn and st.session_state.current_output:
                st.session_state.editing_mode = True
                st.session_state.edit_node = st.session_state.current_node

                # Mostra l'interfaccia di modifica
                with st.form(key="edit_form"):
                    st.subheader("✏️ Modifica Contenuto")

                    # Istruzioni per la modifica
                    edit_instructions = st.text_area(
                        "Istruzioni per la modifica",
                        placeholder="Descrivi come vuoi modificare il contenuto...",
                        height=100
                    )

                    # Pulsanti del form
                    edit_cols = st.columns(2)
                    with edit_cols[0]:
                        cancel_edit = st.form_submit_button("Annulla", use_container_width=True)

                    with edit_cols[1]:
                        apply_edit = st.form_submit_button("Applica Modifiche", use_container_width=True, type="primary")

                    if apply_edit and edit_instructions:
                        current_node_name = st.session_state.current_node
                        if current_node_name in node_functions:
                            # Verifica se è stato raggiunto il limite di generazione
                            gen_count = st.session_state.state_dict.get('generation_count', 0)
                            max_gen = st.session_state.state_dict.get('max_generations', 30)

                            # Le modifiche contano come mezzo messaggio
                            if gen_count >= max_gen - 0.5:
                                st.error(f"⛔ Hai raggiunto il limite massimo di {max_gen} messaggi. Non è possibile generare ulteriore contenuto.")
                                # Suggerimento per l'utente
                                st.info("Raggiunti i limiti di utilizzo. Contatta il supporto per aumentare il tuo piano.")
                            else:
                                node_func = node_functions[current_node_name]

                                # Prepara lo stato per la modifica
                                current_state = st.session_state.state_dict.copy()
                                current_state['edit_instructions'] = edit_instructions
                                current_state['original_text'] = st.session_state.current_output

                                with st.spinner(f"Applicazione modifiche in corso..."):
                                    try:
                                        # Esegui il nodo in modalità modifica
                                        result = node_func(current_state)

                                        # Estrai l'output significativo
                                        if isinstance(result, dict) and 'messages' in result and result['messages']:
                                            last_message = result['messages'][-1]
                                            if isinstance(last_message, dict) and 'content' in last_message:
                                                raw_output = last_message['content']
                                            else:
                                                raw_output = str(last_message)
                                        else:
                                            raw_output = str(result)

                                        # Pulisci e salva l'output
                                        st.session_state.current_output = extract_pure_content(raw_output)
                                        st.session_state.history.append((f"{current_node_name}_edit", current_state, st.session_state.current_output))

                                        # Incrementa il contatore di generazione (0.5 per le modifiche)
                                        st.session_state.state_dict['generation_count'] = gen_count + 0.5

                                        st.success("Modifiche applicate con successo!")
                                        st.session_state.editing_mode = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Errore durante la modifica: {e}")
                        else:
                            st.warning(f"Funzione per '{current_node_name}' non trovata.")

                    if cancel_edit:
                        st.session_state.editing_mode = False
                        st.rerun()

    # Tab Finanza
    if not ('simplified_mode' in st.session_state and st.session_state.simplified_mode and simplified_modules_available):
        with tabs[1]:
            # Mostra la tab finanziaria
            financial_tab.add_financial_tab_to_app()

        # Tab Ricerca
        with tabs[2]:
            # Sezione Ricerca Online
            with st.expander("🔍 Ricerca Online", expanded=True):
                st.caption("Trova informazioni aggiornate per il tuo business plan")

                if st.session_state.search_available:
                    # Contenuto della ricerca con miglioramenti UX
                    st.markdown("### 🎯 Seleziona il tipo di ricerca")

                    # Mappa per la conversione al tipo di ricerca
                    section_type_map = {
                        "Analisi di Mercato": "market_analysis",
                        "Analisi Competitiva": "competitor_analysis",
                        "Trend di Settore": "trend_analysis",
                        "Piano Finanziario": "financial_analysis",
                        "Piano di Marketing": "marketing_analysis",
                        "Analisi SWOT": "swot_analysis"
                    }

                    # Layout migliorato per la selezione
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        selected_section = st.selectbox(
                            "Tipo di Ricerca",
                            list(section_type_map.keys()),
                            index=0,
                            help="Seleziona il tipo di informazioni che vuoi cercare",
                            key="search_section_type"
                        )

                    with col2:
                        detailed_search = st.checkbox(
                            "🔍 Dettaglio",
                            value=True,
                            help="Cerca informazioni più approfondite (richiede più tempo)"
                        )

                    # Pulsante per eseguire la ricerca
                    if st.button("🔎 Esegui Ricerca", type="primary", use_container_width=True):
                        # Ottieni i dati necessari per la ricerca
                        company = st.session_state.state_dict.get('company_name', 'Azienda')
                        industry = st.session_state.state_dict.get('business_sector', 'Generico')
                        target = st.session_state.state_dict.get('target_market', 'Clienti generici')

                        # Crea un contesto per la ricerca
                        query_context = f"Azienda: {company}, Settore: {industry}, Target: {target}"

                        # Esegui la ricerca
                        with st.spinner(f"Ricerca in corso per {selected_section}..."):
                            # Aggiorna le opzioni di ricerca
                            st.session_state.search_options = {
                                "use_cache": True,
                                "detailed": detailed_search,
                                "search_type": section_type_map[selected_section]
                            }

                            run_online_search(selected_section, query_context)

                        # Forza il refresh della pagina per mostrare i risultati
                        st.rerun()

                    # Mostra suggerimenti contestuali
                    st.markdown("### 💡 Suggerimenti per la Ricerca")
                    st.markdown(f"Per la sezione '{selected_section}':")

                    # Suggerimenti specifici per tipo di ricerca
                    if selected_section == "Analisi di Mercato":
                        st.markdown("- Cerca dati di mercato recenti (ultimi 12 mesi)")
                        st.markdown("- Includi dimensioni del mercato e tasso di crescita")
                        st.markdown("- Cerca opportunità specifiche per il tuo settore")
                    elif selected_section == "Analisi Competitiva":
                        st.markdown("- Cerca i principali concorrenti nel tuo settore")
                        st.markdown("- Analizza i punti di forza e debolezza dei concorrenti")
                        st.markdown("- Identifica vantaggi competitivi per la tua azienda")
                    elif selected_section == "Trend di Settore":
                        st.markdown("- Cerca trend emergenti nel tuo settore")
                        st.markdown("- Analizza l'impatto dei trend sulla tua azienda")
                        st.markdown("- Identifica opportunità legate ai trend")
                    elif selected_section == "Piano Finanziario":
                        st.markdown("- Cerca dati finanziari di riferimento per il tuo settore")
                        st.markdown("- Analizza le metriche finanziarie chiave")
                        st.markdown("- Identifica fonti di finanziamento")
                    elif selected_section == "Piano di Marketing":
                        st.markdown("- Cerca strategie di marketing efficaci nel tuo settore")
                        st.markdown("- Analizza i canali di marketing più utilizzati")
                        st.markdown("- Identifica opportunità di posizionamento")
                    elif selected_section == "Analisi SWOT":
                        st.markdown("- Cerca analisi SWOT per aziende simili")
                        st.markdown("- Analizza i punti di forza e debolezza del settore")
                        st.markdown("- Identifica opportunità e minacce nel mercato")

                    # Mostra i risultati della ricerca
                    if 'last_search_results' in st.session_state and st.session_state.last_search_results:
                        st.markdown("### 📊 Risultati della Ricerca")
                        search_type = st.session_state.get('last_search_type', 'generic')

                        # Visualizzazione migliorata dei risultati
                        if search_type == "market_analysis":
                            # Visualizzazione per analisi di mercato
                            if "market_size" in st.session_state.last_search_results:
                                market_size = st.session_state.last_search_results["market_size"]
                                st.markdown("#### Dimensione del Mercato")
                                if isinstance(market_size, dict):
                                    if "value" in market_size:
                                        st.metric("Valore", market_size["value"])
                                    if "cagr" in market_size:
                                        st.metric("CAGR", market_size["cagr"])
                                    if "description" in market_size:
                                        st.markdown(market_size["description"])
                                else:
                                    st.markdown(market_size)

                        elif search_type == "competitor_analysis":
                            # Visualizzazione per analisi competitiva
                            if "competitors" in st.session_state.last_search_results:
                                competitors = st.session_state.last_search_results["competitors"]
                                st.markdown("#### Competitor Principali")
                                for i, comp in enumerate(competitors):
                                    if isinstance(comp, dict):
                                        name = comp.get("name", f"Competitor {i+1}")
                                        desc = comp.get("description", "Nessuna descrizione disponibile")
                                        with st.expander(name):
                                            st.markdown(desc)
                                    else:
                                        st.markdown(f"**Competitor {i+1}:** {comp}")

                        elif search_type == "trend_analysis":
                            # Visualizzazione per analisi dei trend
                            if "trends" in st.session_state.last_search_results:
                                trends = st.session_state.last_search_results["trends"]
                                st.markdown("#### Trend Principali")
                                for i, trend in enumerate(trends):
                                    if isinstance(trend, dict) and "description" in trend:
                                        st.markdown(f"**Trend {i+1}:** {trend['description']}")
                                    else:
                                        st.markdown(f"**Trend {i+1}:** {trend}")

                        elif search_type == "financial_analysis":
                            # Visualizzazione per analisi finanziaria
                            if "metrics" in st.session_state.last_search_results:
                                metrics = st.session_state.last_search_results["metrics"]
                                st.markdown("#### Metriche Finanziarie")
                                for i, metric in enumerate(metrics):
                                    if isinstance(metric, dict) and "description" in metric:
                                        st.markdown(f"**{i+1}.** {metric['description']}")
                                    else:
                                        st.markdown(f"**{i+1}.** {metric}")

                        elif search_type == "marketing_analysis":
                            # Visualizzazione per analisi di marketing
                            if "channels" in st.session_state.last_search_results:
                                channels = st.session_state.last_search_results["channels"]
                                st.markdown("#### Canali di Marketing")
                                for i, channel in enumerate(channels):
                                    if isinstance(channel, dict) and "description" in channel:
                                        st.markdown(f"**{i+1}.** {channel['description']}")
                                    else:
                                        st.markdown(f"**{i+1}.** {channel}")

                        elif search_type == "swot_analysis":
                            # Visualizzazione per analisi SWOT
                            if "raw_text" in st.session_state.last_search_results:
                                raw_text = st.session_state.last_search_results["raw_text"]
                                st.markdown("#### Matrice SWOT")

                                # Estrai le sezioni SWOT dal testo
                                import re
                                strengths = []
                                weaknesses = []
                                opportunities = []
                                threats = []

                                # Cerca punti di forza
                                strengths_section = re.search(r"(?:punti\s+di\s+forza|strengths|forza).*?(?=\n\n|\n#|debol|\Z)",
                                                            raw_text, re.IGNORECASE | re.DOTALL)
                                if strengths_section:
                                    strength_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", strengths_section.group(0))
                                    strengths = [item.strip() for item in strength_items if len(item.strip()) > 5]

                                # Cerca debolezze
                                weaknesses_section = re.search(r"(?:punti\s+deboli|debolezze|weaknesses).*?(?=\n\n|\n#|opport|\Z)",
                                                             raw_text, re.IGNORECASE | re.DOTALL)
                                if weaknesses_section:
                                    weakness_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", weaknesses_section.group(0))
                                    weaknesses = [item.strip() for item in weakness_items if len(item.strip()) > 5]

                                # Cerca opportunità
                                opportunities_section = re.search(r"(?:opportunità|opportunita|opportunities).*?(?=\n\n|\n#|minac|\Z)",
                                                               raw_text, re.IGNORECASE | re.DOTALL)
                                if opportunities_section:
                                    opportunity_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", opportunities_section.group(0))
                                    opportunities = [item.strip() for item in opportunity_items if len(item.strip()) > 5]

                                # Cerca minacce
                                threats_section = re.search(r"(?:minacce|threats|rischi).*?(?=\n\n|\n#|\Z)",
                                                          raw_text, re.IGNORECASE | re.DOTALL)
                                if threats_section:
                                    threat_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", threats_section.group(0))
                                    threats = [item.strip() for item in threat_items if len(item.strip()) > 5]

                                # Visualizza la matrice SWOT con un layout migliorato
                                swot_container = st.container()
                                with swot_container:
                                    # Crea una griglia 2x2 con colori diversi
                                    col1, col2 = st.columns(2)

                                    with col1:
                                        st.markdown("### 💪 Punti di Forza (Strengths)")
                                        strengths_container = st.container(border=True)
                                        with strengths_container:
                                            if strengths:
                                                for i, s in enumerate(strengths):
                                                    st.markdown(f"**S{i+1}:** {s}")
                                            else:
                                                st.info("Nessun punto di forza identificato")

                                    with col2:
                                        st.markdown("### 🔄 Punti Deboli (Weaknesses)")
                                        weaknesses_container = st.container(border=True)
                                        with weaknesses_container:
                                            if weaknesses:
                                                for i, w in enumerate(weaknesses):
                                                    st.markdown(f"**W{i+1}:** {w}")
                                            else:
                                                st.info("Nessun punto debole identificato")

                                    col3, col4 = st.columns(2)

                                    with col3:
                                        st.markdown("### 🚀 Opportunità (Opportunities)")
                                        opportunities_container = st.container(border=True)
                                        with opportunities_container:
                                            if opportunities:
                                                for i, o in enumerate(opportunities):
                                                    st.markdown(f"**O{i+1}:** {o}")
                                            else:
                                                st.info("Nessuna opportunità identificata")

                                    with col4:
                                        st.markdown("### ⚠️ Minacce (Threats)")
                                        threats_container = st.container(border=True)
                                        with threats_container:
                                            if threats:
                                                for i, t in enumerate(threats):
                                                    st.markdown(f"**T{i+1}:** {t}")
                                            else:
                                                st.info("Nessuna minaccia identificata")

                                # Mostra il testo completo in un expander
                                with st.expander("Mostra analisi SWOT completa"):
                                    st.markdown(raw_text)

                        # Visualizzazione generica per altri tipi di ricerca
                        else:
                            if "extracted_text" in st.session_state.last_search_results:
                                st.markdown("#### Risultati della Ricerca")
                                st.markdown(st.session_state.last_search_results["extracted_text"])
                            elif "choices" in st.session_state.last_search_results and len(st.session_state.last_search_results["choices"]) > 0:
                                st.markdown("#### Risultati della Ricerca")
                                st.markdown(st.session_state.last_search_results["choices"][0]["message"]["content"])
                            elif "raw_text" in st.session_state.last_search_results:
                                st.markdown("#### Risultati della Ricerca")
                                st.markdown(st.session_state.last_search_results["raw_text"])
                            else:
                                # Fallback: mostra i dati grezzi in formato JSON
                                with st.expander("Dati Grezzi"):
                                    st.json(st.session_state.last_search_results)

                    # Pulsanti di azione migliorati
                    action_cols = st.columns([1, 1])
                    with action_cols[0]:
                        # Pulsante per utilizzare i risultati nella generazione
                        if st.button("📝 Utilizza questi risultati nella generazione", use_container_width=True):
                            st.session_state.state_dict['perplexity_results'] = st.session_state.last_search_results
                            st.session_state.state_dict['online_search_enabled'] = True
                            st.success("✅ I risultati della ricerca saranno utilizzati nella prossima generazione!")

                    with action_cols[1]:
                        # Pulsante per cancellare i risultati
                        if st.button("🗑️ Cancella risultati", use_container_width=True):
                            if 'last_search_results' in st.session_state:
                                del st.session_state.last_search_results
                            if 'perplexity_results' in st.session_state.state_dict:
                                del st.session_state.state_dict['perplexity_results']
                            st.rerun()
                else:
                    st.warning("La ricerca online non è disponibile. Verifica le impostazioni nella barra laterale.")

        # Tab Impostazioni
        with tabs[3]:
            # Impostazioni di Generazione
            with st.expander("🔧 Impostazioni Generazione", expanded=True):
                # Temperatura
                temperature = st.slider(
                    "Temperatura",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.state_dict.get("temperature", 0.7),
                    step=0.1,
                    help="Controlla la creatività del testo generato. Valori più alti = più creativo, valori più bassi = più deterministico."
                )

                # Aggiorna lo stato
                st.session_state.state_dict["temperature"] = temperature

                # Lunghezza massima
                max_tokens = st.slider(
                    "Lunghezza massima (tokens)",
                    min_value=500,
                    max_value=4000,
                    value=st.session_state.state_dict.get("max_tokens", 2000),
                    step=100,
                    help="Controlla la lunghezza massima del testo generato."
                )

                # Aggiorna lo stato
                st.session_state.state_dict["max_tokens"] = max_tokens
else:
    # Mostra un messaggio di benvenuto e istruzioni iniziali
    st.markdown("## Benvenuto nel Business Plan Builder")
    st.markdown("Seleziona una sezione dalla barra laterale per iniziare a creare il tuo business plan.")

    # Aggiungi una breve guida
    with st.expander("📖 Guida Rapida", expanded=True):
        st.markdown("""
        ### Come utilizzare questa applicazione:

        1. **Seleziona una sezione** dalla barra laterale a sinistra
        2. **Genera il contenuto** utilizzando i pulsanti nella scheda Editor
        3. **Modifica il contenuto** se necessario
        4. **Esporta il business plan** completo quando hai finito

        Puoi anche utilizzare la scheda Ricerca per trovare informazioni aggiornate per il tuo business plan.
        """)

    # Aggiungi un'immagine o logo
    st.image("https://img.freepik.com/free-vector/business-plan-concept-illustration_114360-1678.jpg", width=400)

    # Aggiungi un pulsante per iniziare
    if st.button("🚀 Inizia a Creare il Tuo Business Plan", type="primary", use_container_width=True):
        st.session_state.current_node = "executive_summary"
        st.rerun()

# Nessun tag di chiusura necessario qui

# --- Esportazione ---
if not is_initial_screen:
    # Raccogli tutti gli output generati dalla history
    full_plan_content = f"# {st.session_state.state_dict.get('document_title', 'Business Plan')}\n"
    full_plan_content += f"## Azienda: {st.session_state.state_dict.get('company_name', 'N/A')}\n"
    full_plan_content += f"Data: {st.session_state.state_dict.get('creation_date', 'N/A')}\nVersione: {st.session_state.state_dict.get('version', 'N/A')}\n\n"

    # Usa i nodi come ordine delle sezioni
    processed_nodes = set()
    for node_name in node_keys:
        # Trova l'ultimo output valido per questo nodo nella history
        last_output = ""
        for node, _, output in reversed(st.session_state.history):
            # Considera sia la generazione che la modifica
            if (node == node_name or node == f"{node_name}_edit") and output and isinstance(output, str) and not output.startswith("Errore"):
                last_output = output
                break

        if last_output:
            section_title = node_name.replace('_', ' ').title()
            full_plan_content += f"\n## {section_title}\n\n{last_output}\n\n"
            processed_nodes.add(node_name)

    # Container per l'esportazione
    with st.expander("💾 Esporta Business Plan", expanded=False):
        st.caption("Scarica il tuo business plan completo")

        # Crea una riga con colonne per i pulsanti di download
        col1, col2 = st.columns(2)

        with col1:
            # Pulsante Download TXT con stile migliorato
            st.download_button(
                label="📄 Scarica Piano Completo (.txt)",
                data=full_plan_content.encode('utf-8'),
                file_name=f"{st.session_state.state_dict.get('document_title', 'business_plan').replace(' ', '_')}.txt",
                mime="text/plain",
                help="Scarica il business plan completo in formato testo",
                use_container_width=True
            )

        with col2:
            # Placeholder per esportazione DOCX con stile migliorato
            st.button(
                "📊 Esporta in DOCX (Coming Soon)",
                disabled=True,
                help="Questa funzionalità sarà disponibile in una versione futura",
                use_container_width=True
            )

# --- Visualizzazione Stato e Cronologia (per Debug) ---
if not is_initial_screen:
    with st.expander("🔍 Debug", expanded=False):
        debug_tabs = st.tabs(["Stato", "Cronologia", "Diagnostica"])

        with debug_tabs[0]:
            st.caption("Stato interno dell'applicazione")
            st.json(st.session_state.state_dict)

        with debug_tabs[1]:
            st.caption("Ultimi eventi registrati")
            # Mostra gli ultimi 5 eventi
            if st.session_state.history:
                for i, (node, input_state, result) in enumerate(reversed(st.session_state.history[-5:])):
                    st.markdown(f"**Passo {len(st.session_state.history)-i}: {node}**")
                    st.text_area(
                        f"Output {len(st.session_state.history)-i}",
                        value=str(result)[:300] + ('...' if result and len(str(result)) > 300 else ''),
                        height=80,
                        disabled=True
                    )
            else:
                st.info("Nessun evento registrato")

        with debug_tabs[2]:
            st.caption("Strumenti di diagnostica")

            # Aggiungi un pulsante per testare la generazione diretta
            st.subheader("Test Generazione Sezioni")

            # Seleziona la sezione da testare
            test_sections = [
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

            test_section = st.selectbox(
                "Sezione da testare",
                test_sections,
                key="test_section"
            )

            # Pulsante per testare la generazione
            if st.button("Test Generazione Diretta", key="test_generation"):
                with st.spinner(f"Test di generazione per '{test_section}' in corso..."):
                    try:
                        # Gestione speciale per "Descrizione dell'Azienda"
                        if test_section == "Descrizione dell'Azienda":
                            node_name = "descrizione_dell_azienda"
                        else:
                            # Converti il nome della sezione in formato nodo
                            node_name = test_section.lower().replace(" ", "_").replace("'", "").replace("-", "_")

                        # Prepara lo stato per il test
                        test_state = st.session_state.state_dict.copy()

                        # Prova prima con direct_generator se disponibile
                        try:
                            # Verifica se il modulo direct_generator è disponibile
                            if 'direct_generator' in sys.modules:
                                # Verifica se la funzione esiste nel modulo direct_generator
                                italian_func_name = node_name
                                if hasattr(direct_generator, italian_func_name):
                                    # Ottieni la funzione dal modulo direct_generator
                                    italian_func = getattr(direct_generator, italian_func_name)
                                    # Esegui la funzione
                                    result = italian_func(test_state)
                                    st.info(f"Utilizzando la funzione '{italian_func_name}' dal modulo direct_generator")
                                else:
                                    # Usa la funzione generate_section_by_name
                                    result = direct_generator.generate_section_by_name(test_section, test_state)
                                    st.info(f"Utilizzando generate_section_by_name per '{test_section}'")
                            # Fallback al metodo originale
                            elif node_name in node_functions:
                                # Esegui la funzione del nodo
                                node_func = node_functions[node_name]
                                result = node_func(test_state)
                            else:
                                st.error(f"Funzione per '{node_name}' non trovata in node_functions")
                                st.code(f"Nodi disponibili: {list(node_functions.keys())}")
                                # Interrompi l'esecuzione qui
                                result = None
                        except Exception as e:
                            # Se fallisce con direct_generator, prova con node_functions
                            if node_name in node_functions:
                                st.warning(f"Fallback a node_functions per '{node_name}': {str(e)}")
                                # Esegui la funzione del nodo
                                node_func = node_functions[node_name]
                                result = node_func(test_state)
                            else:
                                st.error(f"Funzione per '{node_name}' non trovata in node_functions")
                                st.code(f"Nodi disponibili: {list(node_functions.keys())}")
                                # Interrompi l'esecuzione qui
                                result = None

                        # Verifica se abbiamo un risultato valido
                        if result is not None:
                            # Estrai il contenuto
                            if isinstance(result, dict) and 'messages' in result and result['messages']:
                                last_message = result['messages'][-1]
                                if isinstance(last_message, dict) and 'content' in last_message:
                                    content = last_message['content']
                                else:
                                    content = str(last_message)
                            else:
                                content = str(result)

                            # Pulisci il contenuto
                            clean_content = extract_pure_content(content)

                            # Mostra il risultato
                            st.success(f"Test completato con successo per '{test_section}'")
                            st.text_area("Contenuto generato", value=clean_content, height=300)

                            # Aggiungi dettagli tecnici
                            with st.expander("Dettagli tecnici"):
                                st.code(f"Nodo: {node_name}\nTipo risultato: {type(result)}\nLunghezza contenuto: {len(clean_content)} caratteri")
                        else:
                            # Mostra un messaggio di errore
                            st.error("Impossibile generare il contenuto. Verifica i messaggi di errore sopra.")
                    except Exception as e:
                        st.error(f"Errore durante il test: {str(e)}")
                        st.code(traceback.format_exc())

            # Mostra informazioni sul sistema
            st.subheader("Informazioni di Sistema")

            # Mostra le variabili d'ambiente (solo quelle sicure)
            safe_env_vars = {
                "PYTHONPATH": os.environ.get("PYTHONPATH", "Non impostato"),
                "STREAMLIT_SERVER_PORT": os.environ.get("STREAMLIT_SERVER_PORT", "Non impostato"),
                "GEMINI_API_KEY": "***" if os.environ.get("GEMINI_API_KEY") else "Non impostato"
            }

            st.json(safe_env_vars)

            # Mostra i nodi disponibili
            st.subheader("Nodi Disponibili")
            st.write(f"Nodo corrente: **{st.session_state.current_node}**")
            st.write("Tutti i nodi:")
            st.json(node_keys)

# --- Guida Rapida (se non nella sidebar) ---
# Potrebbe essere utile avere un link o un piccolo riassunto qui
# st.sidebar.markdown("[Link alla Guida Completa](#)") # Esempio

# --- Footer ---
st.markdown("---")

# Footer semplificato
st.markdown("""
<div style="text-align: center; margin-top: 1rem;">
    <p style="color: #6c757d; font-size: 0.9rem;">
        <strong>Business Plan Builder v1.0</strong>
    </p>
</div>
""", unsafe_allow_html=True)
