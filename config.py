#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configurazione del sistema Business Plan Builder

Questo modulo contiene tutte le configurazioni e costanti utilizzate dal sistema,
includendo dimensioni dei chunk, configurazioni delle API e altre impostazioni globali.
"""

class Config:
    """Classe di configurazione per il Business Plan Builder"""

    # Configurazioni generali
    APP_NAME = "Business Plan Builder"
    VERSION = "1.0.0"
    DEBUG = False

    # Configurazioni per il chunking
    MAX_CHUNK_SIZE = 1000  # Numero massimo di token per chunk
    MIN_CHUNK_SIZE = 100   # Numero minimo di token per chunk
    CHUNK_OVERLAP = 50     # Sovrapposizione tra chunk adiacenti
    MAX_SECTION_DEPTH = 5  # Profondità massima della gerarchia delle sezioni

    # Configurazioni per il database vettoriale
    VECTOR_DB_PATH = "./database/vector_db"
    EMBEDDING_MODEL = "text-embedding-ada-002"  # Modello OpenAI per embedding
    EMBEDDING_DIMENSION = 1536  # Dimensione degli embedding

    # Configurazioni per i modelli LLM
    DEFAULT_MODEL = "gpt-4o-mini"  # Modello predefinito (legacy)
    FALLBACK_MODEL = "gpt-3.5-turbo-16k"   # Modello di fallback (legacy)
    TEMPERATURE = 0.2  # Temperatura per la generazione di testo
    MAX_TOKENS = 4000  # Numero massimo di token per risposta

    # Configurazioni per Gemini (DISABILITATE)
    USE_GEMINI = False  # DEVE ESSERE FALSE
    GEMINI_MODEL = ""  # Non utilizzato
    GEMINI_API_TIMEOUT = 0  # Non utilizzato
    GEMINI_CACHE_ENABLED = False  # Non utilizzato
    GEMINI_CACHE_TTL = 0  # Non utilizzato

    # Configurazioni per la ricerca online
    PERPLEXITY_API_TIMEOUT = 60  # Timeout per le richieste API in secondi (aumentato)
    MAX_SEARCH_RESULTS = 5       # Numero massimo di risultati di ricerca
    SEARCH_CACHE_EXPIRY = 86400  # Scadenza della cache di ricerca in secondi (24 ore)
    PERPLEXITY_MODELS = {
        "pro": "sonar-pro",              # Modello più potente, per analisi approfondite
        "medium": "sonar-medium-online",  # Modello bilanciato, per ricerche standard
        "small": "sonar-small-online"     # Modello leggero, per ricerche rapide
    }

    # Abilita o disabilita la ricerca online
    # Può essere sovrascritto dal file .env
    ENABLE_ONLINE_RESEARCH = True

    # Configurazioni per la generazione di documenti
    DOCX_TEMPLATE_PATH = "./tools/templates/business_plan_template.docx"
    DEFAULT_FONT = "Calibri"
    DEFAULT_FONT_SIZE = 11

    # Struttura predefinita del business plan
    DEFAULT_BUSINESS_PLAN_STRUCTURE = {
        "Sommario Esecutivo": [
            "Panoramica dell'Azienda",
            "Prodotti e Servizi",
            "Obiettivi Aziendali",
            "Punti di Forza",
            "Richiesta Finanziaria"
        ],
        "Descrizione dell'Azienda": [
            "Missione e Visione",
            "Storia dell'Azienda",
            "Struttura Legale",
            "Localizzazione",
            "Team di Gestione"
        ],
        "Analisi di Mercato": [
            "Panoramica del Settore",
            "Tendenze di Mercato",
            "Dimensione del Mercato",
            "Segmentazione del Mercato",
            "Mercato Target"
        ],
        "Analisi Competitiva": [
            "Concorrenti Diretti",
            "Concorrenti Indiretti",
            "Vantaggi Competitivi",
            "Barriere all'Ingresso",
            "Analisi SWOT"
        ],
        "Prodotti e Servizi": [
            "Descrizione Dettagliata",
            "Ciclo di Vita del Prodotto",
            "Proprietà Intellettuale",
            "Ricerca e Sviluppo",
            "Fornitori e Catena di Approvvigionamento"
        ],
        "Piano di Marketing": [
            "Strategia di Marketing",
            "Strategia di Prezzo",
            "Strategia di Promozione",
            "Strategia di Distribuzione",
            "Piano di Vendita"
        ],
        "Piano Operativo": [
            "Processi Operativi",
            "Struttura Organizzativa",
            "Risorse Umane",
            "Attrezzature e Tecnologia",
            "Gestione della Qualità"
        ],
        "Piano Finanziario": [
            "Ipotesi Finanziarie",
            "Proiezioni di Vendita",
            "Conto Economico Previsionale",
            "Stato Patrimoniale Previsionale",
            "Flusso di Cassa Previsionale",
            "Analisi del Punto di Pareggio",
            "Richiesta di Finanziamento"
        ],
        "Piano di Implementazione": [
            "Milestone",
            "Tempistiche",
            "Gestione del Rischio"
        ],
        "Appendici": [
            "Documenti di Supporto",
            "Ricerche di Mercato",
            "Dettagli Finanziari",
            "Curriculum del Team"
        ]
    }

# Costanti globali
MAX_CHUNK_SIZE = Config.MAX_CHUNK_SIZE
MIN_CHUNK_SIZE = Config.MIN_CHUNK_SIZE
CHUNK_OVERLAP = Config.CHUNK_OVERLAP
DEFAULT_MODEL = Config.DEFAULT_MODEL
