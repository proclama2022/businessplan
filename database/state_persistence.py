#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Persistenza dello stato per il Business Plan Builder

Questo modulo gestisce il salvataggio e il caricamento dello stato del business plan,
permettendo di mantenere il contesto attraverso sessioni diverse e di riprendere
il lavoro da dove era stato interrotto.
"""

import os
import json
import pickle
from typing import Dict, Any, Optional
from datetime import datetime
from config import Config

class StatePersistence:
    """Classe per la gestione della persistenza dello stato"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Inizializza il sistema di persistenza dello stato"""
        self.storage_dir = storage_dir or os.path.join(Config.VECTOR_DB_PATH, "state")
        
        # Crea la directory se non esiste
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def save_state(self, state: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Salva lo stato su disco"""
        if filename is None:
            # Genera un nome file basato sul titolo del documento e sulla data
            safe_title = state.get("document_title", "business_plan").replace(" ", "_").lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_title}_{timestamp}.state"
        
        # Percorso completo del file
        filepath = os.path.join(self.storage_dir, filename)
        
        # Prepara una copia dello stato per il salvataggio
        # Converti i set in liste per la serializzazione JSON
        state_copy = state.copy()
        if "completed_sections" in state_copy:
            state_copy["completed_sections"] = list(state_copy["completed_sections"])
        if "approved_sections" in state_copy:
            state_copy["approved_sections"] = list(state_copy["approved_sections"])
        
        # Rimuovi i messaggi per evitare file troppo grandi
        if "messages" in state_copy:
            # Salva solo gli ultimi 10 messaggi
            state_copy["messages"] = state_copy["messages"][-10:] if state_copy["messages"] else []
        
        # Salva lo stato in formato JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state_copy, f, ensure_ascii=False, indent=2)
        
        # Salva anche una versione binaria per i dati complessi (come gli embedding)
        binary_filepath = f"{filepath}.pkl"
        with open(binary_filepath, "wb") as f:
            pickle.dump(state, f)
        
        return filename
    
    def load_state(self, filename: str) -> Dict[str, Any]:
        """Carica lo stato da disco"""
        # Percorso completo del file
        filepath = os.path.join(self.storage_dir, filename)
        
        # Prova a caricare la versione binaria (più completa)
        binary_filepath = f"{filepath}.pkl"
        if os.path.exists(binary_filepath):
            try:
                with open(binary_filepath, "rb") as f:
                    state = pickle.load(f)
                return state
            except Exception as e:
                print(f"Errore nel caricamento dello stato binario: {e}")
        
        # Fallback: carica la versione JSON
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    state = json.load(f)
                
                # Converti le liste in set
                if "completed_sections" in state:
                    state["completed_sections"] = set(state["completed_sections"])
                if "approved_sections" in state:
                    state["approved_sections"] = set(state["approved_sections"])
                
                return state
            except Exception as e:
                print(f"Errore nel caricamento dello stato JSON: {e}")
        
        raise FileNotFoundError(f"File di stato non trovato: {filename}")
    
    def list_saved_states(self) -> Dict[str, Dict[str, Any]]:
        """Elenca tutti gli stati salvati con i loro metadati"""
        saved_states = {}
        
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".state"):
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        state_data = json.load(f)
                    
                    # Estrai i metadati principali
                    saved_states[filename] = {
                        "document_title": state_data.get("document_title", "Sconosciuto"),
                        "company_name": state_data.get("company_name", "Sconosciuta"),
                        "creation_date": state_data.get("creation_date", "Sconosciuta"),
                        "version": state_data.get("version", 1),
                        "last_modified": datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S"),
                        "file_size": os.path.getsize(filepath),
                        "completed_sections": len(state_data.get("completed_sections", [])),
                        "total_sections": len(state_data.get("outline", {}))
                    }
                except Exception as e:
                    print(f"Errore nella lettura dei metadati per {filename}: {e}")
        
        return saved_states
    
    def delete_state(self, filename: str) -> bool:
        """Elimina uno stato salvato"""
        filepath = os.path.join(self.storage_dir, filename)
        binary_filepath = f"{filepath}.pkl"
        
        success = True
        
        # Elimina il file JSON
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Errore nell'eliminazione del file {filepath}: {e}")
                success = False
        
        # Elimina il file binario
        if os.path.exists(binary_filepath):
            try:
                os.remove(binary_filepath)
            except Exception as e:
                print(f"Errore nell'eliminazione del file {binary_filepath}: {e}")
                success = False
        
        return success
    
    def create_backup(self, state: Dict[str, Any]) -> str:
        """Crea un backup dello stato corrente"""
        # Genera un nome file per il backup
        safe_title = state.get("document_title", "business_plan").replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{safe_title}_backup_{timestamp}.state"
        
        # Salva lo stato con il nome del backup
        return self.save_state(state, backup_filename)
    
    def auto_save(self, state: Dict[str, Any], interval_minutes: int = 10) -> Optional[str]:
        """Salva automaticamente lo stato se è passato abbastanza tempo dall'ultimo salvataggio"""
        # Controlla l'ultimo salvataggio automatico
        last_autosave_file = os.path.join(self.storage_dir, "last_autosave.txt")
        
        current_time = datetime.now()
        should_save = True
        
        if os.path.exists(last_autosave_file):
            try:
                with open(last_autosave_file, "r") as f:
                    last_save_time_str = f.read().strip()
                    last_save_time = datetime.fromisoformat(last_save_time_str)
                    
                    # Calcola il tempo trascorso in minuti
                    elapsed_minutes = (current_time - last_save_time).total_seconds() / 60
                    
                    # Salva solo se è passato abbastanza tempo
                    should_save = elapsed_minutes >= interval_minutes
            except Exception:
                # In caso di errore, procedi con il salvataggio
                pass
        
        if should_save:
            # Genera un nome file per l'autosave
            safe_title = state.get("document_title", "business_plan").replace(" ", "_").lower()
            autosave_filename = f"{safe_title}_autosave.state"
            
            # Salva lo stato
            filename = self.save_state(state, autosave_filename)
            
            # Aggiorna il timestamp dell'ultimo salvataggio
            with open(last_autosave_file, "w") as f:
                f.write(current_time.isoformat())
            
            return filename
        
        return None