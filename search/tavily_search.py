#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integrazione aggiornata con Tavily API per ricerche di mercato e competitive.
Gestione header, errori e parametri secondo best practice 2024.
"""

import os
from typing import Dict, Any, List, Optional
import requests
import time

class TavilySearch:
    """Classe per l'integrazione con Tavily Search API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("Chiave API Tavily non trovata. Aggiungi TAVILY_API_KEY al file .env")
        self.base_url = "https://api.tavily.com"
        self.timeout = 30  # Timeout predefinito di 30 secondi
        self.retries = 3  # Numero massimo di tentativi
        self.backoff_factor = 1  # Fattore di backoff iniziale

    def _backoff(self, attempt):
        """Calcola il tempo di attesa per il backoff esponenziale"""
        wait_time = self.backoff_factor * (2 ** (attempt - 1))
        return wait_time

    def search(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 10,
        topic: str = "general",
        include_answer: bool = True,
        chunks_per_source: Optional[int] = None,
        time_range: Optional[str] = None,
        days: Optional[int] = None,
        include_images: Optional[bool] = None,
        include_image_descriptions: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Esegue una ricerca utilizzando Tavily Search API (endpoint /search).

        Args:
            query: stringa di ricerca (obbligatoria)
            search_depth: "basic" (default) o "advanced"
            max_results: numero massimo di risultati (max 20)
            topic: "general" (default) o "news"
            include_answer: se includere la risposta LLM (default True)
            chunks_per_source: solo per search_depth="advanced" (1-3)
            time_range: filtra per periodo (es. "month", "year", "2024-01-01to2024-12-31")
            days: solo se topic="news"
            include_images: se includere immagini
            include_image_descriptions: se includere descrizioni immagini
        """
        endpoint = f"{self.base_url}/search"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "topic": topic,
            "include_answer": include_answer
        }
        if chunks_per_source is not None:
            data["chunks_per_source"] = chunks_per_source
        if time_range is not None:
            data["time_range"] = time_range
        if days is not None:
            data["days"] = days
        if include_images is not None:
            data["include_images"] = include_images
        if include_image_descriptions is not None:
            data["include_image_descriptions"] = include_image_descriptions

        for attempt in range(1, self.retries + 1):
            try:
                response = requests.post(endpoint, headers=headers, json=data, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    print(f"Errore Tavily API: 401 Unauthorized - Chiave API non valida o non abilitata (tentativo {attempt}/{self.retries})")
                    if attempt == self.retries:
                        return {"error": "401 Unauthorized - Chiave API non valida o non abilitata", "results": []}
                    wait_time = self._backoff(attempt)
                    print(f"Ritento tra {wait_time} secondi...")
                    time.sleep(wait_time)
                elif response.status_code == 422:
                    print("Errore Tavily API: 422 Unprocessable Entity - Parametri query non validi")
                    return {"error": "422 Unprocessable Entity - Parametri query non validi", "results": []}
                elif response.status_code == 400:
                    print(f"Errore Tavily API: 400 Bad Request - Controlla i parametri inviati: {response.text}")
                    return {"error": f"400 Bad Request - {response.text}", "results": []}
                else:
                    print(f"Errore Tavily API: {e}")
                    if attempt == self.retries:
                        return {"error": str(e), "results": []}
                    wait_time = self._backoff(attempt)
                    print(f"Ritento tra {wait_time} secondi...")
                    time.sleep(wait_time)
            except requests.exceptions.RequestException as e:
                print(f"Errore generico Tavily API: {e}")
                if attempt == self.retries:
                    return {"error": str(e), "results": []}
                wait_time = self._backoff(attempt)
                print(f"Ritento tra {wait_time} secondi...")
                time.sleep(wait_time)
        return {"error": "Tutti i tentativi sono falliti", "results": []}

    def market_analysis(self, industry: str, target_market: str, region: str = "Italia") -> Dict[str, Any]:
        query = f"Fornisci un'analisi dettagliata del mercato {industry} con focus su {target_market} in {region}. Includi dimensioni del mercato, tasso di crescita, tendenze principali, segmentazione e previsioni future."
        return self.search(query, search_depth="advanced", max_results=15)

    def competitor_analysis(self, company_name: str, industry: str, target_market: str) -> Dict[str, Any]:
        query = f"Analisi competitiva completa per un'azienda chiamata {company_name} nel settore {industry} che si rivolge al mercato {target_market}. Identifica i principali concorrenti, le loro quote di mercato, punti di forza, punti deboli, strategie e posizionamento."
        return self.search(query, search_depth="advanced", max_results=15)

    def market_opportunities(self, industry: str, target_market: str, region: str = "Italia") -> Dict[str, Any]:
        query = f"Identifica le principali opportunità di mercato nel settore {industry} per il segmento {target_market} in {region}. Evidenzia gap di mercato, esigenze non soddisfatte, tendenze emergenti e potenziali aree di crescita."
        return self.search(query, search_depth="advanced", max_results=10)

    def market_risks(self, industry: str, target_market: str, region: str = "Italia") -> Dict[str, Any]:
        query = f"Quali sono i principali rischi e sfide che un'azienda nel settore {industry} potrebbe affrontare nel segmento {target_market} in {region}? Considera fattori economici, normativi, tecnologici e competitivi."
        return self.search(query, search_depth="basic", max_results=10)
