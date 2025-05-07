#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integrazione avanzata con Perplexity API per ricerche di mercato approfondite
Utilizza la libreria openai con base_url Perplexity, headers e gestione errori secondo best practice 2024.
Supporta modelli sonar-pro e sonar-medium-online per ricerche ottimizzate.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional, Union
from openai import OpenAI, AuthenticationError, APIError, RateLimitError

class PerplexitySearch:
    """Classe per l'integrazione con Perplexity API (nuovo client OpenAI)"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key or not self.api_key.startswith("pplx-"):
            raise ValueError("Chiave API Perplexity non trovata o non valida. Aggiungi PERPLEXITY_API_KEY al file .env")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.perplexity.ai",
            timeout=60.0  # Timeout aumentato per ricerche complesse
        )

        # Modelli disponibili
        self.models = {
            "pro": "sonar-pro",              # Modello più potente, per analisi approfondite
            "medium": "sonar-medium-online",  # Modello bilanciato, per ricerche standard
            "small": "sonar-small-online"     # Modello leggero, per ricerche rapide
        }

        # Cache per evitare ricerche duplicate
        self.cache = {}
        self.cache_ttl = 3600  # 1 ora di validità cache

    def search(self, query: str, model_size: str = "pro", temperature: float = 0.4,
               max_tokens: int = 2000, use_cache: bool = True) -> Dict[str, Any]:
        """
        Esegue una ricerca utilizzando Perplexity API

        Args:
            query: La query di ricerca
            model_size: Dimensione del modello ('pro', 'medium', 'small')
            temperature: Temperatura per la generazione (0.0-1.0)
            max_tokens: Numero massimo di token nella risposta
            use_cache: Se utilizzare la cache per query identiche

        Returns:
            Dizionario con i risultati della ricerca
        """
        # Verifica se la query è nella cache e se è ancora valida
        cache_key = f"{query}_{model_size}_{temperature}_{max_tokens}"
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                print(f"Usando risultato in cache per: {query[:50]}...")
                return cache_entry["result"]

        # Seleziona il modello appropriato
        model = self.models.get(model_size, self.models["pro"])

        try:
            # Prepara il prompt di sistema in base al tipo di ricerca
            system_prompt = (
                "Sei un analista di mercato esperto. Rispondi in modo dettagliato e strutturato, "
                "con dati numerici, trend, competitor, opportunità, rischi e almeno 5 fonti web attendibili. "
                "Cita le fonti in fondo alla risposta. Organizza la risposta in sezioni chiare. "
                "Includi sempre dati quantitativi quando disponibili. "
                "Rispondi in italiano."
            )

            # Esegui la richiesta API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Estrai e formatta la risposta
            result = self._format_response(response)

            # Salva nella cache
            if use_cache:
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "result": result
                }

            return result

        except RateLimitError as e:
            print(f"Errore limite di rate Perplexity API: {e}")
            return {
                "error": "429 Rate Limit - Troppe richieste. Attendi qualche minuto prima di riprovare.",
                "results": [],
                "status": "error"
            }
        except AuthenticationError as e:
            print(f"Errore autenticazione Perplexity API: {e}")
            return {
                "error": "401 Unauthorized - Chiave API non valida o non abilitata",
                "results": [],
                "status": "error"
            }
        except APIError as e:
            print(f"Errore API Perplexity: {e}")
            return {"error": str(e), "results": [], "status": "error"}
        except Exception as e:
            print(f"Errore generico Perplexity: {e}")
            return {"error": str(e), "results": [], "status": "error"}

    def _format_response(self, response: Any) -> Dict[str, Any]:
        """Formatta la risposta dell'API in un formato strutturato"""
        try:
            # Estrai il testo della risposta
            if hasattr(response, "choices") and len(response.choices) > 0:
                content = response.choices[0].message.content
            else:
                return {"error": "Formato di risposta non valido", "status": "error"}

            # Converti in dizionario se possibile
            response_dict = response.model_dump() if hasattr(response, "model_dump") else dict(response)

            # Aggiungi il testo estratto e lo stato
            response_dict["extracted_text"] = content
            response_dict["status"] = "success"

            return response_dict
        except Exception as e:
            print(f"Errore nella formattazione della risposta: {e}")
            return {"error": str(e), "status": "error"}

    def market_research(self, company_name: str, industry: str, target_market: str,
                        region: str = "Italia", detailed: bool = True) -> Dict[str, Any]:
        """
        Esegue una ricerca di mercato approfondita

        Args:
            company_name: Nome dell'azienda
            industry: Settore industriale
            target_market: Mercato target
            region: Regione geografica
            detailed: Se eseguire un'analisi dettagliata

        Returns:
            Dizionario con i risultati dell'analisi di mercato
        """
        model = "pro" if detailed else "medium"

        query = (
            f"Analisi di mercato aggiornata e approfondita per il settore {industry} in {region}, "
            f"focalizzata sul mercato target {target_market}, per l'azienda: {company_name}.\n\n"
            f"Includi le seguenti sezioni:\n"
            f"1. Dimensione del mercato (in euro e CAGR)\n"
            f"2. Trend principali (almeno 5)\n"
            f"3. Competitor principali (almeno 5, con quote di mercato se disponibili)\n"
            f"4. Opportunità di crescita (almeno 3)\n"
            f"5. Rischi e sfide (almeno 3)\n"
            f"6. Segmentazione del mercato\n\n"
            f"Cita almeno 5 fonti attendibili e recenti."
        )

        return self.search(query, model_size=model, temperature=0.3, max_tokens=2500 if detailed else 1800)

    def competitor_analysis(self, company_name: str, industry: str,
                           competitors: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Esegue un'analisi competitiva dettagliata

        Args:
            company_name: Nome dell'azienda
            industry: Settore industriale
            competitors: Lista di competitor specifici da analizzare

        Returns:
            Dizionario con i risultati dell'analisi competitiva
        """
        competitors_str = ", ".join(competitors) if competitors else "principali competitor del settore"

        query = (
            f"Analisi competitiva dettagliata per l'azienda {company_name} nel settore {industry}.\n\n"
            f"Analizza i seguenti competitor: {competitors_str}.\n\n"
            f"Per ciascun competitor includi:\n"
            f"1. Quota di mercato stimata\n"
            f"2. Punti di forza\n"
            f"3. Punti di debolezza\n"
            f"4. Strategia di mercato\n"
            f"5. Posizionamento rispetto a {company_name}\n\n"
            f"Concludi con un'analisi SWOT per {company_name} rispetto ai competitor.\n"
            f"Cita fonti attendibili e recenti."
        )

        return self.search(query, model_size="pro", temperature=0.3, max_tokens=2500)

    def trend_analysis(self, industry: str, timeframe: str = "prossimi 3 anni") -> Dict[str, Any]:
        """
        Analizza i trend di settore

        Args:
            industry: Settore industriale
            timeframe: Orizzonte temporale dell'analisi

        Returns:
            Dizionario con i risultati dell'analisi dei trend
        """
        query = (
            f"Analisi approfondita dei trend nel settore {industry} per i {timeframe}.\n\n"
            f"Includi:\n"
            f"1. Trend tecnologici emergenti\n"
            f"2. Cambiamenti nelle preferenze dei consumatori\n"
            f"3. Innovazioni di prodotto/servizio\n"
            f"4. Trend normativi e regolamentari\n"
            f"5. Previsioni di crescita\n\n"
            f"Supporta con dati quantitativi e cita fonti attendibili."
        )

        return self.search(query, model_size="medium", temperature=0.4, max_tokens=2000)

    def financial_analysis(self, company_name: str, industry: str, company_stage: str = "startup",
                          funding_needs: Optional[str] = None) -> Dict[str, Any]:
        """
        Esegue un'analisi finanziaria per un business plan

        Args:
            company_name: Nome dell'azienda
            industry: Settore industriale
            company_stage: Fase dell'azienda (startup, growth, mature)
            funding_needs: Necessità di finanziamento (opzionale)

        Returns:
            Dizionario con i risultati dell'analisi finanziaria
        """
        funding_str = f", con necessità di finanziamento di {funding_needs}" if funding_needs else ""

        query = (
            f"Analisi finanziaria dettagliata per un business plan di {company_name}, "
            f"azienda in fase {company_stage} nel settore {industry}{funding_str}.\n\n"
            f"Includi le seguenti sezioni:\n"
            f"1. Struttura dei costi tipica per questo settore (costi fissi e variabili)\n"
            f"2. Metriche finanziarie chiave e KPI per il settore\n"
            f"3. Proiezioni finanziarie tipiche (fatturato, margini, break-even)\n"
            f"4. Fonti di finanziamento consigliate\n"
            f"5. Rischi finanziari principali\n\n"
            f"Fornisci dati numerici specifici e benchmark di settore quando possibile.\n"
            f"Cita fonti attendibili e recenti."
        )

        return self.search(query, model_size="pro", temperature=0.3, max_tokens=2500)

    def marketing_strategy(self, company_name: str, industry: str, target_market: str,
                          products: Optional[str] = None) -> Dict[str, Any]:
        """
        Esegue un'analisi della strategia di marketing

        Args:
            company_name: Nome dell'azienda
            industry: Settore industriale
            target_market: Mercato target
            products: Prodotti/servizi offerti (opzionale)

        Returns:
            Dizionario con i risultati dell'analisi di marketing
        """
        products_str = f", che offre {products}" if products else ""

        query = (
            f"Strategia di marketing completa per {company_name}, azienda nel settore {industry}{products_str}, "
            f"rivolta al mercato target: {target_market}.\n\n"
            f"Includi le seguenti sezioni:\n"
            f"1. Canali di marketing più efficaci per questo settore e target\n"
            f"2. Strategie di pricing consigliate con esempi numerici\n"
            f"3. Strategie di posizionamento rispetto ai competitor\n"
            f"4. Tattiche di acquisizione clienti con costi stimati (CAC)\n"
            f"5. Metriche di marketing da monitorare\n"
            f"6. Budget di marketing consigliato (% sul fatturato)\n\n"
            f"Fornisci esempi concreti e dati numerici quando possibile.\n"
            f"Cita fonti attendibili e recenti."
        )

        return self.search(query, model_size="pro", temperature=0.3, max_tokens=2500)

    def operational_plan(self, company_name: str, industry: str, company_size: str = "piccola",
                        location: str = "Italia") -> Dict[str, Any]:
        """
        Esegue un'analisi del piano operativo

        Args:
            company_name: Nome dell'azienda
            industry: Settore industriale
            company_size: Dimensione dell'azienda (piccola, media, grande)
            location: Localizzazione geografica

        Returns:
            Dizionario con i risultati dell'analisi operativa
        """
        query = (
            f"Piano operativo dettagliato per {company_name}, azienda {company_size} nel settore {industry} in {location}.\n\n"
            f"Includi le seguenti sezioni:\n"
            f"1. Struttura organizzativa consigliata\n"
            f"2. Processi operativi chiave\n"
            f"3. Risorse necessarie (umane, tecnologiche, fisiche)\n"
            f"4. Fornitori e partner strategici tipici del settore\n"
            f"5. Tecnologie e sistemi informativi consigliati\n"
            f"6. Metriche operative da monitorare\n\n"
            f"Fornisci esempi concreti e best practice del settore.\n"
            f"Cita fonti attendibili e recenti."
        )

        return self.search(query, model_size="medium", temperature=0.4, max_tokens=2000)



    def operational_plan(self, company_name: str, industry: str, company_size: str = "piccola",
                        location: str = "Italia") -> Dict[str, Any]:
        """
        Esegue un'analisi del piano operativo

        Args:
            company_name: Nome dell'azienda
            industry: Settore industriale
            company_size: Dimensione dell'azienda (piccola, media, grande)
            location: Localizzazione geografica

        Returns:
            Dizionario con i risultati dell'analisi operativa
        """
        query = (
            f"Piano operativo dettagliato per {company_name}, azienda {company_size} nel settore {industry} in {location}.\n\n"
            f"Includi le seguenti sezioni:\n"
            f"1. Struttura organizzativa consigliata\n"
            f"2. Processi operativi chiave\n"
            f"3. Risorse necessarie (umane, tecnologiche, fisiche)\n"
            f"4. Fornitori e partner strategici tipici del settore\n"
            f"5. Tecnologie e sistemi informativi consigliati\n"
            f"6. Metriche operative da monitorare\n\n"
            f"Fornisci esempi concreti e best practice del settore.\n"
            f"Cita fonti attendibili e recenti."
        )

        return self.search(query, model_size="medium", temperature=0.4, max_tokens=2000)
