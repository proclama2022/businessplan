#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Definizione dello stato per il Business Plan Builder

Questo modulo definisce la struttura dello stato utilizzato da LangGraph per mantenere
il contesto attraverso l'intero documento, supportando documenti molto lunghi tramite
chunking gerarchico e persistenza dello stato.
"""

from typing import Annotated, List, Dict, Any, Optional, Set
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class DocumentChunk(TypedDict):
    """Rappresenta un blocco di testo con metadati per il chunking gerarchico"""
    id: str
    content: str
    section: str
    subsection: Optional[str]
    parent_id: Optional[str]
    level: int
    embeddings: Optional[List[float]]
    summary: Optional[str]

class FinancialData(TypedDict):
    """Dati finanziari strutturati per il business plan"""
    projections: Dict[str, Any]
    startup_costs: Dict[str, float]
    revenue_streams: List[Dict[str, Any]]
    cashflow: Dict[str, List[float]]
    break_even: Dict[str, Any]
    funding_requirements: Dict[str, Any]

class MarketData(TypedDict):
    """Dati di mercato per il business plan"""
    market_size: Dict[str, Any]
    target_segments: List[Dict[str, Any]]
    competitors: List[Dict[str, Any]]
    trends: List[Dict[str, Any]]
    opportunities: List[Dict[str, Any]]
    research_sources: List[Dict[str, str]]

class BusinessPlanState(TypedDict):
    """Stato completo del business plan con supporto per documenti lunghi"""
    # Cronologia dei messaggi per il contesto dell'agente
    messages: Annotated[List, add_messages]
    
    # Metadati del documento
    document_title: str
    company_name: str
    creation_date: str
    version: int
    
    # Struttura del documento
    outline: Dict[str, List[str]]
    
    # Contenuto in chunks
    document_chunks: Dict[str, DocumentChunk]
    active_chunk_id: Optional[str]
    
    # Sezioni completate e approvate
    completed_sections: Set[str]
    approved_sections: Set[str]
    
    # Dati strutturati
    financial_data: FinancialData
    market_data: MarketData
    
    # Stato dell'intervento umano
    human_feedback: Dict[str, Any]
    
    # Cache delle ricerche effettuate
    search_cache: Dict[str, Dict[str, Any]]

def initialize_state(document_title: str, company_name: str, creation_date: str, version: int = 1) -> BusinessPlanState:
    """Inizializza lo stato del business plan con valori predefiniti"""
    from config import Config
    
    # Inizializza lo stato con valori predefiniti
    state: BusinessPlanState = {
        "messages": [],
        "document_title": document_title,
        "company_name": company_name,
        "creation_date": creation_date,
        "version": version,
        "outline": Config.DEFAULT_BUSINESS_PLAN_STRUCTURE,
        "document_chunks": {},
        "active_chunk_id": None,
        "completed_sections": set(),
        "approved_sections": set(),
        "financial_data": {
            "projections": {},
            "startup_costs": {},
            "revenue_streams": [],
            "cashflow": {},
            "break_even": {},
            "funding_requirements": {}
        },
        "market_data": {
            "market_size": {},
            "target_segments": [],
            "competitors": [],
            "trends": [],
            "opportunities": [],
            "research_sources": []
        },
        "human_feedback": {},
        "search_cache": {}
    }
    
    return state