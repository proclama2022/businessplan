#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema di chunking gerarchico per documenti lunghi

Questo modulo implementa strategie avanzate di chunking per suddividere documenti molto lunghi
in blocchi gerarchici, mantenendo la struttura e il contesto attraverso sezioni e sottosezioni.
È la chiave per gestire business plan fino a 20.000 parole.
"""

import re
import uuid
from typing import List, Dict, Tuple, Optional, Any
import tiktoken
from config import MAX_CHUNK_SIZE, MIN_CHUNK_SIZE, CHUNK_OVERLAP

# Crea un'istanza dell'encoder per calcolare i token
tokenizer = tiktoken.get_encoding("cl100k_base")

def detect_section_structure(text: str) -> Dict[str, List[str]]:
    """Rileva la struttura gerarchica del documento in base ai titoli"""
    # Pattern per trovare titoli di vari livelli
    patterns = {
        1: r'^#\s+(.+)$',       # # Titolo
        2: r'^##\s+(.+)$',      # ## Sottotitolo
        3: r'^###\s+(.+)$',     # ### Sotto-sottotitolo
        4: r'^####\s+(.+)$',    # #### Livello 4
        5: r'^#####\s+(.+)$',   # ##### Livello 5
    }
    
    # Struttura del documento
    structure: Dict[str, List[str]] = {}
    current_section = None
    
    # Analizza il testo riga per riga
    lines = text.split('\n')
    for line in lines:
        for level, pattern in patterns.items():
            match = re.match(pattern, line)
            if match:
                title = match.group(1).strip()
                if level == 1:
                    # Sezione principale
                    current_section = title
                    structure[current_section] = []
                elif level == 2 and current_section:
                    # Sottosezione
                    structure[current_section].append(title)
                break
    
    # Se non è stata trovata alcuna struttura, crea una struttura predefinita
    if not structure:
        structure = {"Documento": []}
    
    return structure

def count_tokens(text: str) -> int:
    """Conta il numero di token in un testo"""
    return len(tokenizer.encode(text))

def chunk_document(text: str, structure: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
    """Suddivide un documento in chunk gerarchici basati sulla struttura delle sezioni"""
    if structure is None:
        structure = detect_section_structure(text)
    
    # Risultato: dizionario di chunk con metadati
    chunks = {}
    
    # Pattern per trovare titoli di vari livelli
    section_patterns = {
        1: r'^#\s+(.+)$',       # # Titolo
        2: r'^##\s+(.+)$',      # ## Sottotitolo
    }
    
    # Suddividi il testo in sezioni principali
    sections = re.split(r'^#\s+', text, flags=re.MULTILINE)
    
    # Il primo elemento è il testo prima del primo titolo (potrebbe essere vuoto)
    preamble = sections.pop(0).strip()
    if preamble:
        chunk_id = str(uuid.uuid4())
        chunks[chunk_id] = {
            "id": chunk_id,
            "content": preamble,
            "section": "Introduzione",
            "subsection": None,
            "parent_id": None,
            "level": 0,
            "embeddings": None,
            "summary": None
        }
    
    # Processa ogni sezione principale
    for i, section_content in enumerate(sections):
        # Estrai il titolo della sezione dalla prima riga
        section_lines = section_content.split('\n')
        section_title = section_lines[0].strip()
        
        # Rimuovi il titolo dal contenuto e unisci il resto
        section_content_without_title = '\n'.join(section_lines[1:]).strip()
        
        # Aggiungi il titolo formattato all'inizio del contenuto
        section_text = f"# {section_title}\n\n{section_content_without_title}"
        
        # Crea un chunk per la sezione principale
        section_id = str(uuid.uuid4())
        
        # Se la sezione è troppo grande, suddividila in sottosezioni
        if count_tokens(section_text) > MAX_CHUNK_SIZE:
            # Suddividi in sottosezioni
            subsection_parts = re.split(r'^##\s+', section_content_without_title, flags=re.MULTILINE)
            
            # Il primo elemento è il testo prima della prima sottosezione
            main_content = subsection_parts.pop(0).strip()
            
            # Crea un chunk per il contenuto principale della sezione
            if main_content and count_tokens(main_content) > MIN_CHUNK_SIZE:
                chunks[section_id] = {
                    "id": section_id,
                    "content": f"# {section_title}\n\n{main_content}",
                    "section": section_title,
                    "subsection": None,
                    "parent_id": None,
                    "level": 1,
                    "embeddings": None,
                    "summary": None
                }
            
            # Processa ogni sottosezione
            for j, subsection_content in enumerate(subsection_parts):
                # Estrai il titolo della sottosezione dalla prima riga
                subsection_lines = subsection_content.split('\n')
                subsection_title = subsection_lines[0].strip()
                
                # Rimuovi il titolo dal contenuto e unisci il resto
                subsection_content_without_title = '\n'.join(subsection_lines[1:]).strip()
                
                # Aggiungi il titolo formattato all'inizio del contenuto
                subsection_text = f"## {subsection_title}\n\n{subsection_content_without_title}"
                
                # Se la sottosezione è ancora troppo grande, suddividila ulteriormente
                if count_tokens(subsection_text) > MAX_CHUNK_SIZE:
                    # Suddividi in paragrafi
                    paragraphs = re.split(r'\n\n+', subsection_text)
                    
                    # Raggruppa i paragrafi in chunk di dimensione appropriata
                    current_chunk = ""
                    for paragraph in paragraphs:
                        if count_tokens(current_chunk + "\n\n" + paragraph) <= MAX_CHUNK_SIZE:
                            if current_chunk:
                                current_chunk += "\n\n"
                            current_chunk += paragraph
                        else:
                            if current_chunk:
                                # Salva il chunk corrente
                                chunk_id = str(uuid.uuid4())
                                chunks[chunk_id] = {
                                    "id": chunk_id,
                                    "content": current_chunk,
                                    "section": section_title,
                                    "subsection": subsection_title,
                                    "parent_id": section_id,
                                    "level": 2,
                                    "embeddings": None,
                                    "summary": None
                                }
                            # Inizia un nuovo chunk
                            current_chunk = paragraph
                    
                    # Salva l'ultimo chunk
                    if current_chunk:
                        chunk_id = str(uuid.uuid4())
                        chunks[chunk_id] = {
                            "id": chunk_id,
                            "content": current_chunk,
                            "section": section_title,
                            "subsection": subsection_title,
                            "parent_id": section_id,
                            "level": 2,
                            "embeddings": None,
                            "summary": None
                        }
                else:
                    # La sottosezione è abbastanza piccola, salvala come un unico chunk
                    chunk_id = str(uuid.uuid4())
                    chunks[chunk_id] = {
                        "id": chunk_id,
                        "content": subsection_text,
                        "section": section_title,
                        "subsection": subsection_title,
                        "parent_id": section_id,
                        "level": 2,
                        "embeddings": None,
                        "summary": None
                    }
        else:
            # La sezione è abbastanza piccola, salvala come un unico chunk
            chunks[section_id] = {
                "id": section_id,
                "content": section_text,
                "section": section_title,
                "subsection": None,
                "parent_id": None,
                "level": 1,
                "embeddings": None,
                "summary": None
            }
    
    # Se non ci sono sezioni, tratta il documento come un unico chunk
    if not chunks:
        chunk_id = str(uuid.uuid4())
        chunks[chunk_id] = {
            "id": chunk_id,
            "content": text.strip(),
            "section": "Documento",
            "subsection": None,
            "parent_id": None,
            "level": 0,
            "embeddings": None,
            "summary": None
        }
    
    return {
        "chunks": chunks,
        "structure": structure or {"Documento": []}
    }

def generate_chunk_summaries(chunks: Dict[str, Any]) -> Dict[str, Any]:
    """Genera riassunti per ogni chunk per facilitare la navigazione e la ricerca"""
    # Implementazione della generazione di riassunti
    # Questo richiederebbe l'uso di un modello LLM per generare riassunti
    # Per ora, restituiamo i chunk senza modifiche
    return chunks

def merge_chunks(chunks: Dict[str, Any], chunk_ids: List[str]) -> Dict[str, Any]:
    """Unisce più chunk in un unico chunk mantenendo i metadati appropriati"""
    if not chunk_ids or len(chunk_ids) == 0:
        return {}
    
    if len(chunk_ids) == 1:
        return chunks[chunk_ids[0]]
    
    # Raccogli i chunk da unire
    chunks_to_merge = [chunks[chunk_id] for chunk_id in chunk_ids if chunk_id in chunks]
    
    if not chunks_to_merge:
        return {}
    
    # Ordina i chunk per livello e poi per sezione/sottosezione
    chunks_to_merge.sort(key=lambda x: (x["level"], x["section"], x["subsection"] or ""))
    
    # Unisci i contenuti
    merged_content = "\n\n".join([chunk["content"] for chunk in chunks_to_merge])
    
    # Crea un nuovo chunk unito
    merged_chunk = {
        "id": str(uuid.uuid4()),
        "content": merged_content,
        "section": chunks_to_merge[0]["section"],
        "subsection": chunks_to_merge[0]["subsection"],
        "parent_id": chunks_to_merge[0]["parent_id"],
        "level": chunks_to_merge[0]["level"],
        "embeddings": None,
        "summary": None
    }
    
    return merged_chunk