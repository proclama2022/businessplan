#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo avanzato per la ricerca di mercato e analisi competitiva

Questo modulo utilizza Perplexity API per fornire analisi di mercato
e competitive approfondite, con supporto per caching e ricerche parallele.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple, Union
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Importa il modulo Perplexity
from search.perplexity import PerplexitySearch

class CombinedSearch:
    """Classe avanzata per eseguire ricerche di mercato e analisi competitive"""

    def __init__(self, perplexity_api_key: Optional[str] = None):
        """Inizializza il client di ricerca combinata"""
        self.perplexity_available = False
        self.last_error = None

        # Inizializza il client Perplexity se la chiave API è disponibile
        try:
            self.perplexity = PerplexitySearch(perplexity_api_key)
            self.perplexity_available = True
            print("Perplexity API inizializzata correttamente")
        except Exception as e:
            self.last_error = str(e)
            print(f"Perplexity API non disponibile: {e}")

        # Cache per risultati di ricerca
        self.cache = {}
        self.cache_ttl = 86400  # 24 ore di validità cache

    def clear_cache(self):
        """Pulisce la cache dei risultati"""
        self.cache = {}
        print("Cache di ricerca cancellata")

    def _run_parallel_searches(self, search_functions: List[Tuple[callable, str]]) -> List[Dict[str, Any]]:
        """Esegue le ricerche in parallelo e raccoglie i risultati"""
        results = []

        with ThreadPoolExecutor(max_workers=min(len(search_functions), 3)) as executor:
            future_to_search = {executor.submit(func): name for func, name in search_functions}
            for future in as_completed(future_to_search):
                name = future_to_search[future]
                try:
                    result = future.result()
                    results.append({"source": name, "result": result})
                except Exception as e:
                    print(f"Errore durante l'esecuzione della ricerca {name}: {e}")
                    results.append({"source": name, "result": {"error": str(e), "status": "error"}})

        return results

    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Estrae dati strutturati dal testo della risposta
        Cerca di identificare sezioni come dimensione mercato, trend, competitor, ecc.
        """
        structured_data = {
            "market_size": {},
            "trends": [],
            "competitors": [],
            "opportunities": [],
            "threats": [],
            "customer_segments": [],
            "sources": []
        }

        # Estrai dimensione del mercato (cerca valori numerici con € o euro e percentuali)
        market_size_pattern = r"(?:dimensione(?:\sdel)?\smercato|mercato\s(?:vale|stimato|di)).*?(?:€|euro|EUR|miliard[io]|milion[ie])[^\n\.]*?(?:\d+(?:,\d+)?(?:\.\d+)?%?|CAGR)"
        market_size_matches = re.finditer(market_size_pattern, text, re.IGNORECASE)
        for match in market_size_matches:
            market_size_text = match.group(0).strip()
            if market_size_text:
                structured_data["market_size"]["description"] = market_size_text
                # Cerca valori numerici
                value_pattern = r"(?:€|euro|EUR)\s*(\d+(?:[,.]\d+)?(?:\s*(?:miliard[io]|milion[ie]|mila)))"
                value_match = re.search(value_pattern, market_size_text, re.IGNORECASE)
                if value_match:
                    structured_data["market_size"]["value"] = value_match.group(1)
                # Cerca CAGR
                cagr_pattern = r"CAGR\s*(?:del)?\s*(\d+(?:[,.]\d+)?%)"
                cagr_match = re.search(cagr_pattern, market_size_text, re.IGNORECASE)
                if cagr_match:
                    structured_data["market_size"]["cagr"] = cagr_match.group(1)

        # Estrai trend (cerca elenchi puntati o numerati dopo la parola "trend")
        trends_section = re.search(r"(?:trend|tendenze).*?(?=\n\n|\n#|\Z)", text, re.IGNORECASE | re.DOTALL)
        if trends_section:
            trends_text = trends_section.group(0)
            # Cerca elementi di elenco (numerati o puntati)
            trend_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*)([^\n]+)", trends_text)
            for item in trend_items:
                if len(item.strip()) > 10:  # Ignora elementi troppo corti
                    structured_data["trends"].append({"description": item.strip()})

        # Estrai competitor
        competitors_section = re.search(r"(?:competitor|concorrenti).*?(?=\n\n|\n#|\Z)", text, re.IGNORECASE | re.DOTALL)
        if competitors_section:
            competitors_text = competitors_section.group(0)
            # Cerca nomi di aziende (spesso in grassetto o seguiti da descrizione)
            competitor_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^:]+)(?::|\s-\s)(.*?)(?=\n\s*(?:\d+\.|[*•-])|\Z)", competitors_text, re.DOTALL)
            for name, description in competitor_items:
                if len(name.strip()) > 2:  # Ignora elementi troppo corti
                    structured_data["competitors"].append({
                        "name": name.strip(),
                        "description": description.strip()
                    })

            # Se non trova con il pattern precedente, prova un pattern più semplice
            if not structured_data["competitors"]:
                competitor_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", competitors_text)
                for item in competitor_items:
                    if len(item.strip()) > 2:
                        structured_data["competitors"].append({
                            "name": item.strip(),
                            "description": ""
                        })

        # Estrai opportunità
        opportunities_section = re.search(r"(?:opportunità|opportunita).*?(?=\n\n|\n#|\Z)", text, re.IGNORECASE | re.DOTALL)
        if opportunities_section:
            opportunities_text = opportunities_section.group(0)
            opportunity_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", opportunities_text)
            for item in opportunity_items:
                if len(item.strip()) > 10:
                    structured_data["opportunities"].append({"description": item.strip()})

        # Estrai minacce/rischi
        threats_section = re.search(r"(?:minacce|rischi|sfide).*?(?=\n\n|\n#|\Z)", text, re.IGNORECASE | re.DOTALL)
        if threats_section:
            threats_text = threats_section.group(0)
            threat_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", threats_text)
            for item in threat_items:
                if len(item.strip()) > 10:
                    structured_data["threats"].append({"description": item.strip()})

        # Estrai fonti
        sources_section = re.search(r"(?:fonti|bibliografia|references|sources).*?(?=\n\n|\n#|\Z)", text, re.IGNORECASE | re.DOTALL)
        if sources_section:
            sources_text = sources_section.group(0)
            # Cerca URL o citazioni
            source_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", sources_text)
            for item in source_items:
                if len(item.strip()) > 5:
                    # Cerca URL nella fonte
                    url_match = re.search(r"https?://[^\s]+", item)
                    url = url_match.group(0) if url_match else ""
                    structured_data["sources"].append({
                        "description": item.strip(),
                        "url": url,
                        "topic": "Analisi di mercato"
                    })

        return structured_data

    def comprehensive_market_analysis(self, company_name: str, industry: str,
                                      target_market: str, region: str = "Italia",
                                      detailed: bool = True, use_cache: bool = True) -> Dict[str, Any]:
        """
        Esegue un'analisi di mercato completa e strutturata

        Args:
            company_name: Nome dell'azienda
            industry: Settore industriale
            target_market: Mercato target
            region: Regione geografica
            detailed: Se eseguire un'analisi dettagliata
            use_cache: Se utilizzare la cache per query identiche

        Returns:
            Un dizionario contenente l'analisi di mercato strutturata
        """
        # Verifica se il risultato è nella cache
        cache_key = f"market_{company_name}_{industry}_{target_market}_{region}_{detailed}"
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                print(f"Usando analisi di mercato in cache per: {company_name}, {industry}")
                return cache_entry["result"]

        search_functions = []

        # Aggiungi la funzione di ricerca Perplexity se disponibile
        if self.perplexity_available:
            search_functions.append((
                lambda: self.perplexity.market_research(company_name, industry, target_market, region, detailed),
                "Perplexity Market Research"
            ))

        # Esegui la ricerca
        if search_functions:
            raw_results = self._run_parallel_searches(search_functions)
        else:
            error_result = {
                "error": f"Perplexity API non disponibile. {self.last_error}",
                "market_size": {}, "trends": [], "opportunities": [], "threats": [],
                "sources": [],
                "api_status": {"status": "error"},
                "raw_text": ""
            }
            return error_result

        # Struttura per i risultati
        combined_results = {
            "market_size": {},
            "trends": [],
            "opportunities": [],
            "threats": [],
            "customer_segments": [],
            "competitors": [],
            "sources": [],
            "api_status": {},  # Stato API
            "raw_text": ""     # Testo completo per riferimento
        }

        # Elabora i risultati da Perplexity
        for result_data in raw_results:
            source = result_data["source"]
            result = result_data["result"]

            # Stato API
            if "error" in result:
                combined_results["api_status"][source] = result["error"]
                combined_results["api_status"]["status"] = "error"
            else:
                combined_results["api_status"][source] = "OK"
                combined_results["api_status"]["status"] = "success"

            if source == "Perplexity Market Research" and "status" in result and result["status"] == "success":
                # Estrai il testo completo
                full_text = result.get("extracted_text", "")
                combined_results["raw_text"] = full_text

                # Estrai dati strutturati dal testo
                structured_data = self._extract_structured_data(full_text)

                # Aggiorna i risultati combinati
                if structured_data["market_size"]:
                    combined_results["market_size"] = structured_data["market_size"]
                if structured_data["trends"]:
                    combined_results["trends"] = structured_data["trends"]
                if structured_data["competitors"]:
                    combined_results["competitors"] = structured_data["competitors"]
                if structured_data["opportunities"]:
                    combined_results["opportunities"] = structured_data["opportunities"]
                if structured_data["threats"]:
                    combined_results["threats"] = structured_data["threats"]
                if structured_data["sources"]:
                    combined_results["sources"] = structured_data["sources"]

        # Salva nella cache
        if use_cache and combined_results["api_status"].get("status") == "success":
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "result": combined_results
            }

        return combined_results

    def comprehensive_competitor_analysis(self, company_name: str, industry: str,
                                         target_market: str = "", competitors: Optional[List[str]] = None,
                                         use_cache: bool = True) -> Dict[str, Any]:
        """
        Esegue un'analisi competitiva dettagliata e strutturata

        Args:
            company_name: Nome dell'azienda
            industry: Settore industriale
            target_market: Mercato target (opzionale)
            competitors: Lista di competitor specifici da analizzare
            use_cache: Se utilizzare la cache per query identiche

        Returns:
            Un dizionario contenente l'analisi competitiva strutturata
        """
        # Verifica se il risultato è nella cache
        competitors_str = ",".join(sorted(competitors)) if competitors else "auto"
        cache_key = f"competitors_{company_name}_{industry}_{target_market}_{competitors_str}"
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                print(f"Usando analisi competitiva in cache per: {company_name}, {industry}")
                return cache_entry["result"]

        search_functions = []

        # Aggiungi la funzione di ricerca Perplexity se disponibile
        if self.perplexity_available:
            search_functions.append((
                lambda: self.perplexity.competitor_analysis(company_name, industry, competitors),
                "Perplexity Competitor Analysis"
            ))

        # Esegui la ricerca
        if search_functions:
            raw_results = self._run_parallel_searches(search_functions)
        else:
            error_result = {
                "error": f"Perplexity API non disponibile. {self.last_error}",
                "competitors": [],
                "positioning": {},
                "swot": {},
                "sources": [],
                "api_status": {"status": "error"},
                "raw_text": ""
            }
            return error_result

        # Struttura per i risultati
        combined_results = {
            "competitors": [],
            "positioning": {},
            "swot": {
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": []
            },
            "industry_leaders": [],
            "sources": [],
            "api_status": {},
            "raw_text": ""
        }

        # Elabora i risultati
        for result_data in raw_results:
            source = result_data["source"]
            result = result_data["result"]

            # Stato API
            if "error" in result:
                combined_results["api_status"][source] = result["error"]
                combined_results["api_status"]["status"] = "error"
            else:
                combined_results["api_status"][source] = "OK"
                combined_results["api_status"]["status"] = "success"

            if source == "Perplexity Competitor Analysis" and "status" in result and result["status"] == "success":
                # Estrai il testo completo
                full_text = result.get("extracted_text", "")
                combined_results["raw_text"] = full_text

                # Estrai dati strutturati dal testo
                structured_data = self._extract_structured_data(full_text)

                # Aggiorna i risultati combinati
                if structured_data["competitors"]:
                    combined_results["competitors"] = structured_data["competitors"]
                if structured_data["sources"]:
                    combined_results["sources"] = structured_data["sources"]

                # Estrai analisi SWOT se presente
                swot_section = re.search(r"(?:SWOT|analisi\s+SWOT).*?(?=\n\n|\n#|\Z)", full_text, re.IGNORECASE | re.DOTALL)
                if swot_section:
                    swot_text = swot_section.group(0)

                    # Cerca punti di forza
                    strengths = re.search(r"(?:punti\s+di\s+forza|strengths|forza).*?(?=\n\n|\n#|debol|weakn|\Z)", swot_text, re.IGNORECASE | re.DOTALL)
                    if strengths:
                        strength_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", strengths.group(0))
                        for item in strength_items:
                            if len(item.strip()) > 5:
                                combined_results["swot"]["strengths"].append({"description": item.strip()})

                    # Cerca debolezze
                    weaknesses = re.search(r"(?:punti\s+deboli|debolezze|weaknesses).*?(?=\n\n|\n#|opport|\Z)", swot_text, re.IGNORECASE | re.DOTALL)
                    if weaknesses:
                        weakness_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", weaknesses.group(0))
                        for item in weakness_items:
                            if len(item.strip()) > 5:
                                combined_results["swot"]["weaknesses"].append({"description": item.strip()})

        # Salva nella cache
        if use_cache and combined_results["api_status"].get("status") == "success":
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "result": combined_results
            }

        return combined_results

    def trend_analysis(self, industry: str, timeframe: str = "prossimi 3 anni",
                      use_cache: bool = True) -> Dict[str, Any]:
        """
        Analizza i trend di settore

        Args:
            industry: Settore industriale
            timeframe: Orizzonte temporale dell'analisi
            use_cache: Se utilizzare la cache per query identiche

        Returns:
            Un dizionario contenente l'analisi dei trend
        """
        # Verifica se il risultato è nella cache
        cache_key = f"trends_{industry}_{timeframe}"
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                print(f"Usando analisi trend in cache per: {industry}")
                return cache_entry["result"]

        if not self.perplexity_available:
            return {
                "error": f"Perplexity API non disponibile. {self.last_error}",
                "trends": [],
                "sources": [],
                "api_status": {"status": "error"},
                "raw_text": ""
            }

        # Esegui la ricerca
        result = self.perplexity.trend_analysis(industry, timeframe)

        # Struttura per i risultati
        trend_results = {
            "trends": [],
            "sources": [],
            "api_status": {},
            "raw_text": ""
        }

        # Stato API
        if "error" in result:
            trend_results["api_status"]["status"] = "error"
            trend_results["api_status"]["message"] = result["error"]
            return trend_results

        trend_results["api_status"]["status"] = "success"

        # Estrai il testo completo
        full_text = result.get("extracted_text", "")
        trend_results["raw_text"] = full_text

        # Estrai dati strutturati dal testo
        structured_data = self._extract_structured_data(full_text)

        # Aggiorna i risultati
        if structured_data["trends"]:
            trend_results["trends"] = structured_data["trends"]
        if structured_data["sources"]:
            trend_results["sources"] = structured_data["sources"]

        # Salva nella cache
        if use_cache and trend_results["api_status"].get("status") == "success":
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "result": trend_results
            }

        return trend_results

    def financial_analysis(self, company_name: str, industry: str, company_stage: str = "startup",
                          funding_needs: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        Esegue un'analisi finanziaria per un business plan

        Args:
            company_name: Nome dell'azienda
            industry: Settore industriale
            company_stage: Fase dell'azienda (startup, growth, mature)
            funding_needs: Necessità di finanziamento (opzionale)
            use_cache: Se utilizzare la cache per query identiche

        Returns:
            Un dizionario contenente l'analisi finanziaria strutturata
        """
        # Verifica se il risultato è nella cache
        cache_key = f"finance_{company_name}_{industry}_{company_stage}_{funding_needs}"
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                print(f"Usando analisi finanziaria in cache per: {company_name}, {industry}")
                return cache_entry["result"]

        if not self.perplexity_available:
            return {
                "error": f"Perplexity API non disponibile. {self.last_error}",
                "costs": [],
                "metrics": [],
                "projections": {},
                "funding": [],
                "risks": [],
                "sources": [],
                "api_status": {"status": "error"},
                "raw_text": ""
            }

        # Esegui la ricerca
        result = self.perplexity.financial_analysis(company_name, industry, company_stage, funding_needs)

        # Struttura per i risultati
        finance_results = {
            "costs": [],
            "metrics": [],
            "projections": {},
            "funding": [],
            "risks": [],
            "sources": [],
            "api_status": {},
            "raw_text": ""
        }

        # Stato API
        if "error" in result:
            finance_results["api_status"]["status"] = "error"
            finance_results["api_status"]["message"] = result["error"]
            return finance_results

        finance_results["api_status"]["status"] = "success"

        # Estrai il testo completo
        full_text = result.get("extracted_text", "")
        finance_results["raw_text"] = full_text

        # Estrai dati strutturati dal testo
        structured_data = self._extract_structured_data(full_text)

        # Estrai informazioni finanziarie specifiche
        # Estrai struttura dei costi
        costs_section = re.search(r"(?:struttura\s+dei\s+costi|costi\s+tipici).*?(?=\n\n|\n#|\Z)",
                                 full_text, re.IGNORECASE | re.DOTALL)
        if costs_section:
            costs_text = costs_section.group(0)
            cost_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", costs_text)
            for item in cost_items:
                if len(item.strip()) > 10:
                    finance_results["costs"].append({"description": item.strip()})

        # Estrai metriche finanziarie
        metrics_section = re.search(r"(?:metriche\s+finanziarie|KPI|indicatori\s+chiave).*?(?=\n\n|\n#|\Z)",
                                   full_text, re.IGNORECASE | re.DOTALL)
        if metrics_section:
            metrics_text = metrics_section.group(0)
            metric_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", metrics_text)
            for item in metric_items:
                if len(item.strip()) > 5:
                    finance_results["metrics"].append({"description": item.strip()})

        # Estrai fonti di finanziamento
        funding_section = re.search(r"(?:fonti\s+di\s+finanziamento|finanziamento).*?(?=\n\n|\n#|\Z)",
                                   full_text, re.IGNORECASE | re.DOTALL)
        if funding_section:
            funding_text = funding_section.group(0)
            funding_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", funding_text)
            for item in funding_items:
                if len(item.strip()) > 5:
                    finance_results["funding"].append({"description": item.strip()})

        # Estrai rischi finanziari
        risks_section = re.search(r"(?:rischi\s+finanziari|rischi).*?(?=\n\n|\n#|\Z)",
                                 full_text, re.IGNORECASE | re.DOTALL)
        if risks_section:
            risks_text = risks_section.group(0)
            risk_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", risks_text)
            for item in risk_items:
                if len(item.strip()) > 5:
                    finance_results["risks"].append({"description": item.strip()})

        # Aggiungi fonti
        if structured_data["sources"]:
            finance_results["sources"] = structured_data["sources"]

        # Salva nella cache
        if use_cache and finance_results["api_status"].get("status") == "success":
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "result": finance_results
            }

        return finance_results

    def marketing_strategy_analysis(self, company_name: str, industry: str, target_market: str,
                                   products: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """
        Esegue un'analisi della strategia di marketing

        Args:
            company_name: Nome dell'azienda
            industry: Settore industriale
            target_market: Mercato target
            products: Prodotti/servizi offerti (opzionale)
            use_cache: Se utilizzare la cache per query identiche

        Returns:
            Un dizionario contenente l'analisi di marketing strutturata
        """
        # Verifica se il risultato è nella cache
        products_key = products or "none"
        cache_key = f"marketing_{company_name}_{industry}_{target_market}_{products_key}"
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                print(f"Usando analisi marketing in cache per: {company_name}, {industry}")
                return cache_entry["result"]

        if not self.perplexity_available:
            return {
                "error": f"Perplexity API non disponibile. {self.last_error}",
                "channels": [],
                "pricing": [],
                "positioning": [],
                "acquisition": [],
                "metrics": [],
                "budget": {},
                "sources": [],
                "api_status": {"status": "error"},
                "raw_text": ""
            }

        # Esegui la ricerca
        result = self.perplexity.marketing_strategy(company_name, industry, target_market, products)

        # Struttura per i risultati
        marketing_results = {
            "channels": [],
            "pricing": [],
            "positioning": [],
            "acquisition": [],
            "metrics": [],
            "budget": {},
            "sources": [],
            "api_status": {},
            "raw_text": ""
        }

        # Stato API
        if "error" in result:
            marketing_results["api_status"]["status"] = "error"
            marketing_results["api_status"]["message"] = result["error"]
            return marketing_results

        marketing_results["api_status"]["status"] = "success"

        # Estrai il testo completo
        full_text = result.get("extracted_text", "")
        marketing_results["raw_text"] = full_text

        # Estrai dati strutturati dal testo
        structured_data = self._extract_structured_data(full_text)

        # Estrai informazioni di marketing specifiche
        # Estrai canali di marketing
        channels_section = re.search(r"(?:canali\s+di\s+marketing|canali).*?(?=\n\n|\n#|\Z)",
                                    full_text, re.IGNORECASE | re.DOTALL)
        if channels_section:
            channels_text = channels_section.group(0)
            channel_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", channels_text)
            for item in channel_items:
                if len(item.strip()) > 5:
                    marketing_results["channels"].append({"description": item.strip()})

        # Estrai strategie di pricing
        pricing_section = re.search(r"(?:strategie\s+di\s+pricing|pricing|prezzi).*?(?=\n\n|\n#|\Z)",
                                   full_text, re.IGNORECASE | re.DOTALL)
        if pricing_section:
            pricing_text = pricing_section.group(0)
            pricing_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", pricing_text)
            for item in pricing_items:
                if len(item.strip()) > 5:
                    marketing_results["pricing"].append({"description": item.strip()})

        # Estrai strategie di posizionamento
        positioning_section = re.search(r"(?:posizionamento|positioning).*?(?=\n\n|\n#|\Z)",
                                       full_text, re.IGNORECASE | re.DOTALL)
        if positioning_section:
            positioning_text = positioning_section.group(0)
            positioning_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", positioning_text)
            for item in positioning_items:
                if len(item.strip()) > 5:
                    marketing_results["positioning"].append({"description": item.strip()})

        # Estrai tattiche di acquisizione clienti
        acquisition_section = re.search(r"(?:acquisizione\s+clienti|customer\s+acquisition).*?(?=\n\n|\n#|\Z)",
                                       full_text, re.IGNORECASE | re.DOTALL)
        if acquisition_section:
            acquisition_text = acquisition_section.group(0)
            acquisition_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", acquisition_text)
            for item in acquisition_items:
                if len(item.strip()) > 5:
                    marketing_results["acquisition"].append({"description": item.strip()})

        # Estrai budget di marketing
        budget_section = re.search(r"(?:budget\s+di\s+marketing|budget).*?(?=\n\n|\n#|\Z)",
                                  full_text, re.IGNORECASE | re.DOTALL)
        if budget_section:
            budget_text = budget_section.group(0)
            # Cerca percentuali
            percentage_match = re.search(r"(\d+(?:[,.]\d+)?%)", budget_text)
            if percentage_match:
                marketing_results["budget"]["percentage"] = percentage_match.group(1)
            # Cerca valori assoluti
            value_match = re.search(r"(?:€|euro|EUR)\s*(\d+(?:[,.]\d+)?(?:\s*(?:mila|k|mln|milion[ie])))", budget_text, re.IGNORECASE)
            if value_match:
                marketing_results["budget"]["value"] = value_match.group(1)
            # Aggiungi descrizione completa
            marketing_results["budget"]["description"] = budget_text.strip()

        # Aggiungi fonti
        if structured_data["sources"]:
            marketing_results["sources"] = structured_data["sources"]

        # Salva nella cache
        if use_cache and marketing_results["api_status"].get("status") == "success":
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "result": marketing_results
            }

        return marketing_results

    def operational_plan_analysis(self, company_name: str, industry: str, company_size: str = "piccola",
                                 location: str = "Italia", use_cache: bool = True) -> Dict[str, Any]:
        """
        Esegue un'analisi del piano operativo

        Args:
            company_name: Nome dell'azienda
            industry: Settore industriale
            company_size: Dimensione dell'azienda (piccola, media, grande)
            location: Localizzazione geografica
            use_cache: Se utilizzare la cache per query identiche

        Returns:
            Un dizionario contenente l'analisi operativa strutturata
        """
        # Verifica se il risultato è nella cache
        cache_key = f"operations_{company_name}_{industry}_{company_size}_{location}"
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                print(f"Usando analisi operativa in cache per: {company_name}, {industry}")
                return cache_entry["result"]

        if not self.perplexity_available:
            return {
                "error": f"Perplexity API non disponibile. {self.last_error}",
                "structure": [],
                "processes": [],
                "resources": [],
                "partners": [],
                "technologies": [],
                "metrics": [],
                "sources": [],
                "api_status": {"status": "error"},
                "raw_text": ""
            }

        # Esegui la ricerca
        result = self.perplexity.operational_plan(company_name, industry, company_size, location)

        # Struttura per i risultati
        operations_results = {
            "structure": [],
            "processes": [],
            "resources": [],
            "partners": [],
            "technologies": [],
            "metrics": [],
            "sources": [],
            "api_status": {},
            "raw_text": ""
        }

        # Stato API
        if "error" in result:
            operations_results["api_status"]["status"] = "error"
            operations_results["api_status"]["message"] = result["error"]
            return operations_results

        operations_results["api_status"]["status"] = "success"

        # Estrai il testo completo
        full_text = result.get("extracted_text", "")
        operations_results["raw_text"] = full_text

        # Estrai dati strutturati dal testo
        structured_data = self._extract_structured_data(full_text)

        # Estrai informazioni operative specifiche
        # Estrai struttura organizzativa
        structure_section = re.search(r"(?:struttura\s+organizzativa|organizzazione).*?(?=\n\n|\n#|\Z)",
                                     full_text, re.IGNORECASE | re.DOTALL)
        if structure_section:
            structure_text = structure_section.group(0)
            structure_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", structure_text)
            for item in structure_items:
                if len(item.strip()) > 5:
                    operations_results["structure"].append({"description": item.strip()})

        # Estrai processi operativi
        processes_section = re.search(r"(?:processi\s+operativi|processi\s+chiave).*?(?=\n\n|\n#|\Z)",
                                     full_text, re.IGNORECASE | re.DOTALL)
        if processes_section:
            processes_text = processes_section.group(0)
            process_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", processes_text)
            for item in process_items:
                if len(item.strip()) > 5:
                    operations_results["processes"].append({"description": item.strip()})

        # Estrai risorse necessarie
        resources_section = re.search(r"(?:risorse\s+necessarie|risorse).*?(?=\n\n|\n#|\Z)",
                                     full_text, re.IGNORECASE | re.DOTALL)
        if resources_section:
            resources_text = resources_section.group(0)
            resource_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", resources_text)
            for item in resource_items:
                if len(item.strip()) > 5:
                    operations_results["resources"].append({"description": item.strip()})

        # Estrai fornitori e partner
        partners_section = re.search(r"(?:fornitori|partner).*?(?=\n\n|\n#|\Z)",
                                    full_text, re.IGNORECASE | re.DOTALL)
        if partners_section:
            partners_text = partners_section.group(0)
            partner_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", partners_text)
            for item in partner_items:
                if len(item.strip()) > 5:
                    operations_results["partners"].append({"description": item.strip()})

        # Estrai tecnologie
        tech_section = re.search(r"(?:tecnologie|sistemi\s+informativi).*?(?=\n\n|\n#|\Z)",
                               full_text, re.IGNORECASE | re.DOTALL)
        if tech_section:
            tech_text = tech_section.group(0)
            tech_items = re.findall(r"(?:^|\n)(?:\d+\.\s*|\*\s*|-\s*|•\s*)([^\n]+)", tech_text)
            for item in tech_items:
                if len(item.strip()) > 5:
                    operations_results["technologies"].append({"description": item.strip()})

        # Aggiungi fonti
        if structured_data["sources"]:
            operations_results["sources"] = structured_data["sources"]

        # Salva nella cache
        if use_cache and operations_results["api_status"].get("status") == "success":
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "result": operations_results
            }

        return operations_results
