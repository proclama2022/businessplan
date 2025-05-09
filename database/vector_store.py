#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database vettoriale per il Business Plan Builder

Questo modulo implementa un database vettoriale utilizzando ChromaDB per memorizzare
e recuperare i chunk di testo in base alla loro similarità semantica, permettendo
ricerche efficienti all'interno di documenti molto lunghi.
"""

# Fix per SQLite su Streamlit Cloud
import sys
import importlib.util

if importlib.util.find_spec("pysqlite3") is not None:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3

import os
import json
import random
import numpy as np
from typing import List, Dict, Any, Optional, Union
import chromadb
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings
from config import Config

# Classe di embedding di fallback che genera vettori casuali
class MockEmbeddings(Embeddings):
    """Classe di embedding di fallback che genera vettori casuali quando OpenAI non è disponibile."""

    def __init__(self, dimension: int = 1536):
        """Inizializza l'embedding di fallback."""
        self.dimension = dimension
        print("ATTENZIONE: Usando MockEmbeddings invece di OpenAI. Funzionalità limitate!")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Genera embedding casuali per una lista di testi."""
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Genera un embedding casuale per una query."""
        # Usa il testo come seed per avere consistenza
        random.seed(hash(text) % 2**32)
        # Genera un vettore casuale normalizzato
        vector = [random.uniform(-1, 1) for _ in range(self.dimension)]
        # Normalizza il vettore
        norm = sum(x*x for x in vector) ** 0.5
        return [x/norm for x in vector]

