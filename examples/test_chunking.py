#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test del sistema di chunking gerarchico

Questo script dimostra l'utilizzo del modulo di chunking gerarchico per suddividere
un business plan di esempio in chunk mantenendo la struttura e il contesto.
"""

import os
import sys
import json
from pathlib import Path

# Aggiungi la directory principale al path per importare i moduli del progetto
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunking.hierarchical import chunk_document, detect_section_structure, generate_chunk_summaries
from config import MAX_CHUNK_SIZE, MIN_CHUNK_SIZE, CHUNK_OVERLAP

def load_example_document(file_path):
    """Carica un documento di esempio in formato markdown"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def print_chunk_info(chunk_id, chunk, indent=0):
    """Stampa informazioni su un chunk in modo leggibile"""
    indent_str = ' ' * indent
    print(f"{indent_str}Chunk ID: {chunk_id}")
    print(f"{indent_str}Sezione: {chunk['section']}")
    if chunk['subsection']:
        print(f"{indent_str}Sottosezione: {chunk['subsection']}")
    print(f"{indent_str}Livello: {chunk['level']}")
    print(f"{indent_str}Lunghezza contenuto: {len(chunk['content'])} caratteri")
    print(f"{indent_str}Primi 100 caratteri: {chunk['content'][:100]}...")
    print()

def main():
    """Funzione principale per testare il chunking gerarchico"""
    # Percorso del documento di esempio
    example_path = os.path.join(os.path.dirname(__file__), "esempio_business_plan.md")
    
    print(f"\n===== Test del Sistema di Chunking Gerarchico =====\n")
    print(f"Dimensione massima chunk: {MAX_CHUNK_SIZE} token")
    print(f"Dimensione minima chunk: {MIN_CHUNK_SIZE} token")
    print(f"Sovrapposizione chunk: {CHUNK_OVERLAP} token\n")
    
    # Carica il documento di esempio
    try:
        document = load_example_document(example_path)
        print(f"Documento caricato: {example_path}")
        print(f"Lunghezza documento: {len(document)} caratteri\n")
    except Exception as e:
        print(f"Errore nel caricamento del documento: {e}")
        return
    
    # Rileva la struttura del documento
    print("Rilevamento della struttura del documento...")
    structure = detect_section_structure(document)
    print(f"Struttura rilevata: {len(structure)} sezioni principali")
    for section, subsections in structure.items():
        print(f"  - {section} ({len(subsections)} sottosezioni)")
    print()
    
    # Suddividi il documento in chunk
    print("Suddivisione del documento in chunk...")
    result = chunk_document(document, structure)
    chunks = result["chunks"]
    print(f"Documento suddiviso in {len(chunks)} chunk\n")
    
    # Stampa informazioni sui chunk
    print("Informazioni sui chunk generati:")
    
    # Raggruppa i chunk per sezione e livello
    sections = {}
    for chunk_id, chunk in chunks.items():
        section = chunk["section"]
        if section not in sections:
            sections[section] = []
        sections[section].append((chunk_id, chunk))
    
    # Stampa i chunk organizzati per sezione
    for section, section_chunks in sections.items():
        print(f"\nSEZIONE: {section} ({len(section_chunks)} chunk)")
        
        # Ordina i chunk per livello e sottosezione
        section_chunks.sort(key=lambda x: (x[1]["level"], x[1]["subsection"] or ""))
        
        for chunk_id, chunk in section_chunks:
            print_chunk_info(chunk_id, chunk, indent=2)
    
    # Genera riassunti per i chunk (opzionale)
    print("\nGenerazione dei riassunti per i chunk...")
    chunks_with_summaries = generate_chunk_summaries(chunks)
    print("Riassunti generati.\n")
    
    # Salva i risultati in un file JSON per ispezione
    output_path = os.path.join(os.path.dirname(__file__), "chunking_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Risultati salvati in: {output_path}")

if __name__ == "__main__":
    main()