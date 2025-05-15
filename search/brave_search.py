#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integrazione aggiornata con Brave Search API per ricerche di mercato
Gestione header, errori e parametri secondo best practice 2024.
"""

import os
from typing import Dict, Any, List, Optional
import requests
from search.brave_cache import get_cached_result, set_cached_result

class BraveSearch:
    """Classe per l'integrazione con Brave Search API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BRAVE_SEARCH_API_KEY")
        if not self.api_key:
            raise ValueError("Chiave API Brave Search non trovata. Aggiungi BRAVE_SEARCH_API_KEY al file .env")
        self.base_url = "https://api.search.brave.com/res/v1"
        self.timeout = 30  # Timeout predefinito di 30 secondi

    def search(
        self,
        query: str,
        count: int = 10,
        search_lang: str = "it",
        country: str = "IT",
        safesearch: str = "moderate",
        freshness: Optional[str] = None,
        result_filter: Optional[str] = None,
        summary: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Esegue una ricerca utilizzando Brave Search API con caching locale.

        Args:
            query: stringa di ricerca
            count: numero di risultati (max 20)
            search_lang: lingua dei risultati (default "it")
            country: paese dei risultati (default "IT")
            safesearch: filtro contenuti adulti ("off", "moderate", "strict")
            freshness: filtra per data (es. "pm", "py", "2024-01-01to2024-12-31")
            result_filter: filtra per tipo di risultato (es. "web,news")
            summary: abilita generazione riassunto (True/False)
        """
        # Caching: chiave cache = query + parametri principali
        cache_key = f"{query}|{count}|{search_lang}|{country}|{safesearch}|{freshness}|{result_filter}|{summary}"
        cached = get_cached_result(cache_key)
        if cached is not None:
            return cached

        endpoint = f"{self.base_url}/web/search"
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        params = {
            "q": query,
            "count": count,
            "search_lang": search_lang,
            "country": country,
            "safesearch": safesearch
        }
        if freshness:
            params["freshness"] = freshness
        if result_filter:
            params["result_filter"] = result_filter
        if summary is not None:
            params["summary"] = str(summary).lower()
        retries = 0
        max_retries = 4
        while retries < max_retries:
            try:
                response = requests.get(endpoint, headers=headers, params=params, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                set_cached_result(cache_key, result)
                return result
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    print("Errore Brave API: 401 Unauthorized - Chiave API non valida o non abilitata")
                    return {"error": "401 Unauthorized - Chiave API non valida o non abilitata", "results": []}
                elif response.status_code == 422:
                    print("Errore Brave API: 422 Unprocessable Entity - Parametri query non validi")
                    return {"error": "422 Unprocessable Entity - Parametri query non validi", "results": []}
                elif response.status_code == 429:
                    print("Errore Brave API: 429 Too Many Requests - Attendo e ritento...")
                    import time
                    delay = 2 ** retries
                    time.sleep(delay)
                    retries += 1
                    continue
                else:
                    print(f"Errore Brave API: {e}")
                    return {"error": str(e), "results": []}
            except Exception as e:
                print(f"Errore generico Brave API: {e}")
                return {"error": str(e), "results": []}
        print("Errore Brave API: Limite di retry superato (troppi 429)")
        return {"error": "429 Too Many Requests - Limite di retry superato", "results": []}

    def market_analysis(self, industry: str, target_market: str, region: str = "Italia") -> List[Dict[str, Any]]:
        query = f"analisi mercato {industry} {target_market} {region} statistiche recenti"
        results = self.search(query, count=15)
        return results.get("web", {}).get("results", [])

    def competitor_analysis(self, company_name: str, industry: str, target_market: str) -> List[Dict[str, Any]]:
        query = f"concorrenti aziende {industry} {target_market} analisi SWOT"
        results = self.search(query, count=15)
        return results.get("web", {}).get("results", [])

    def find_market_trends(self, industry: str, target_market: str, year: str = "2025") -> List[Dict[str, Any]]:
        query = f"tendenze mercato {industry} {target_market} {year} trend principali"
        results = self.search(query, count=15)
        return results.get("web", {}).get("results", [])

    def find_market_opportunities(self, industry: str, target_market: str) -> List[Dict[str, Any]]:
        query = f"opportunità di mercato {industry} {target_market} gap di mercato"
        results = self.search(query, count=15)
        return results.get("web", {}).get("results", [])
