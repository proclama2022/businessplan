#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo per il tracciamento dell'utilizzo delle generazioni AI

Questo modulo gestisce il conteggio delle generazioni AI per utente/sessione,
permettendo di limitare l'uso dell'AI in base ai limiti configurati.
"""

import os
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from config import Config

class UsageTracker:
    """Classe per tracciare l'utilizzo delle generazioni AI"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Inizializza il tracker di utilizzo"""
        self.storage_dir = storage_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "usage")
        
        # Crea la directory se non esiste
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Nome file per archiviare i dati di utilizzo
        self.usage_file = os.path.join(self.storage_dir, "usage_data.json")
        
        # Carica i dati di utilizzo esistenti o crea un nuovo dizionario
        self.usage_data = self._load_usage_data()
    
    def _load_usage_data(self) -> Dict[str, Any]:
        """Carica i dati di utilizzo dal file JSON"""
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Errore nel caricamento dei dati di utilizzo: {e}")
                return {}
        return {}
    
    def _save_usage_data(self) -> None:
        """Salva i dati di utilizzo nel file JSON"""
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Errore nel salvataggio dei dati di utilizzo: {e}")
    
    def increment_generation_count(self, session_id: str, tokens_generated: int = 0) -> None:
        """
        Incrementa il contatore delle generazioni per una sessione

        Args:
            session_id: ID della sessione utente
            tokens_generated: Numero stimato di token generati (opzionale)
        """
        # Assicura che il session_id sia una stringa
        session_id = str(session_id)
        
        # Ottieni il timestamp corrente
        current_time = time.time()
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Inizializza i dati della sessione se non esistono
        if session_id not in self.usage_data:
            self.usage_data[session_id] = {
                "first_access": current_time,
                "last_access": current_time,
                "generations_count": 0,
                "estimated_tokens": 0,
                "generations_by_date": {}
            }
        
        # Aggiorna i contatori
        self.usage_data[session_id]["last_access"] = current_time
        self.usage_data[session_id]["generations_count"] += 1
        self.usage_data[session_id]["estimated_tokens"] += tokens_generated
        
        # Aggiorna il contatore per data
        if current_date not in self.usage_data[session_id]["generations_by_date"]:
            self.usage_data[session_id]["generations_by_date"][current_date] = 0
        self.usage_data[session_id]["generations_by_date"][current_date] += 1
        
        # Salva i dati aggiornati
        self._save_usage_data()
    
    def get_usage_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Ottiene le statistiche di utilizzo per una sessione

        Args:
            session_id: ID della sessione utente

        Returns:
            Dict con le statistiche di utilizzo
        """
        # Assicura che il session_id sia una stringa
        session_id = str(session_id)
        
        # Ottieni il limite configurato
        generation_limit = Config.MAX_GENERATIONS_PER_SESSION
        
        # Se la sessione non esiste nei dati, restituisci statistiche predefinite
        if session_id not in self.usage_data:
            return {
                "total_generations": 0,
                "estimated_tokens": 0,
                "first_access": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_access": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "limit": generation_limit,
                "remaining": generation_limit,
                "percentage_used": 0.0
            }
        
        # Ottieni i dati della sessione
        session_data = self.usage_data[session_id]
        total_generations = session_data["generations_count"]
        estimated_tokens = session_data.get("estimated_tokens", 0)
        
        # Calcola le generazioni rimanenti
        remaining = max(0, generation_limit - total_generations)
        
        # Calcola la percentuale di utilizzo
        percentage_used = (total_generations / generation_limit) * 100 if generation_limit > 0 else 0
        
        # Formatta le date per la visualizzazione
        first_access = datetime.fromtimestamp(session_data["first_access"]).strftime("%Y-%m-%d %H:%M:%S")
        last_access = datetime.fromtimestamp(session_data["last_access"]).strftime("%Y-%m-%d %H:%M:%S")
        
        # Restituisci le statistiche
        return {
            "total_generations": total_generations,
            "estimated_tokens": estimated_tokens,
            "first_access": first_access,
            "last_access": last_access,
            "limit": generation_limit,
            "remaining": remaining,
            "percentage_used": percentage_used
        }
    
    def check_limit_reached(self, session_id: str) -> bool:
        """
        Verifica se il limite di generazioni è stato raggiunto

        Args:
            session_id: ID della sessione utente

        Returns:
            True se il limite è stato raggiunto, False altrimenti
        """
        # Assicura che il session_id sia una stringa
        session_id = str(session_id)
        
        # Ottieni il limite configurato
        generation_limit = Config.MAX_GENERATIONS_PER_SESSION
        
        # Se la sessione non esiste nei dati, non è stato raggiunto il limite
        if session_id not in self.usage_data:
            return False
        
        # Ottieni il conteggio delle generazioni per la sessione
        total_generations = self.usage_data[session_id]["generations_count"]
        
        # Restituisci True se il limite è stato raggiunto o superato
        return total_generations >= generation_limit
    
    def reset_usage(self, session_id: str) -> None:
        """
        Reimposta i contatori di utilizzo per una sessione (usato per test/debug)

        Args:
            session_id: ID della sessione utente
        """
        # Assicura che il session_id sia una stringa
        session_id = str(session_id)
        
        # Se la sessione esiste, reimpostala
        if session_id in self.usage_data:
            current_time = time.time()
            self.usage_data[session_id] = {
                "first_access": current_time,
                "last_access": current_time,
                "generations_count": 0,
                "estimated_tokens": 0,
                "generations_by_date": {}
            }
            
            # Salva i dati aggiornati
            self._save_usage_data()
    
    def get_all_usage_data(self) -> Dict[str, Any]:
        """
        Ottiene tutti i dati di utilizzo (per report amministrativi)

        Returns:
            Dict con tutti i dati di utilizzo
        """
        return self.usage_data 