class VectorDatabase:
    """Classe per la gestione del database vettoriale"""

    def __init__(self, persist_directory: Optional[str] = None, use_mock: bool = False):
        """Inizializza il database vettoriale

        Args:
            persist_directory: Directory dove salvare il database
            use_mock: Se True, usa MockEmbeddings invece di OpenAIEmbeddings
        """
        self.persist_directory = persist_directory or Config.VECTOR_DB_PATH
        self.using_mock = use_mock

        # Crea la directory se non esiste
        os.makedirs(self.persist_directory, exist_ok=True)

        # Inizializza il client ChromaDB (nuova API)
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # Inizializza il modello di embedding
        if use_mock:
            # Usa l'embedding di fallback
            print("Modalità fallback: usando MockEmbeddings")
            self.embeddings = MockEmbeddings(dimension=Config.EMBEDDING_DIMENSION)
        else:
            # Prova a usare OpenAI
            try:
                # Ottieni la chiave API OpenAI da variabili d'ambiente o secrets
                openai_api_key = os.environ.get("OPENAI_API_KEY")

                # Verifica se la chiave API è disponibile
                if not openai_api_key:
                    try:
                        import streamlit as st
                        # Accedi direttamente alla chiave API in secrets.toml
                        if "OPENAI_API_KEY" in st.secrets:
                            openai_api_key = st.secrets["OPENAI_API_KEY"]
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

                if not openai_api_key:
                    # Fallback a MockEmbeddings
                    print("Chiave OpenAI API non trovata, usando MockEmbeddings")
                    self.embeddings = MockEmbeddings(dimension=Config.EMBEDDING_DIMENSION)
                    self.using_mock = True
                else:
                    # Inizializza il modello di embedding con la chiave API da env/secrets
                    self.embeddings = OpenAIEmbeddings(
                        model=Config.EMBEDDING_MODEL,
                        openai_api_key=openai_api_key
                    )
            except Exception as e:
                print(f"Errore nell'inizializzazione di OpenAIEmbeddings: {e}")
                print("Fallback a MockEmbeddings")
                self.embeddings = MockEmbeddings(dimension=Config.EMBEDDING_DIMENSION)
                self.using_mock = True

        # Crea o recupera la collezione per i chunk del business plan
        self.collection = self.client.get_or_create_collection(
            name="business_plan_chunks",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunk(self, chunk: Dict[str, Any]) -> None:
        """Aggiunge un chunk al database vettoriale"""
        # Genera l'embedding per il contenuto del chunk
        if not chunk.get("embeddings"):
            chunk["embeddings"] = self.embeddings.embed_query(chunk["content"])

        # Prepara i metadati
        metadata = {
            "section": chunk["section"],
            "subsection": chunk["subsection"] or "",
            "level": chunk["level"],
            "parent_id": chunk["parent_id"] or "",
            "summary": chunk["summary"] or ""
        }

        # Aggiungi il chunk alla collezione
        self.collection.add(
            ids=[chunk["id"]],
            embeddings=[chunk["embeddings"]],
            metadatas=[metadata],
            documents=[chunk["content"]]
        )

    def add_chunks(self, chunks: Dict[str, Dict[str, Any]]) -> None:
        """Aggiunge più chunk al database vettoriale"""
        for chunk_id, chunk in chunks.items():
            self.add_chunk(chunk)

    def search_chunks(self, query: str, n_results: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Cerca chunk simili alla query nel database vettoriale"""
        # Genera l'embedding per la query
        query_embedding = self.embeddings.embed_query(query)

        # Esegui la ricerca
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )

        # Formatta i risultati
        formatted_results = []
        for i, (chunk_id, document, metadata, distance) in enumerate(zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            formatted_results.append({
                "id": chunk_id,
                "content": document,
                "section": metadata["section"],
                "subsection": metadata["subsection"],
                "level": metadata["level"],
                "parent_id": metadata["parent_id"],
                "summary": metadata["summary"],
                "similarity": 1.0 - distance  # Converte la distanza in similarità
            })

        return formatted_results

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Recupera un chunk specifico dal database vettoriale"""
        try:
            result = self.collection.get(ids=[chunk_id])

            if result["ids"] and len(result["ids"]) > 0:
                metadata = result["metadatas"][0]
                return {
                    "id": result["ids"][0],
                    "content": result["documents"][0],
                    "section": metadata["section"],
                    "subsection": metadata["subsection"],
                    "level": metadata["level"],
                    "parent_id": metadata["parent_id"],
                    "summary": metadata["summary"],
                    "embeddings": None  # Gli embedding non vengono restituiti da ChromaDB
                }
            return None
        except Exception as e:
            print(f"Errore nel recupero del chunk {chunk_id}: {e}")
            return None

    def get_chunks_by_section(self, section: str, subsection: Optional[str] = None) -> List[Dict[str, Any]]:
        """Recupera tutti i chunk di una specifica sezione/sottosezione"""
        filter_metadata = {"section": section}
        if subsection:
            filter_metadata["subsection"] = subsection

        try:
            results = self.collection.get(where=filter_metadata)

            formatted_results = []
            for i, (chunk_id, document, metadata) in enumerate(zip(
                results["ids"],
                results["documents"],
                results["metadatas"]
            )):
                formatted_results.append({
                    "id": chunk_id,
                    "content": document,
                    "section": metadata["section"],
                    "subsection": metadata["subsection"],
                    "level": metadata["level"],
                    "parent_id": metadata["parent_id"],
                    "summary": metadata["summary"],
                    "embeddings": None
                })

            return formatted_results
        except Exception as e:
            print(f"Errore nel recupero dei chunk per la sezione {section}: {e}")
            return []

    def update_chunk(self, chunk: Dict[str, Any]) -> None:
        """Aggiorna un chunk esistente nel database vettoriale"""
        # Rimuovi il chunk esistente
        self.collection.delete(ids=[chunk["id"]])

        # Aggiungi il chunk aggiornato
        self.add_chunk(chunk)

    def persist(self) -> None:
        """Salva il database su disco"""
        # ChromaDB salva automaticamente su disco, questa funzione è mantenuta per compatibilità
        pass

    def get_all_sections(self) -> List[str]:
        """Ottiene tutte le sezioni presenti nel database"""
        try:
            # Recupera tutti i metadati
            results = self.collection.get()
            
            # Estrai le sezioni uniche
            sections = set()
            for metadata in results["metadatas"]:
                sections.add(metadata["section"])
                
            return sorted(list(sections))
        except Exception as e:
            print(f"Errore nel recupero delle sezioni: {e}")
            return []

    def get_subsections(self, section: str) -> List[str]:
        """Ottiene tutte le sottosezioni di una sezione specifica"""
        try:
            # Recupera i metadati filtrati per sezione
            results = self.collection.get(where={"section": section})
            
            # Estrai le sottosezioni uniche
            subsections = set()
            for metadata in results["metadatas"]:
                if metadata["subsection"]:
                    subsections.add(metadata["subsection"])
                
            return sorted(list(subsections))
        except Exception as e:
            print(f"Errore nel recupero delle sottosezioni per la sezione {section}: {e}")
            return [] 