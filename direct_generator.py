#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wrapper per direct_section_generator.py
Questo modulo serve da ponte tra i nomi delle sezioni in italiano e le funzioni in inglese.
"""

import os
import sys
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
    try:
        # Prova l'importazione relativa prima (per l'uso come pacchetto)
        from .direct_section_generator import generate_section, extract_pure_content
    except ImportError:
        # Fallback all'importazione assoluta (per l'esecuzione diretta dello script)
        from direct_section_generator import generate_section, extract_pure_content
except ImportError as e:
    print(f"Errore nell'importare i moduli: {e}")
    sys.exit(1)

# Mappa dei nomi delle sezioni in italiano ai nomi delle funzioni in inglese
SECTION_NAME_MAP = {
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

def sommario_esecutivo(company_data: Dict[str, Any]) -> str:
    """
    Genera il sommario esecutivo del business plan.

    Args:
        company_data: Dati dell'azienda

    Returns:
        str: Testo generato
    """
    return generate_section("Sommario Esecutivo", company_data)

def descrizione_dellazienda(company_data: Dict[str, Any]) -> str:
    """
    Genera la descrizione dell'azienda del business plan.

    Args:
        company_data: Dati dell'azienda

    Returns:
        str: Testo generato
    """
    return generate_section("Descrizione dell'Azienda", company_data)

# Alias per gestire diverse varianti del nome della funzione
def descrizione_dell_azienda(company_data: Dict[str, Any]) -> str:
    """Alias per descrizione_dellazienda"""
    return descrizione_dellazienda(company_data)

def prodotti_e_servizi(company_data: Dict[str, Any]) -> str:
    """
    Genera la sezione prodotti e servizi del business plan.

    Args:
        company_data: Dati dell'azienda

    Returns:
        str: Testo generato
    """
    return generate_section("Prodotti e Servizi", company_data)

def analisi_di_mercato(company_data: Dict[str, Any]) -> str:
    """
    Genera l'analisi di mercato del business plan.

    Args:
        company_data: Dati dell'azienda

    Returns:
        str: Testo generato
    """
    return generate_section("Analisi di Mercato", company_data)

def analisi_competitiva(company_data: Dict[str, Any]) -> str:
    """
    Genera l'analisi competitiva del business plan.

    Args:
        company_data: Dati dell'azienda

    Returns:
        str: Testo generato
    """
    return generate_section("Analisi Competitiva", company_data)

def strategia_di_marketing(company_data: Dict[str, Any]) -> str:
    """
    Genera la strategia di marketing del business plan.

    Args:
        company_data: Dati dell'azienda

    Returns:
        str: Testo generato
    """
    return generate_section("Strategia di Marketing", company_data)

def piano_operativo(company_data: Dict[str, Any]) -> str:
    """
    Genera il piano operativo del business plan.

    Args:
        company_data: Dati dell'azienda

    Returns:
        str: Testo generato
    """
    return generate_section("Piano Operativo", company_data)

def organizzazione_e_team_di_gestione(company_data: Dict[str, Any]) -> str:
    """
    Genera la sezione organizzazione e team di gestione del business plan.

    Args:
        company_data: Dati dell'azienda

    Returns:
        str: Testo generato
    """
    return generate_section("Organizzazione e Team di Gestione", company_data)

def analisi_dei_rischi(company_data: Dict[str, Any]) -> str:
    """
    Genera l'analisi dei rischi del business plan.

    Args:
        company_data: Dati dell'azienda

    Returns:
        str: Testo generato
    """
    return generate_section("Analisi dei Rischi", company_data)

def piano_finanziario(company_data: Dict[str, Any]) -> str:
    """
    Genera il piano finanziario del business plan.

    Args:
        company_data: Dati dell'azienda

    Returns:
        str: Testo generato
    """
    return generate_section("Piano Finanziario", company_data)

def generate_section_by_name(section_name: str, company_data: Dict[str, Any]) -> str:
    """
    Genera una sezione del business plan in base al nome (supporta sia italiano che inglese).

    Args:
        section_name: Nome della sezione da generare (in italiano o inglese)
        company_data: Dati dell'azienda

    Returns:
        str: Testo generato
    """
    # Normalizza il nome della sezione (diverse varianti per gestire apostrofi e spazi)
    normalized_name = section_name.lower()

    # Prova diverse normalizzazioni per trovare una corrispondenza
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
    english_name = None
    for variant in variants:
        if variant in SECTION_NAME_MAP:
            english_name = SECTION_NAME_MAP[variant]
            break

    # Se non è stata trovata una corrispondenza, usa il nome normalizzato
    if english_name is None:
        # Normalizzazione standard come fallback
        english_name = normalized_name.replace(" ", "_").replace("'", "").replace("-", "_")

    # Verifica se la funzione del nodo esiste
    if english_name not in node_functions:
        return f"Errore: Funzione per '{section_name}' ('{english_name}') non trovata."

    # Usa la funzione di generazione esistente
    return generate_section(section_name, company_data)

# Esporta le funzioni con nomi italiani
__all__ = [
    'sommario_esecutivo',
    'descrizione_dellazienda',
    'descrizione_dell_azienda',  # Aggiungiamo la variante con underscore
    'prodotti_e_servizi',
    'analisi_di_mercato',
    'analisi_competitiva',
    'strategia_di_marketing',
    'piano_operativo',
    'organizzazione_e_team_di_gestione',
    'analisi_dei_rischi',
    'piano_finanziario',
    'generate_section_by_name'
]
