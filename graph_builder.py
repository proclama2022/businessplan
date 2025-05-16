#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Costruttore del grafo LangGraph per il Business Plan Builder

Questo modulo definisce la struttura del grafo LangGraph che orchestrerà i vari nodi
e il flusso di lavoro del sistema, permettendo la gestione di documenti lunghi e complessi.
"""

import os
import json
from typing import Dict, Any, List, Tuple, Callable, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from database.vector_store import VectorDatabase
from state import BusinessPlanState
from config import Config
from search.combined_search import CombinedSearch
from search.perplexity import PerplexitySearch # Assicurati che sia importato
# Funzioni dei nodi a livello di modulo

def initial_planning(state: BusinessPlanState) -> Dict[str, Any]:
    print("DEBUG: initial_planning chiamata con stato:", state)
    print("DEBUG: Utilizzo OpenAI per la generazione")
    
    # Inizializza OpenAI
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
    print("DEBUG: ChatOpenAI costruito")

    # Ottieni il contesto dai documenti
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"\n\n---\nDocumenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---\n" if doc_context else ""

    # Ottieni il contesto dalle sezioni precedenti
    previous_sections = state.get("previous_sections", "")
    previous_sections_context = f"\n\n---\nSezioni precedenti del business plan:\n{previous_sections}\n---\n" if previous_sections else ""

    # Ottieni le istruzioni di modifica e il testo originale
    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")

    # Ottieni i risultati della ricerca online
    online_search_enabled = state.get("online_search_enabled", False)
    perplexity_results = state.get("perplexity_results")

    search_section = ""
    if online_search_enabled and perplexity_results:
        search_section = f"""\
\n---
Informazioni aggiuntive dalla ricerca online (Perplexity):
---
{perplexity_results}
---
Utilizza queste informazioni per arricchire la sezione.
"""

    if edit_instructions and original_text:
        print("DEBUG: initial_planning in modalità revisione, edit_instructions:", edit_instructions)
        print("DEBUG: original_text:", original_text)
        # Prompt for revision
        prompt_template = f"""
        Sei un esperto consulente di business plan. Rivedi il seguente testo della sezione 'Pianificazione Iniziale' per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni sull'azienda:
        - Nome: {{company_name}}
        - Titolo del documento: {{document_title}}
        - Data di creazione: {{creation_date}}
        - Versione: {{version}}
        {doc_section}
        {previous_sections_context}
        {search_section}

        Restituisci solo il testo rivisto della sezione 'Pianificazione Iniziale'.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        prompt_str = prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name"),
            document_title=state.get("document_title"),
            creation_date=state.get("creation_date"),
            version=state.get("version")
        )
        print("DEBUG: prompt inviato a LLM (revisione):", prompt_str)
        try:
            # Usa OpenAI per la generazione
            response = llm.invoke(prompt_str)
            print("DEBUG: risposta OpenAI (revisione):", response)
        except Exception as e:
            print("ERRORE LLM (revisione):", e)
            response = {"role": "assistant", "content": f"Errore nella generazione: {e}"}
    else:
        # Prompt for initial generation
        prompt_template = f"""
        Sei un esperto consulente di business plan. Stai aiutando a creare un business plan completo per l'azienda {{company_name}}.

        Basandoti sulle informazioni disponibili, analizza e pianifica la struttura del business plan.

        Informazioni sull'azienda:
        - Nome: {{company_name}}
        - Titolo del documento: {{document_title}}
        - Data di creazione: {{creation_date}}
        - Versione: {{version}}

        Struttura attuale del business plan:
        {{outline}}
        {doc_section}
        {previous_sections_context}
        {search_section}

        Fornisci una valutazione iniziale e suggerimenti per migliorare la struttura del business plan.
        Identifica le sezioni prioritarie che dovrebbero essere sviluppate per prime.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        outline_str = "\n".join([f"- {section}:\n  " + "\n  ".join([f"- {subsection}" for subsection in subsections])
                            for section, subsections in state.get("outline", {}).items()])
        prompt_str = prompt.format(
            company_name=state.get("company_name"),
            document_title=state.get("document_title"),
            creation_date=state.get("creation_date"),
            version=state.get("version"),
            outline=outline_str
        )
        print("DEBUG: prompt inviato a LLM (generazione):", prompt_str)
        try:
            # Usa OpenAI per la generazione
            response = llm.invoke(prompt_str)
            print("DEBUG: risposta OpenAI (generazione):", response)
        except Exception as e:
            print("ERRORE LLM (generazione):", e)
            response = {"role": "assistant", "content": f"Errore nella generazione: {e}"}
    # Ensure response is a dict with role/content
    print("DEBUG: prima del return finale di initial_planning")
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        # Handle cases where response might be AIMessage or similar
        try:
            content = response.content if hasattr(response, 'content') else str(response)
            response = {"role": "assistant", "content": content}
        except Exception:
             response = {"role": "assistant", "content": str(response)}

    print("DEBUG: return finale di initial_planning:", response)
    return {"messages": [response]}

def executive_summary(state: BusinessPlanState) -> Dict[str, Any]:
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)

    # Ottieni il contesto dai documenti
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"\n\n---\nDocumenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---\n" if doc_context else ""

    # Ottieni il contesto dalle sezioni precedenti
    previous_sections = state.get("previous_sections", "")
    previous_sections_context = f"\n\n---\nSezioni precedenti del business plan:\n{previous_sections}\n---\n" if previous_sections else ""

    # Ottieni le istruzioni di modifica e il testo originale
    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")

    # Ottieni i risultati della ricerca online
    online_search_enabled = state.get("online_search_enabled", False)
    perplexity_results = state.get("perplexity_results")

    search_section = ""
    if online_search_enabled and perplexity_results:
        # Estrai il testo dai risultati di Perplexity in base al formato
        perplexity_text = ""
        if isinstance(perplexity_results, dict):
            # Se è un dizionario, cerca prima il testo grezzo
            if "raw_text" in perplexity_results:
                perplexity_text = perplexity_results["raw_text"]
            # Altrimenti, cerca altre chiavi comuni
            elif "extracted_text" in perplexity_results:
                perplexity_text = perplexity_results["extracted_text"]
            elif "choices" in perplexity_results and len(perplexity_results["choices"]) > 0:
                if isinstance(perplexity_results["choices"][0], dict) and "message" in perplexity_results["choices"][0]:
                    perplexity_text = perplexity_results["choices"][0]["message"].get("content", "")
            # Se non troviamo testo, proviamo a convertire l'intero dizionario in testo
            else:
                try:
                    # Estrai solo le sezioni più rilevanti per il sommario esecutivo
                    summary_info = []

                    # Informazioni sull'azienda
                    if "company_info" in perplexity_results and perplexity_results["company_info"]:
                        info = perplexity_results["company_info"]
                        info_text = "Informazioni sull'azienda:\n"
                        if isinstance(info, dict):
                            for key, value in info.items():
                                info_text += f"- {key}: {value}\n"
                        else:
                            info_text += str(info)
                        summary_info.append(info_text)

                    # Mercato
                    if "market_size" in perplexity_results and perplexity_results["market_size"]:
                        market_size = perplexity_results["market_size"]
                        market_text = "Mercato:\n"
                        if isinstance(market_size, dict):
                            if "description" in market_size:
                                market_text += f"- Dimensione: {market_size['description']}\n"
                            elif "value" in market_size:
                                market_text += f"- Dimensione: {market_size['value']}\n"
                            if "cagr" in market_size:
                                market_text += f"- CAGR: {market_size['cagr']}\n"
                        else:
                            market_text += f"- {market_size}\n"
                        summary_info.append(market_text)

                    # Competitor
                    if "competitors" in perplexity_results and perplexity_results["competitors"]:
                        competitors = perplexity_results["competitors"]
                        competitors_text = "Competitor principali:\n"
                        for i, comp in enumerate(competitors[:3]):  # Limita a 3 competitor per il sommario
                            if isinstance(comp, dict):
                                name = comp.get("name", f"Competitor {i+1}")
                                desc = comp.get("description", "")
                                competitors_text += f"- {name}: {desc}\n"
                            else:
                                competitors_text += f"- {comp}\n"
                        summary_info.append(competitors_text)

                    # Proiezioni finanziarie
                    if "financial_projections" in perplexity_results and perplexity_results["financial_projections"]:
                        projections = perplexity_results["financial_projections"]
                        projections_text = "Proiezioni finanziarie (sintesi):\n"
                        if isinstance(projections, dict):
                            for year, data in list(projections.items())[:2]:  # Limita a 2 anni per il sommario
                                projections_text += f"- Anno {year}: "
                                if isinstance(data, dict):
                                    if "revenue" in data:
                                        projections_text += f"Ricavi: {data['revenue']}, "
                                    if "profit" in data:
                                        projections_text += f"Profitto: {data['profit']}"
                                    projections_text += "\n"
                                else:
                                    projections_text += f"{data}\n"
                        elif isinstance(projections, list) and len(projections) > 0:
                            for item in projections[:2]:  # Limita a 2 anni per il sommario
                                if isinstance(item, dict):
                                    year = item.get("year", "")
                                    revenue = item.get("revenue", "")
                                    profit = item.get("profit", "")
                                    projections_text += f"- Anno {year}: Ricavi: {revenue}, Profitto: {profit}\n"
                                else:
                                    projections_text += f"- {item}\n"
                        else:
                            projections_text += str(projections)
                        summary_info.append(projections_text)

                    # Fonti
                    if "sources" in perplexity_results and perplexity_results["sources"]:
                        sources = perplexity_results["sources"]
                        sources_text = "Fonti:\n"
                        for i, source in enumerate(sources[:3]):  # Limita a 3 fonti per il sommario
                            if isinstance(source, dict) and "url" in source:
                                sources_text += f"- {source.get('title', 'Fonte ' + str(i+1))}: {source['url']}\n"
                            else:
                                sources_text += f"- {source}\n"
                        summary_info.append(sources_text)

                    # Unisci tutte le sezioni
                    perplexity_text = "\n\n".join(summary_info)

                    # Se non abbiamo estratto nulla, usa il dizionario completo come fallback
                    if not perplexity_text:
                        perplexity_text = json.dumps(perplexity_results, indent=2, ensure_ascii=False)
                except Exception as e:
                    perplexity_text = f"Errore nell'elaborazione dei risultati: {str(e)}\n{str(perplexity_results)}"
        else:
            # Se non è un dizionario, converti direttamente in stringa
            perplexity_text = str(perplexity_results)

        search_section = f"""\
\n---
Informazioni aggiuntive dalla ricerca online (Perplexity):
---
{perplexity_text}
---
Utilizza queste informazioni per arricchire la sezione.
"""

    if edit_instructions and original_text:
        prompt_template = f"""
        Rivedi il seguente Sommario Esecutivo per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni sull'azienda:
        - Settore: {{business_sector}}
        - Descrizione: {{company_description}}
        - Anno fondazione: {{year_founded}}
        - Dipendenti: {{num_employees}}
        - Prodotti/servizi: {{main_products}}
        - Mercato target: {{target_market}}
        - Area geografica: {{area}}
        - Obiettivi: {{plan_objectives}}
        - Orizzonte temporale: {{time_horizon}}
        - Necessità di finanziamento: {{funding_needs}}
        {doc_section}
        {previous_sections_context}
        {search_section}

        Restituisci solo il testo rivisto del Sommario Esecutivo.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            company_description=state.get("company_description"),
            year_founded=state.get("year_founded"),
            num_employees=state.get("num_employees"),
            main_products=state.get("main_products"),
            target_market=state.get("target_market"),
            area=state.get("area"),
            plan_objectives=state.get("plan_objectives"),
            time_horizon=state.get("time_horizon"),
            funding_needs=state.get("funding_needs")
        ))
    else:
        prompt_template = f"""
        Sei un esperto consulente di business plan. Scrivi un Sommario Esecutivo conciso e convincente per {{company_name}}.

        Informazioni sull'azienda:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Descrizione: {{company_description}}
        - Anno fondazione: {{year_founded}}
        - Dipendenti: {{num_employees}}
        - Prodotti/servizi principali: {{main_products}}
        - Mercato target: {{target_market}}
        - Area geografica di operatività: {{area}}
        - Obiettivi principali del piano: {{plan_objectives}}
        - Orizzonte temporale del piano: {{time_horizon}}
        - Eventuali necessità di finanziamento: {{funding_needs}}
        {doc_section}
        {previous_sections_context}
        {search_section}

        Includi i punti chiave dell'azienda, la sua missione, i prodotti/servizi, il mercato target e le proiezioni finanziarie principali (se disponibili).
        Restituisci solo il testo del Sommario Esecutivo.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            company_description=state.get("company_description"),
            year_founded=state.get("year_founded"),
            num_employees=state.get("num_employees"),
            main_products=state.get("main_products"),
            target_market=state.get("target_market"),
            area=state.get("area"),
            plan_objectives=state.get("plan_objectives"),
            time_horizon=state.get("time_horizon"),
            funding_needs=state.get("funding_needs")
        ))

    # Ensure response is a dict with role/content
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        # Handle cases where response might be AIMessage or similar
        try:
            content = response.content if hasattr(response, 'content') else str(response)
            response = {"role": "assistant", "content": content}
        except Exception:
             response = {"role": "assistant", "content": str(response)}

    return {"messages": [response]}

def market_analysis(state: BusinessPlanState) -> Dict[str, Any]:
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"\n\n---\nDocumenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---\n" if doc_context else ""

    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")
    online_search_enabled = state.get("online_search_enabled", False)
    perplexity_results = state.get("perplexity_results")

    search_section = ""
    if online_search_enabled and perplexity_results:
        # Estrai il testo dai risultati di Perplexity in base al formato
        perplexity_text = ""
        if isinstance(perplexity_results, dict):
            # Se è un dizionario, cerca prima il testo grezzo
            if "raw_text" in perplexity_results:
                perplexity_text = perplexity_results["raw_text"]
            # Altrimenti, cerca altre chiavi comuni
            elif "extracted_text" in perplexity_results:
                perplexity_text = perplexity_results["extracted_text"]
            elif "choices" in perplexity_results and len(perplexity_results["choices"]) > 0:
                if isinstance(perplexity_results["choices"][0], dict) and "message" in perplexity_results["choices"][0]:
                    perplexity_text = perplexity_results["choices"][0]["message"].get("content", "")
            # Se non troviamo testo, proviamo a convertire l'intero dizionario in testo
            else:
                try:
                    # Estrai solo le sezioni più rilevanti per l'analisi di mercato
                    market_info = []

                    # Dimensione del mercato
                    if "market_size" in perplexity_results and perplexity_results["market_size"]:
                        market_size = perplexity_results["market_size"]
                        market_size_text = "Dimensione del mercato: "
                        if isinstance(market_size, dict):
                            if "description" in market_size:
                                market_size_text += market_size["description"]
                            elif "value" in market_size:
                                market_size_text += f"Valore: {market_size['value']}"
                            if "cagr" in market_size:
                                market_size_text += f", CAGR: {market_size['cagr']}"
                        else:
                            market_size_text += str(market_size)
                        market_info.append(market_size_text)

                    # Trend
                    if "trends" in perplexity_results and perplexity_results["trends"]:
                        trends = perplexity_results["trends"]
                        trends_text = "Trend principali:\n"
                        for i, trend in enumerate(trends):
                            if isinstance(trend, dict) and "description" in trend:
                                trends_text += f"- {trend['description']}\n"
                            else:
                                trends_text += f"- {trend}\n"
                        market_info.append(trends_text)

                    # Competitor
                    if "competitors" in perplexity_results and perplexity_results["competitors"]:
                        competitors = perplexity_results["competitors"]
                        competitors_text = "Competitor principali:\n"
                        for i, comp in enumerate(competitors):
                            if isinstance(comp, dict):
                                name = comp.get("name", f"Competitor {i+1}")
                                desc = comp.get("description", "")
                                competitors_text += f"- {name}: {desc}\n"
                            else:
                                competitors_text += f"- {comp}\n"
                        market_info.append(competitors_text)

                    # Opportunità
                    if "opportunities" in perplexity_results and perplexity_results["opportunities"]:
                        opportunities = perplexity_results["opportunities"]
                        opportunities_text = "Opportunità di crescita:\n"
                        for i, opp in enumerate(opportunities):
                            if isinstance(opp, dict) and "description" in opp:
                                opportunities_text += f"- {opp['description']}\n"
                            else:
                                opportunities_text += f"- {opp}\n"
                        market_info.append(opportunities_text)

                    # Minacce
                    if "threats" in perplexity_results and perplexity_results["threats"]:
                        threats = perplexity_results["threats"]
                        threats_text = "Rischi e sfide:\n"
                        for i, threat in enumerate(threats):
                            if isinstance(threat, dict) and "description" in threat:
                                threats_text += f"- {threat['description']}\n"
                            else:
                                threats_text += f"- {threat}\n"
                        market_info.append(threats_text)

                    # Fonti
                    if "sources" in perplexity_results and perplexity_results["sources"]:
                        sources = perplexity_results["sources"]
                        sources_text = "Fonti:\n"
                        for i, source in enumerate(sources):
                            if isinstance(source, dict) and "url" in source:
                                sources_text += f"- {source.get('title', 'Fonte ' + str(i+1))}: {source['url']}\n"
                            else:
                                sources_text += f"- {source}\n"
                        market_info.append(sources_text)

                    # Unisci tutte le sezioni
                    perplexity_text = "\n\n".join(market_info)

                    # Se non abbiamo estratto nulla, usa il dizionario completo come fallback
                    if not perplexity_text:
                        perplexity_text = json.dumps(perplexity_results, indent=2, ensure_ascii=False)
                except Exception as e:
                    perplexity_text = f"Errore nell'elaborazione dei risultati: {str(e)}\n{str(perplexity_results)}"
        else:
            # Se non è un dizionario, converti direttamente in stringa
            perplexity_text = str(perplexity_results)

        search_section = f"""\
\n---
Informazioni aggiuntive dalla ricerca online (Perplexity):
---
{perplexity_text}
---
Utilizza queste informazioni per arricchire la sezione.
"""

    if edit_instructions and original_text:
        prompt_template = f"""
        Rivedi la seguente Analisi di Mercato per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni rilevanti:
        - Settore: {{business_sector}}
        - Mercato target: {{target_market}}
        - Area geografica: {{area}}
        - Prodotti/servizi: {{main_products}}
        {doc_section}
        {search_section} # Aggiunta dei risultati di ricerca
        Restituisci solo il testo rivisto dell'Analisi di Mercato.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            target_market=state.get("target_market"),
            area=state.get("area"),
            main_products=state.get("main_products")
        ))
    else:
        prompt_template = f"""
        Sei un esperto analista di mercato. Scrivi un'Analisi di Mercato dettagliata per {{company_name}}.

        Informazioni rilevanti:
        - Nome azienda: {{company_name}}
        - Settore: {{business_sector}}
        - Mercato target: {{target_market}}
        - Area geografica di operatività: {{area}}
        - Prodotti/servizi principali: {{main_products}}
        {doc_section}
        {search_section} # Aggiunta dei risultati di ricerca
        Analizza la dimensione del mercato, i trend, le opportunità, le minacce (analisi SWOT se pertinente) e il pubblico target.
        Restituisci solo il testo dell'Analisi di Mercato.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            target_market=state.get("target_market"),
            area=state.get("area"),
            main_products=state.get("main_products")
        ))

    # Ensure response is a dict with role/content
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        try:
            content = response.content if hasattr(response, 'content') else str(response)
            response = {"role": "assistant", "content": content}
        except Exception:
             response = {"role": "assistant", "content": str(response)}

    return {"messages": [response]}

def competitor_analysis(state: BusinessPlanState) -> Dict[str, Any]:
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"""\n\n---
Documenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---
""" if doc_context else ""

    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")
    online_search_enabled = state.get("online_search_enabled", False)
    perplexity_results = state.get("perplexity_results")

    search_section = ""
    if online_search_enabled and perplexity_results:
        # Estrai il testo dai risultati di Perplexity in base al formato
        perplexity_text = ""
        if isinstance(perplexity_results, dict):
            # Se è un dizionario, cerca prima il testo grezzo
            if "raw_text" in perplexity_results:
                perplexity_text = perplexity_results["raw_text"]
            # Altrimenti, cerca altre chiavi comuni
            elif "extracted_text" in perplexity_results:
                perplexity_text = perplexity_results["extracted_text"]
            elif "choices" in perplexity_results and len(perplexity_results["choices"]) > 0:
                if isinstance(perplexity_results["choices"][0], dict) and "message" in perplexity_results["choices"][0]:
                    perplexity_text = perplexity_results["choices"][0]["message"].get("content", "")
            # Se non troviamo testo, proviamo a convertire l'intero dizionario in testo
            else:
                try:
                    # Estrai solo le sezioni più rilevanti per l'analisi competitiva
                    competitor_info = []

                    # Competitor
                    if "competitors" in perplexity_results and perplexity_results["competitors"]:
                        competitors = perplexity_results["competitors"]
                        competitors_text = "Competitor principali:\n"
                        for i, comp in enumerate(competitors):
                            if isinstance(comp, dict):
                                name = comp.get("name", f"Competitor {i+1}")
                                desc = comp.get("description", "")
                                competitors_text += f"- {name}: {desc}\n"
                            else:
                                competitors_text += f"- {comp}\n"
                        competitor_info.append(competitors_text)

                    # SWOT
                    if "swot" in perplexity_results and perplexity_results["swot"]:
                        swot = perplexity_results["swot"]
                        swot_text = "Analisi SWOT:\n"

                        if isinstance(swot, dict):
                            if "strengths" in swot and swot["strengths"]:
                                swot_text += "\nPunti di Forza:\n"
                                for s in swot["strengths"]:
                                    swot_text += f"- {s}\n"

                            if "weaknesses" in swot and swot["weaknesses"]:
                                swot_text += "\nPunti Deboli:\n"
                                for w in swot["weaknesses"]:
                                    swot_text += f"- {w}\n"

                            if "opportunities" in swot and swot["opportunities"]:
                                swot_text += "\nOpportunità:\n"
                                for o in swot["opportunities"]:
                                    swot_text += f"- {o}\n"

                            if "threats" in swot and swot["threats"]:
                                swot_text += "\nMinacce:\n"
                                for t in swot["threats"]:
                                    swot_text += f"- {t}\n"

                        competitor_info.append(swot_text)

                    # Fonti
                    if "sources" in perplexity_results and perplexity_results["sources"]:
                        sources = perplexity_results["sources"]
                        sources_text = "Fonti:\n"
                        for i, source in enumerate(sources):
                            if isinstance(source, dict) and "url" in source:
                                sources_text += f"- {source.get('title', 'Fonte ' + str(i+1))}: {source['url']}\n"
                            else:
                                sources_text += f"- {source}\n"
                        competitor_info.append(sources_text)

                    # Unisci tutte le sezioni
                    perplexity_text = "\n\n".join(competitor_info)

                    # Se non abbiamo estratto nulla, usa il dizionario completo come fallback
                    if not perplexity_text:
                        perplexity_text = json.dumps(perplexity_results, indent=2, ensure_ascii=False)
                except Exception as e:
                    perplexity_text = f"Errore nell'elaborazione dei risultati: {str(e)}\n{str(perplexity_results)}"
        else:
            # Se non è un dizionario, converti direttamente in stringa
            perplexity_text = str(perplexity_results)

        search_section = f"""\
\n---
Informazioni aggiuntive dalla ricerca online (Perplexity):
---
{perplexity_text}
---
Utilizza queste informazioni per arricchire la sezione.
"""

    if edit_instructions and original_text:
        prompt_template = f"""
        Rivedi la seguente Analisi Competitiva per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni rilevanti:
        - Settore: {{business_sector}}
        - Mercato target: {{target_market}}
        - Principali concorrenti (se noti): {{competitors}}
        {doc_section}
        {search_section} # Aggiunta dei risultati di ricerca
        Restituisci solo il testo rivisto dell'Analisi Competitiva.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            target_market=state.get("target_market"),
            competitors=state.get("competitors", "Non specificati") # Aggiungi campo competitors allo stato se necessario
        ))
    else:
        prompt_template = f"""
        Sei un esperto analista di mercato. Scrivi un'Analisi Competitiva dettagliata per {{company_name}}.

        Informazioni rilevanti:
        - Nome azienda: {{company_name}}
        - Settore: {{business_sector}}
        - Mercato target: {{target_market}}
        - Principali concorrenti (se noti): {{competitors}}
        {doc_section}
        {search_section} # Aggiunta dei risultati di ricerca
        Identifica i principali concorrenti diretti e indiretti. Analizza i loro punti di forza, debolezza, strategie di prezzo, quote di mercato (se disponibili) e posizionamento.
        Descrivi il vantaggio competitivo di {{company_name}}.
        Restituisci solo il testo dell'Analisi Competitiva.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            target_market=state.get("target_market"),
            competitors=state.get("competitors", "Non specificati")
        ))

    # Ensure response is a dict with role/content
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        try:
            content = response.content if hasattr(response, 'content') else str(response)
            response = {"role": "assistant", "content": content}
        except Exception:
             response = {"role": "assistant", "content": str(response)}

    return {"messages": [response]}

def financial_plan(state: BusinessPlanState) -> Dict[str, Any]:
    """
    Genera il piano finanziario per il business plan.

    Questa funzione utilizza il modulo finanziario per generare il piano finanziario
    se sono disponibili dati finanziari importati, altrimenti utilizza il modello LLM.

    Args:
        state: Stato del business plan

    Returns:
        Dict[str, Any]: Messaggio con il piano finanziario
    """
    import streamlit as st

    # Verifica se ci sono dati finanziari analizzati nella sessione
    if "financial_analysis" in st.session_state and st.session_state.financial_analysis:
        try:
            # Importa il modulo per generare il piano finanziario
            from financial_integration import generate_financial_plan_from_data

            # Genera il piano finanziario utilizzando i dati finanziari importati
            financial_plan_text = generate_financial_plan_from_data(state)

            # Crea la risposta
            response = {"role": "assistant", "content": financial_plan_text}

            return {"messages": [response]}
        except Exception as e:
            print(f"Errore nell'utilizzo del modulo finanziario: {e}")
            # Fallback al metodo standard in caso di errore

    # Se non ci sono dati finanziari o c'è stato un errore, utilizza il metodo standard
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"\n\n---\nDocumenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---\n" if doc_context else ""

    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")
    online_search_enabled = state.get("online_search_enabled", False)
    perplexity_results = state.get("perplexity_results")

    search_section = ""
    if online_search_enabled and perplexity_results:
        # Estrai il testo dai risultati di Perplexity in base al formato
        perplexity_text = ""
        if isinstance(perplexity_results, dict):
            # Se è un dizionario, cerca prima il testo grezzo
            if "raw_text" in perplexity_results:
                perplexity_text = perplexity_results["raw_text"]
            # Altrimenti, cerca altre chiavi comuni
            elif "extracted_text" in perplexity_results:
                perplexity_text = perplexity_results["extracted_text"]
            elif "choices" in perplexity_results and len(perplexity_results["choices"]) > 0:
                if isinstance(perplexity_results["choices"][0], dict) and "message" in perplexity_results["choices"][0]:
                    perplexity_text = perplexity_results["choices"][0]["message"].get("content", "")
            # Se non troviamo testo, proviamo a convertire l'intero dizionario in testo
            else:
                try:
                    # Estrai solo le sezioni più rilevanti per il piano finanziario
                    financial_info = []

                    # Proiezioni finanziarie
                    if "financial_projections" in perplexity_results and perplexity_results["financial_projections"]:
                        projections = perplexity_results["financial_projections"]
                        projections_text = "Proiezioni finanziarie:\n"
                        if isinstance(projections, dict):
                            for year, data in projections.items():
                                projections_text += f"\nAnno {year}:\n"
                                if isinstance(data, dict):
                                    for key, value in data.items():
                                        projections_text += f"- {key}: {value}\n"
                                else:
                                    projections_text += f"- {data}\n"
                        elif isinstance(projections, list):
                            for item in projections:
                                if isinstance(item, dict):
                                    year = item.get("year", "")
                                    projections_text += f"\nAnno {year}:\n"
                                    for key, value in item.items():
                                        if key != "year":
                                            projections_text += f"- {key}: {value}\n"
                                else:
                                    projections_text += f"- {item}\n"
                        else:
                            projections_text += str(projections)
                        financial_info.append(projections_text)

                    # Investimenti necessari
                    if "investment_needs" in perplexity_results and perplexity_results["investment_needs"]:
                        investment = perplexity_results["investment_needs"]
                        investment_text = "Investimenti necessari:\n"
                        if isinstance(investment, dict):
                            for category, amount in investment.items():
                                investment_text += f"- {category}: {amount}\n"
                        elif isinstance(investment, list):
                            for item in investment:
                                if isinstance(item, dict):
                                    category = item.get("category", "")
                                    amount = item.get("amount", "")
                                    investment_text += f"- {category}: {amount}\n"
                                else:
                                    investment_text += f"- {item}\n"
                        else:
                            investment_text += str(investment)
                        financial_info.append(investment_text)

                    # Fonti di finanziamento
                    if "funding_sources" in perplexity_results and perplexity_results["funding_sources"]:
                        funding = perplexity_results["funding_sources"]
                        funding_text = "Fonti di finanziamento:\n"
                        if isinstance(funding, list):
                            for item in funding:
                                if isinstance(item, dict):
                                    source = item.get("source", "")
                                    amount = item.get("amount", "")
                                    funding_text += f"- {source}: {amount}\n"
                                else:
                                    funding_text += f"- {item}\n"
                        else:
                            funding_text += str(funding)
                        financial_info.append(funding_text)

                    # Indicatori finanziari
                    if "financial_indicators" in perplexity_results and perplexity_results["financial_indicators"]:
                        indicators = perplexity_results["financial_indicators"]
                        indicators_text = "Indicatori finanziari:\n"
                        if isinstance(indicators, dict):
                            for name, value in indicators.items():
                                indicators_text += f"- {name}: {value}\n"
                        elif isinstance(indicators, list):
                            for item in indicators:
                                if isinstance(item, dict):
                                    name = item.get("name", "")
                                    value = item.get("value", "")
                                    indicators_text += f"- {name}: {value}\n"
                                else:
                                    indicators_text += f"- {item}\n"
                        else:
                            indicators_text += str(indicators)
                        financial_info.append(indicators_text)

                    # Fonti
                    if "sources" in perplexity_results and perplexity_results["sources"]:
                        sources = perplexity_results["sources"]
                        sources_text = "Fonti:\n"
                        for i, source in enumerate(sources):
                            if isinstance(source, dict) and "url" in source:
                                sources_text += f"- {source.get('title', 'Fonte ' + str(i+1))}: {source['url']}\n"
                            else:
                                sources_text += f"- {source}\n"
                        financial_info.append(sources_text)

                    # Unisci tutte le sezioni
                    perplexity_text = "\n\n".join(financial_info)

                    # Se non abbiamo estratto nulla, usa il dizionario completo come fallback
                    if not perplexity_text:
                        perplexity_text = json.dumps(perplexity_results, indent=2, ensure_ascii=False)
                except Exception as e:
                    perplexity_text = f"Errore nell'elaborazione dei risultati: {str(e)}\n{str(perplexity_results)}"
        else:
            # Se non è un dizionario, converti direttamente in stringa
            perplexity_text = str(perplexity_results)

        search_section = f"""\
\n---
Informazioni aggiuntive dalla ricerca online (Perplexity):
---
{perplexity_text}
---
Utilizza queste informazioni per arricchire la sezione.
"""

    if edit_instructions and original_text:
        prompt_template = f"""
        Rivedi il seguente Piano Finanziario per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni rilevanti:
        - Obiettivi del piano: {{plan_objectives}}
        - Orizzonte temporale: {{time_horizon}}
        - Necessità di finanziamento: {{funding_needs}}
        - Dati finanziari esistenti (se disponibili): {{financial_data}}
        {doc_section}
        {search_section} # Aggiunta dei risultati di ricerca
        Restituisci solo il testo rivisto del Piano Finanziario.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name"),
            plan_objectives=state.get("plan_objectives"),
            time_horizon=state.get("time_horizon"),
            funding_needs=state.get("funding_needs"),
            financial_data=state.get("financial_data", "Non disponibili") # Aggiungere campo allo stato
        ))
    else:
        prompt_template = f"""
        Sei un esperto analista finanziario. Scrivi un Piano Finanziario dettagliato per {{company_name}}.

        Informazioni rilevanti:
        - Nome azienda: {{company_name}}
        - Obiettivi del piano: {{plan_objectives}}
        - Orizzonte temporale del piano: {{time_horizon}}
        - Necessità di finanziamento: {{funding_needs}}
        - Dati finanziari esistenti (se disponibili): {{financial_data}}
        {doc_section}
        {search_section} # Aggiunta dei risultati di ricerca
        Includi proiezioni di vendita, conto economico previsionale, stato patrimoniale previsionale, rendiconto finanziario previsionale, analisi del punto di pareggio (break-even) e analisi dei principali indici finanziari.
        Specifica le assunzioni chiave utilizzate.
        Restituisci solo il testo del Piano Finanziario.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            company_name=state.get("company_name"),
            plan_objectives=state.get("plan_objectives"),
            time_horizon=state.get("time_horizon"),
            funding_needs=state.get("funding_needs"),
            financial_data=state.get("financial_data", "Non disponibili")
        ))

    # Ensure response is a dict with role/content
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        try:
            content = response.content if hasattr(response, 'content') else str(response)
            response = {"role": "assistant", "content": content}
        except Exception:
             response = {"role": "assistant", "content": str(response)}

    return {"messages": [response]}

def human_review(state: BusinessPlanState) -> Dict[str, Any]:
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"\n\n---\nDocumenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---\n" if doc_context else ""

    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")

    if edit_instructions and original_text:
        prompt_template = f"""
        Rivedi il seguente Riepilogo per Revisione per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni sull'azienda:
        - Nome: {{company_name}}
        {doc_section}
        Restituisci solo il testo rivisto del Riepilogo per Revisione.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name")
        ))
    else:
        prompt_template = f"""
        Genera un riepilogo del business plan di {{company_name}} pronto per la revisione.

        Riassumi brevemente:
        - Sommario esecutivo
        - Punti chiave dell'analisi di mercato
        - Punti chiave dell'analisi competitiva
        - Elementi principali del piano finanziario
        {doc_section}
        Suggerisci anche 3-5 domande che l'utente dovrebbe considerare per migliorare ulteriormente il piano.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            company_name=state.get("company_name")
        ))
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        response = {"role": "assistant", "content": str(response)}
    return {"messages": [response]}

def document_generation(state: BusinessPlanState) -> Dict[str, Any]:
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"\n\n---\nDocumenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---\n" if doc_context else ""

    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")

    if edit_instructions and original_text:
        prompt_template = f"""
        Rivedi il seguente Sommario Finale per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni sull'azienda:
        - Nome: {{company_name}}
        {doc_section}
        Restituisci solo il testo rivisto del Sommario Finale.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name")
        ))
    else:
        prompt_template = f"""
        Genera un sommario di tutto il business plan per {{company_name}}.

        Il documento finale è pronto per essere generato e deve includere un indice e tutte le sezioni.
        Elenca tutte le sezioni che saranno incluse nel documento finale con una breve descrizione del contenuto.
        {doc_section}
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            company_name=state.get("company_name")
        ))
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        response = {"role": "assistant", "content": str(response)}
    return {"messages": [response]}

def build_business_plan_graph(vector_db: VectorDatabase, custom_outline: Optional[Dict[str, Any]] = None):
    """
    Costruisce il grafo LangGraph per il Business Plan Builder in modo dinamico
    in base alla struttura (outline) fornita dall'utente.
    """
    graph = StateGraph(BusinessPlanState)

    # Determina la struttura da usare: custom_outline o default
    outline = custom_outline if custom_outline else Config.DEFAULT_BUSINESS_PLAN_STRUCTURE

    # Mappa nome sezione -> funzione nodo (aggiungi qui eventuali custom)
    node_map = {
        "Pianificazione Iniziale": initial_planning,
        "Sommario Esecutivo": executive_summary,
        "Analisi di Mercato": market_analysis,
        "Analisi Competitiva": competitor_analysis,
        "Piano Finanziario": financial_plan,
        "Revisione Umana": human_review,
        "Generazione Documento": document_generation,
    }

    # Crea nodi dinamicamente in base all'outline
    section_keys = list(outline.keys())
    for idx, section in enumerate(section_keys):
        node_key = section.lower().replace(" ", "_")
        # Usa la funzione standard se esiste, altrimenti una funzione generica
        node_fn = node_map.get(section, None)
        if node_fn is not None:
            graph.add_node(node_key, node_fn)
        else:
            # Nodo generico per sezioni custom
            def generic_section(state: BusinessPlanState, section_name=section):
                llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
                prompt = ChatPromptTemplate.from_template(
                    f"Genera la sezione '{section_name}' del business plan per {{company_name}}. "
                    f"Includi dettagli rilevanti e adatta lo stile al contesto aziendale."
                )
                response = llm.invoke(prompt.format(company_name=state.get("company_name", "")))
                return {"messages": [{"role": "assistant", "content": str(response)}]}
            graph.add_node(node_key, generic_section)

    # Routing dinamico: ogni sezione va alla successiva, l'ultima termina
    for idx, section in enumerate(section_keys[:-1]):
        current_key = section.lower().replace(" ", "_")
        next_key = section_keys[idx + 1].lower().replace(" ", "_")
        graph.add_edge(current_key, next_key)
    # L'ultimo nodo termina il grafo
    last_key = section_keys[-1].lower().replace(" ", "_")
    graph.add_edge(last_key, END)

    # Imposta il nodo iniziale
    first_key = section_keys[0].lower().replace(" ", "_")
    graph.set_entry_point(first_key)

    return graph

# Funzione per la descrizione dell'azienda
def company_description(state: BusinessPlanState) -> Dict[str, Any]:
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"\n\n---\nDocumenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---\n" if doc_context else ""

    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")
    online_search_enabled = state.get("online_search_enabled", False)
    perplexity_results = state.get("perplexity_results")

    search_section = ""
    if online_search_enabled and perplexity_results:
        # Estrai il testo dai risultati di Perplexity in base al formato
        perplexity_text = ""
        if isinstance(perplexity_results, dict):
            # Se è un dizionario, cerca prima il testo grezzo
            if "raw_text" in perplexity_results:
                perplexity_text = perplexity_results["raw_text"]
            # Altrimenti, cerca altre chiavi comuni
            elif "extracted_text" in perplexity_results:
                perplexity_text = perplexity_results["extracted_text"]
            elif "choices" in perplexity_results and len(perplexity_results["choices"]) > 0:
                if isinstance(perplexity_results["choices"][0], dict) and "message" in perplexity_results["choices"][0]:
                    perplexity_text = perplexity_results["choices"][0]["message"].get("content", "")
            # Se non troviamo testo, proviamo a convertire l'intero dizionario in testo
            else:
                try:
                    # Estrai solo le sezioni più rilevanti per la descrizione dell'azienda
                    company_info = []

                    # Informazioni sull'azienda
                    if "company_info" in perplexity_results and perplexity_results["company_info"]:
                        info = perplexity_results["company_info"]
                        info_text = "Informazioni sull'azienda:\n"
                        if isinstance(info, dict):
                            for key, value in info.items():
                                info_text += f"- {key}: {value}\n"
                        else:
                            info_text += str(info)
                        company_info.append(info_text)

                    # Storia dell'azienda
                    if "history" in perplexity_results and perplexity_results["history"]:
                        history = perplexity_results["history"]
                        history_text = "Storia dell'azienda:\n"
                        if isinstance(history, str):
                            history_text += history
                        else:
                            history_text += str(history)
                        company_info.append(history_text)

                    # Missione e visione
                    if "mission" in perplexity_results and perplexity_results["mission"]:
                        mission = perplexity_results["mission"]
                        mission_text = "Missione:\n"
                        mission_text += str(mission)
                        company_info.append(mission_text)

                    if "vision" in perplexity_results and perplexity_results["vision"]:
                        vision = perplexity_results["vision"]
                        vision_text = "Visione:\n"
                        vision_text += str(vision)
                        company_info.append(vision_text)

                    # Struttura legale
                    if "legal_structure" in perplexity_results and perplexity_results["legal_structure"]:
                        legal = perplexity_results["legal_structure"]
                        legal_text = "Struttura legale:\n"
                        legal_text += str(legal)
                        company_info.append(legal_text)

                    # Fonti
                    if "sources" in perplexity_results and perplexity_results["sources"]:
                        sources = perplexity_results["sources"]
                        sources_text = "Fonti:\n"
                        for i, source in enumerate(sources):
                            if isinstance(source, dict) and "url" in source:
                                sources_text += f"- {source.get('title', 'Fonte ' + str(i+1))}: {source['url']}\n"
                            else:
                                sources_text += f"- {source}\n"
                        company_info.append(sources_text)

                    # Unisci tutte le sezioni
                    perplexity_text = "\n\n".join(company_info)

                    # Se non abbiamo estratto nulla, usa il dizionario completo come fallback
                    if not perplexity_text:
                        perplexity_text = json.dumps(perplexity_results, indent=2, ensure_ascii=False)
                except Exception as e:
                    perplexity_text = f"Errore nell'elaborazione dei risultati: {str(e)}\n{str(perplexity_results)}"
        else:
            # Se non è un dizionario, converti direttamente in stringa
            perplexity_text = str(perplexity_results)

        search_section = f"""\
\n---
Informazioni aggiuntive dalla ricerca online (Perplexity):
---
{perplexity_text}
---
Utilizza queste informazioni per arricchire la sezione.
"""

    if edit_instructions and original_text:
        prompt_template = f"""
        Rivedi la seguente Descrizione dell'Azienda per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni rilevanti:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Descrizione: {{company_description}}
        - Anno fondazione: {{year_founded}}
        - Dipendenti: {{num_employees}}
        - Area geografica: {{area}}
        {doc_section}
        {search_section}
        Restituisci solo il testo rivisto della Descrizione dell'Azienda.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            company_description=state.get("company_description"),
            year_founded=state.get("year_founded"),
            num_employees=state.get("num_employees"),
            area=state.get("area")
        ))
    else:
        prompt_template = f"""
        Sei un esperto consulente di business plan. Scrivi una Descrizione dell'Azienda dettagliata per {{company_name}}.

        Informazioni rilevanti:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Descrizione: {{company_description}}
        - Anno fondazione: {{year_founded}}
        - Dipendenti: {{num_employees}}
        - Area geografica: {{area}}
        {doc_section}
        {search_section}

        Includi la missione e visione dell'azienda, la sua storia, la struttura legale, la localizzazione e il team di gestione.
        Restituisci solo il testo della Descrizione dell'Azienda.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            company_description=state.get("company_description"),
            year_founded=state.get("year_founded"),
            num_employees=state.get("num_employees"),
            area=state.get("area")
        ))

    # Ensure response is a dict with role/content
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        try:
            content = response.content if hasattr(response, 'content') else str(response)
            response = {"role": "assistant", "content": content}
        except Exception:
             response = {"role": "assistant", "content": str(response)}

    return {"messages": [response]}

# Funzione per i prodotti e servizi
def products_and_services(state: BusinessPlanState) -> Dict[str, Any]:
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"\n\n---\nDocumenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---\n" if doc_context else ""

    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")
    online_search_enabled = state.get("online_search_enabled", False)
    perplexity_results = state.get("perplexity_results")

    search_section = ""
    if online_search_enabled and perplexity_results:
        # Estrai il testo dai risultati di Perplexity in base al formato
        perplexity_text = ""
        if isinstance(perplexity_results, dict):
            # Se è un dizionario, cerca prima il testo grezzo
            if "raw_text" in perplexity_results:
                perplexity_text = perplexity_results["raw_text"]
            # Altrimenti, cerca altre chiavi comuni
            elif "extracted_text" in perplexity_results:
                perplexity_text = perplexity_results["extracted_text"]
            elif "choices" in perplexity_results and len(perplexity_results["choices"]) > 0:
                if isinstance(perplexity_results["choices"][0], dict) and "message" in perplexity_results["choices"][0]:
                    perplexity_text = perplexity_results["choices"][0]["message"].get("content", "")
            # Se non troviamo testo, proviamo a convertire l'intero dizionario in testo
            else:
                try:
                    # Estrai solo le sezioni più rilevanti per prodotti e servizi
                    product_info = []

                    # Prodotti e servizi
                    if "products" in perplexity_results and perplexity_results["products"]:
                        products = perplexity_results["products"]
                        products_text = "Prodotti e servizi:\n"
                        if isinstance(products, list):
                            for item in products:
                                if isinstance(item, dict):
                                    name = item.get("name", "")
                                    desc = item.get("description", "")
                                    products_text += f"- {name}: {desc}\n"
                                else:
                                    products_text += f"- {item}\n"
                        else:
                            products_text += str(products)
                        product_info.append(products_text)

                    # Caratteristiche e benefici
                    if "features" in perplexity_results and perplexity_results["features"]:
                        features = perplexity_results["features"]
                        features_text = "Caratteristiche e benefici:\n"
                        if isinstance(features, list):
                            for item in features:
                                if isinstance(item, dict):
                                    name = item.get("name", "")
                                    benefit = item.get("benefit", "")
                                    features_text += f"- {name}: {benefit}\n"
                                else:
                                    features_text += f"- {item}\n"
                        else:
                            features_text += str(features)
                        product_info.append(features_text)

                    # Proprietà intellettuale
                    if "intellectual_property" in perplexity_results and perplexity_results["intellectual_property"]:
                        ip = perplexity_results["intellectual_property"]
                        ip_text = "Proprietà intellettuale:\n"
                        if isinstance(ip, list):
                            for item in ip:
                                if isinstance(item, dict):
                                    type_ip = item.get("type", "")
                                    desc = item.get("description", "")
                                    ip_text += f"- {type_ip}: {desc}\n"
                                else:
                                    ip_text += f"- {item}\n"
                        else:
                            ip_text += str(ip)
                        product_info.append(ip_text)

                    # Ciclo di vita del prodotto
                    if "product_lifecycle" in perplexity_results and perplexity_results["product_lifecycle"]:
                        lifecycle = perplexity_results["product_lifecycle"]
                        lifecycle_text = "Ciclo di vita del prodotto:\n"
                        if isinstance(lifecycle, dict):
                            for stage, desc in lifecycle.items():
                                lifecycle_text += f"- {stage}: {desc}\n"
                        elif isinstance(lifecycle, list):
                            for item in lifecycle:
                                if isinstance(item, dict):
                                    stage = item.get("stage", "")
                                    desc = item.get("description", "")
                                    lifecycle_text += f"- {stage}: {desc}\n"
                                else:
                                    lifecycle_text += f"- {item}\n"
                        else:
                            lifecycle_text += str(lifecycle)
                        product_info.append(lifecycle_text)

                    # Fonti
                    if "sources" in perplexity_results and perplexity_results["sources"]:
                        sources = perplexity_results["sources"]
                        sources_text = "Fonti:\n"
                        for i, source in enumerate(sources):
                            if isinstance(source, dict) and "url" in source:
                                sources_text += f"- {source.get('title', 'Fonte ' + str(i+1))}: {source['url']}\n"
                            else:
                                sources_text += f"- {source}\n"
                        product_info.append(sources_text)

                    # Unisci tutte le sezioni
                    perplexity_text = "\n\n".join(product_info)

                    # Se non abbiamo estratto nulla, usa il dizionario completo come fallback
                    if not perplexity_text:
                        perplexity_text = json.dumps(perplexity_results, indent=2, ensure_ascii=False)
                except Exception as e:
                    perplexity_text = f"Errore nell'elaborazione dei risultati: {str(e)}\n{str(perplexity_results)}"
        else:
            # Se non è un dizionario, converti direttamente in stringa
            perplexity_text = str(perplexity_results)

        search_section = f"""\
\n---
Informazioni aggiuntive dalla ricerca online (Perplexity):
---
{perplexity_text}
---
Utilizza queste informazioni per arricchire la sezione.
"""

    if edit_instructions and original_text:
        prompt_template = f"""
        Rivedi la seguente sezione Prodotti e Servizi per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni rilevanti:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Prodotti/servizi principali: {{main_products}}
        - Mercato target: {{target_market}}
        {doc_section}
        {search_section}
        Restituisci solo il testo rivisto della sezione Prodotti e Servizi.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            main_products=state.get("main_products"),
            target_market=state.get("target_market")
        ))
    else:
        prompt_template = f"""
        Sei un esperto consulente di business plan. Scrivi una sezione dettagliata sui Prodotti e Servizi per {{company_name}}.

        Informazioni rilevanti:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Prodotti/servizi principali: {{main_products}}
        - Mercato target: {{target_market}}
        {doc_section}
        {search_section}

        Includi una descrizione dettagliata dei prodotti/servizi, il ciclo di vita del prodotto, informazioni sulla proprietà intellettuale,
        attività di ricerca e sviluppo, e dettagli sui fornitori e la catena di approvvigionamento.
        Restituisci solo il testo della sezione Prodotti e Servizi.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            main_products=state.get("main_products"),
            target_market=state.get("target_market")
        ))

    # Ensure response is a dict with role/content
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        try:
            content = response.content if hasattr(response, 'content') else str(response)
            response = {"role": "assistant", "content": content}
        except Exception:
             response = {"role": "assistant", "content": str(response)}

    return {"messages": [response]}

# Funzione per la strategia di marketing
def marketing_strategy(state: BusinessPlanState) -> Dict[str, Any]:
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"\n\n---\nDocumenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---\n" if doc_context else ""

    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")
    online_search_enabled = state.get("online_search_enabled", False)
    perplexity_results = state.get("perplexity_results")

    search_section = ""
    if online_search_enabled and perplexity_results:
        # Estrai il testo dai risultati di Perplexity in base al formato
        perplexity_text = ""
        if isinstance(perplexity_results, dict):
            # Se è un dizionario, cerca prima il testo grezzo
            if "raw_text" in perplexity_results:
                perplexity_text = perplexity_results["raw_text"]
            # Altrimenti, cerca altre chiavi comuni
            elif "extracted_text" in perplexity_results:
                perplexity_text = perplexity_results["extracted_text"]
            elif "choices" in perplexity_results and len(perplexity_results["choices"]) > 0:
                if isinstance(perplexity_results["choices"][0], dict) and "message" in perplexity_results["choices"][0]:
                    perplexity_text = perplexity_results["choices"][0]["message"].get("content", "")
            # Se non troviamo testo, proviamo a convertire l'intero dizionario in testo
            else:
                try:
                    # Estrai solo le sezioni più rilevanti per la strategia di marketing
                    marketing_info = []

                    # Strategie di marketing
                    if "marketing_strategies" in perplexity_results and perplexity_results["marketing_strategies"]:
                        strategies = perplexity_results["marketing_strategies"]
                        strategies_text = "Strategie di marketing:\n"
                        if isinstance(strategies, list):
                            for item in strategies:
                                if isinstance(item, dict):
                                    name = item.get("name", "")
                                    desc = item.get("description", "")
                                    strategies_text += f"- {name}: {desc}\n"
                                else:
                                    strategies_text += f"- {item}\n"
                        else:
                            strategies_text += str(strategies)
                        marketing_info.append(strategies_text)

                    # Canali di marketing
                    if "marketing_channels" in perplexity_results and perplexity_results["marketing_channels"]:
                        channels = perplexity_results["marketing_channels"]
                        channels_text = "Canali di marketing:\n"
                        if isinstance(channels, list):
                            for item in channels:
                                if isinstance(item, dict):
                                    name = item.get("name", "")
                                    desc = item.get("description", "")
                                    channels_text += f"- {name}: {desc}\n"
                                else:
                                    channels_text += f"- {item}\n"
                        else:
                            channels_text += str(channels)
                        marketing_info.append(channels_text)

                    # Strategie di prezzo
                    if "pricing_strategy" in perplexity_results and perplexity_results["pricing_strategy"]:
                        pricing = perplexity_results["pricing_strategy"]
                        pricing_text = "Strategia di prezzo:\n"
                        if isinstance(pricing, dict):
                            for key, value in pricing.items():
                                pricing_text += f"- {key}: {value}\n"
                        else:
                            pricing_text += str(pricing)
                        marketing_info.append(pricing_text)

                    # Budget di marketing
                    if "marketing_budget" in perplexity_results and perplexity_results["marketing_budget"]:
                        budget = perplexity_results["marketing_budget"]
                        budget_text = "Budget di marketing:\n"
                        if isinstance(budget, dict):
                            for key, value in budget.items():
                                budget_text += f"- {key}: {value}\n"
                        else:
                            budget_text += str(budget)
                        marketing_info.append(budget_text)

                    # Fonti
                    if "sources" in perplexity_results and perplexity_results["sources"]:
                        sources = perplexity_results["sources"]
                        sources_text = "Fonti:\n"
                        for i, source in enumerate(sources):
                            if isinstance(source, dict) and "url" in source:
                                sources_text += f"- {source.get('title', 'Fonte ' + str(i+1))}: {source['url']}\n"
                            else:
                                sources_text += f"- {source}\n"
                        marketing_info.append(sources_text)

                    # Unisci tutte le sezioni
                    perplexity_text = "\n\n".join(marketing_info)

                    # Se non abbiamo estratto nulla, usa il dizionario completo come fallback
                    if not perplexity_text:
                        perplexity_text = json.dumps(perplexity_results, indent=2, ensure_ascii=False)
                except Exception as e:
                    perplexity_text = f"Errore nell'elaborazione dei risultati: {str(e)}\n{str(perplexity_results)}"
        else:
            # Se non è un dizionario, converti direttamente in stringa
            perplexity_text = str(perplexity_results)

        search_section = f"""\
\n---
Informazioni aggiuntive dalla ricerca online (Perplexity):
---
{perplexity_text}
---
Utilizza queste informazioni per arricchire la sezione.
"""

    if edit_instructions and original_text:
        prompt_template = f"""
        Rivedi la seguente Strategia di Marketing per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni rilevanti:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Prodotti/servizi: {{main_products}}
        - Mercato target: {{target_market}}
        - Area geografica: {{area}}
        {doc_section}
        {search_section}
        Restituisci solo il testo rivisto della Strategia di Marketing.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            main_products=state.get("main_products"),
            target_market=state.get("target_market"),
            area=state.get("area")
        ))
    else:
        prompt_template = f"""
        Sei un esperto di marketing. Scrivi una Strategia di Marketing dettagliata per {{company_name}}.

        Informazioni rilevanti:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Prodotti/servizi: {{main_products}}
        - Mercato target: {{target_market}}
        - Area geografica: {{area}}
        {doc_section}
        {search_section}

        Includi la strategia di marketing generale, la strategia di prezzo, la strategia di promozione,
        la strategia di distribuzione e il piano di vendita.
        Restituisci solo il testo della Strategia di Marketing.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            main_products=state.get("main_products"),
            target_market=state.get("target_market"),
            area=state.get("area")
        ))

    # Ensure response is a dict with role/content
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        try:
            content = response.content if hasattr(response, 'content') else str(response)
            response = {"role": "assistant", "content": content}
        except Exception:
             response = {"role": "assistant", "content": str(response)}

    return {"messages": [response]}

# Funzione per il piano operativo
def operational_plan(state: BusinessPlanState) -> Dict[str, Any]:
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"\n\n---\nDocumenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---\n" if doc_context else ""

    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")
    online_search_enabled = state.get("online_search_enabled", False)
    perplexity_results = state.get("perplexity_results")

    search_section = ""
    if online_search_enabled and perplexity_results:
        # Estrai il testo dai risultati di Perplexity in base al formato
        perplexity_text = ""
        if isinstance(perplexity_results, dict):
            # Se è un dizionario, cerca prima il testo grezzo
            if "raw_text" in perplexity_results:
                perplexity_text = perplexity_results["raw_text"]
            # Altrimenti, cerca altre chiavi comuni
            elif "extracted_text" in perplexity_results:
                perplexity_text = perplexity_results["extracted_text"]
            elif "choices" in perplexity_results and len(perplexity_results["choices"]) > 0:
                if isinstance(perplexity_results["choices"][0], dict) and "message" in perplexity_results["choices"][0]:
                    perplexity_text = perplexity_results["choices"][0]["message"].get("content", "")
            # Se non troviamo testo, proviamo a convertire l'intero dizionario in testo
            else:
                try:
                    # Estrai solo le sezioni più rilevanti per il piano operativo
                    operational_info = []

                    # Processi operativi
                    if "operational_processes" in perplexity_results and perplexity_results["operational_processes"]:
                        processes = perplexity_results["operational_processes"]
                        processes_text = "Processi operativi:\n"
                        if isinstance(processes, list):
                            for item in processes:
                                if isinstance(item, dict):
                                    name = item.get("name", "")
                                    desc = item.get("description", "")
                                    processes_text += f"- {name}: {desc}\n"
                                else:
                                    processes_text += f"- {item}\n"
                        else:
                            processes_text += str(processes)
                        operational_info.append(processes_text)

                    # Struttura organizzativa
                    if "organizational_structure" in perplexity_results and perplexity_results["organizational_structure"]:
                        structure = perplexity_results["organizational_structure"]
                        structure_text = "Struttura organizzativa:\n"
                        if isinstance(structure, list):
                            for item in structure:
                                if isinstance(item, dict):
                                    role = item.get("role", "")
                                    desc = item.get("description", "")
                                    structure_text += f"- {role}: {desc}\n"
                                else:
                                    structure_text += f"- {item}\n"
                        else:
                            structure_text += str(structure)
                        operational_info.append(structure_text)

                    # Risorse necessarie
                    if "resources" in perplexity_results and perplexity_results["resources"]:
                        resources = perplexity_results["resources"]
                        resources_text = "Risorse necessarie:\n"
                        if isinstance(resources, dict):
                            for key, value in resources.items():
                                resources_text += f"- {key}: {value}\n"
                        elif isinstance(resources, list):
                            for item in resources:
                                if isinstance(item, dict):
                                    type_res = item.get("type", "")
                                    desc = item.get("description", "")
                                    resources_text += f"- {type_res}: {desc}\n"
                                else:
                                    resources_text += f"- {item}\n"
                        else:
                            resources_text += str(resources)
                        operational_info.append(resources_text)

                    # Fonti
                    if "sources" in perplexity_results and perplexity_results["sources"]:
                        sources = perplexity_results["sources"]
                        sources_text = "Fonti:\n"
                        for i, source in enumerate(sources):
                            if isinstance(source, dict) and "url" in source:
                                sources_text += f"- {source.get('title', 'Fonte ' + str(i+1))}: {source['url']}\n"
                            else:
                                sources_text += f"- {source}\n"
                        operational_info.append(sources_text)

                    # Unisci tutte le sezioni
                    perplexity_text = "\n\n".join(operational_info)

                    # Se non abbiamo estratto nulla, usa il dizionario completo come fallback
                    if not perplexity_text:
                        perplexity_text = json.dumps(perplexity_results, indent=2, ensure_ascii=False)
                except Exception as e:
                    perplexity_text = f"Errore nell'elaborazione dei risultati: {str(e)}\n{str(perplexity_results)}"
        else:
            # Se non è un dizionario, converti direttamente in stringa
            perplexity_text = str(perplexity_results)

        search_section = f"""\
\n---
Informazioni aggiuntive dalla ricerca online (Perplexity):
---
{perplexity_text}
---
Utilizza queste informazioni per arricchire la sezione.
"""

    if edit_instructions and original_text:
        prompt_template = f"""
        Rivedi il seguente Piano Operativo per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni rilevanti:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Dipendenti: {{num_employees}}
        - Area geografica: {{area}}
        {doc_section}
        {search_section}
        Restituisci solo il testo rivisto del Piano Operativo.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            num_employees=state.get("num_employees"),
            area=state.get("area")
        ))
    else:
        prompt_template = f"""
        Sei un esperto di operazioni aziendali. Scrivi un Piano Operativo dettagliato per {{company_name}}.

        Informazioni rilevanti:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Dipendenti: {{num_employees}}
        - Area geografica: {{area}}
        {doc_section}
        {search_section}

        Includi i processi operativi, la struttura organizzativa, le risorse umane,
        le attrezzature e tecnologie necessarie, e la gestione della qualità.
        Restituisci solo il testo del Piano Operativo.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            num_employees=state.get("num_employees"),
            area=state.get("area")
        ))

    # Ensure response is a dict with role/content
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        try:
            content = response.content if hasattr(response, 'content') else str(response)
            response = {"role": "assistant", "content": content}
        except Exception:
             response = {"role": "assistant", "content": str(response)}

    return {"messages": [response]}

# Funzione per l'organizzazione e team di gestione
def organization_and_management(state: BusinessPlanState) -> Dict[str, Any]:
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"\n\n---\nDocumenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---\n" if doc_context else ""

    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")
    online_search_enabled = state.get("online_search_enabled", False)
    perplexity_results = state.get("perplexity_results")

    search_section = ""
    if online_search_enabled and perplexity_results:
        # Estrai il testo dai risultati di Perplexity in base al formato
        perplexity_text = ""
        if isinstance(perplexity_results, dict):
            # Se è un dizionario, cerca prima il testo grezzo
            if "raw_text" in perplexity_results:
                perplexity_text = perplexity_results["raw_text"]
            # Altrimenti, cerca altre chiavi comuni
            elif "extracted_text" in perplexity_results:
                perplexity_text = perplexity_results["extracted_text"]
            elif "choices" in perplexity_results and len(perplexity_results["choices"]) > 0:
                if isinstance(perplexity_results["choices"][0], dict) and "message" in perplexity_results["choices"][0]:
                    perplexity_text = perplexity_results["choices"][0]["message"].get("content", "")
            # Se non troviamo testo, proviamo a convertire l'intero dizionario in testo
            else:
                try:
                    # Estrai solo le sezioni più rilevanti per l'organizzazione e team di gestione
                    org_info = []

                    # Struttura organizzativa
                    if "organizational_structure" in perplexity_results and perplexity_results["organizational_structure"]:
                        structure = perplexity_results["organizational_structure"]
                        structure_text = "Struttura organizzativa:\n"
                        if isinstance(structure, list):
                            for item in structure:
                                if isinstance(item, dict):
                                    role = item.get("role", "")
                                    desc = item.get("description", "")
                                    structure_text += f"- {role}: {desc}\n"
                                else:
                                    structure_text += f"- {item}\n"
                        else:
                            structure_text += str(structure)
                        org_info.append(structure_text)

                    # Team di gestione
                    if "management_team" in perplexity_results and perplexity_results["management_team"]:
                        team = perplexity_results["management_team"]
                        team_text = "Team di gestione:\n"
                        if isinstance(team, list):
                            for item in team:
                                if isinstance(item, dict):
                                    name = item.get("name", "")
                                    role = item.get("role", "")
                                    exp = item.get("experience", "")
                                    team_text += f"- {name} ({role}): {exp}\n"
                                else:
                                    team_text += f"- {item}\n"
                        else:
                            team_text += str(team)
                        org_info.append(team_text)

                    # Competenze chiave
                    if "key_skills" in perplexity_results and perplexity_results["key_skills"]:
                        skills = perplexity_results["key_skills"]
                        skills_text = "Competenze chiave:\n"
                        if isinstance(skills, list):
                            for item in skills:
                                if isinstance(item, dict):
                                    skill = item.get("skill", "")
                                    desc = item.get("description", "")
                                    skills_text += f"- {skill}: {desc}\n"
                                else:
                                    skills_text += f"- {item}\n"
                        else:
                            skills_text += str(skills)
                        org_info.append(skills_text)

                    # Fonti
                    if "sources" in perplexity_results and perplexity_results["sources"]:
                        sources = perplexity_results["sources"]
                        sources_text = "Fonti:\n"
                        for i, source in enumerate(sources):
                            if isinstance(source, dict) and "url" in source:
                                sources_text += f"- {source.get('title', 'Fonte ' + str(i+1))}: {source['url']}\n"
                            else:
                                sources_text += f"- {source}\n"
                        org_info.append(sources_text)

                    # Unisci tutte le sezioni
                    perplexity_text = "\n\n".join(org_info)

                    # Se non abbiamo estratto nulla, usa il dizionario completo come fallback
                    if not perplexity_text:
                        perplexity_text = json.dumps(perplexity_results, indent=2, ensure_ascii=False)
                except Exception as e:
                    perplexity_text = f"Errore nell'elaborazione dei risultati: {str(e)}\n{str(perplexity_results)}"
        else:
            # Se non è un dizionario, converti direttamente in stringa
            perplexity_text = str(perplexity_results)

        search_section = f"""\
\n---
Informazioni aggiuntive dalla ricerca online (Perplexity):
---
{perplexity_text}
---
Utilizza queste informazioni per arricchire la sezione.
"""

    if edit_instructions and original_text:
        prompt_template = f"""
        Rivedi la seguente sezione Organizzazione e Team di Gestione per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni rilevanti:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Dipendenti: {{num_employees}}
        {doc_section}
        {search_section}
        Restituisci solo il testo rivisto della sezione Organizzazione e Team di Gestione.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            num_employees=state.get("num_employees")
        ))
    else:
        prompt_template = f"""
        Sei un esperto di gestione aziendale. Scrivi una sezione dettagliata sull'Organizzazione e Team di Gestione per {{company_name}}.

        Informazioni rilevanti:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Dipendenti: {{num_employees}}
        {doc_section}
        {search_section}

        Includi la struttura organizzativa, i profili dei membri chiave del team di gestione,
        le competenze e l'esperienza del team, e i piani per l'espansione del personale.
        Restituisci solo il testo della sezione Organizzazione e Team di Gestione.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            num_employees=state.get("num_employees")
        ))

    # Ensure response is a dict with role/content
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        try:
            content = response.content if hasattr(response, 'content') else str(response)
            response = {"role": "assistant", "content": content}
        except Exception:
             response = {"role": "assistant", "content": str(response)}

    return {"messages": [response]}

# Funzione per l'analisi dei rischi
def risk_analysis(state: BusinessPlanState) -> Dict[str, Any]:
    llm = ChatOpenAI(model=Config.DEFAULT_MODEL, temperature=Config.TEMPERATURE)
    doc_context = state.get("section_documents_text") or state.get("documents_text", "")
    doc_section = f"\n\n---\nDocumenti caricati (estratti):\n{doc_context[:2000]}{'...[troncato]' if len(doc_context) > 2000 else ''}\n---\n" if doc_context else ""

    edit_instructions = state.get("edit_instructions")
    original_text = state.get("original_text")
    online_search_enabled = state.get("online_search_enabled", False)
    perplexity_results = state.get("perplexity_results")

    search_section = ""
    if online_search_enabled and perplexity_results:
        # Estrai il testo dai risultati di Perplexity in base al formato
        perplexity_text = ""
        if isinstance(perplexity_results, dict):
            # Se è un dizionario, cerca prima il testo grezzo
            if "raw_text" in perplexity_results:
                perplexity_text = perplexity_results["raw_text"]
            # Altrimenti, cerca altre chiavi comuni
            elif "extracted_text" in perplexity_results:
                perplexity_text = perplexity_results["extracted_text"]
            elif "choices" in perplexity_results and len(perplexity_results["choices"]) > 0:
                if isinstance(perplexity_results["choices"][0], dict) and "message" in perplexity_results["choices"][0]:
                    perplexity_text = perplexity_results["choices"][0]["message"].get("content", "")
            # Se non troviamo testo, proviamo a convertire l'intero dizionario in testo
            else:
                try:
                    # Estrai solo le sezioni più rilevanti per l'analisi dei rischi
                    risk_info = []

                    # Rischi principali
                    if "risks" in perplexity_results and perplexity_results["risks"]:
                        risks = perplexity_results["risks"]
                        risks_text = "Rischi principali:\n"
                        if isinstance(risks, list):
                            for item in risks:
                                if isinstance(item, dict):
                                    type_risk = item.get("type", "")
                                    desc = item.get("description", "")
                                    mitigation = item.get("mitigation", "")
                                    risks_text += f"- {type_risk}: {desc}\n"
                                    if mitigation:
                                        risks_text += f"  Mitigazione: {mitigation}\n"
                                else:
                                    risks_text += f"- {item}\n"
                        else:
                            risks_text += str(risks)
                        risk_info.append(risks_text)

                    # Rischi di mercato
                    if "market_risks" in perplexity_results and perplexity_results["market_risks"]:
                        market_risks = perplexity_results["market_risks"]
                        market_risks_text = "Rischi di mercato:\n"
                        if isinstance(market_risks, list):
                            for item in market_risks:
                                if isinstance(item, dict):
                                    desc = item.get("description", "")
                                    mitigation = item.get("mitigation", "")
                                    market_risks_text += f"- {desc}\n"
                                    if mitigation:
                                        market_risks_text += f"  Mitigazione: {mitigation}\n"
                                else:
                                    market_risks_text += f"- {item}\n"
                        else:
                            market_risks_text += str(market_risks)
                        risk_info.append(market_risks_text)

                    # Rischi finanziari
                    if "financial_risks" in perplexity_results and perplexity_results["financial_risks"]:
                        financial_risks = perplexity_results["financial_risks"]
                        financial_risks_text = "Rischi finanziari:\n"
                        if isinstance(financial_risks, list):
                            for item in financial_risks:
                                if isinstance(item, dict):
                                    desc = item.get("description", "")
                                    mitigation = item.get("mitigation", "")
                                    financial_risks_text += f"- {desc}\n"
                                    if mitigation:
                                        financial_risks_text += f"  Mitigazione: {mitigation}\n"
                                else:
                                    financial_risks_text += f"- {item}\n"
                        else:
                            financial_risks_text += str(financial_risks)
                        risk_info.append(financial_risks_text)

                    # Rischi operativi
                    if "operational_risks" in perplexity_results and perplexity_results["operational_risks"]:
                        operational_risks = perplexity_results["operational_risks"]
                        operational_risks_text = "Rischi operativi:\n"
                        if isinstance(operational_risks, list):
                            for item in operational_risks:
                                if isinstance(item, dict):
                                    desc = item.get("description", "")
                                    mitigation = item.get("mitigation", "")
                                    operational_risks_text += f"- {desc}\n"
                                    if mitigation:
                                        operational_risks_text += f"  Mitigazione: {mitigation}\n"
                                else:
                                    operational_risks_text += f"- {item}\n"
                        else:
                            operational_risks_text += str(operational_risks)
                        risk_info.append(operational_risks_text)

                    # Fonti
                    if "sources" in perplexity_results and perplexity_results["sources"]:
                        sources = perplexity_results["sources"]
                        sources_text = "Fonti:\n"
                        for i, source in enumerate(sources):
                            if isinstance(source, dict) and "url" in source:
                                sources_text += f"- {source.get('title', 'Fonte ' + str(i+1))}: {source['url']}\n"
                            else:
                                sources_text += f"- {source}\n"
                        risk_info.append(sources_text)

                    # Unisci tutte le sezioni
                    perplexity_text = "\n\n".join(risk_info)

                    # Se non abbiamo estratto nulla, usa il dizionario completo come fallback
                    if not perplexity_text:
                        perplexity_text = json.dumps(perplexity_results, indent=2, ensure_ascii=False)
                except Exception as e:
                    perplexity_text = f"Errore nell'elaborazione dei risultati: {str(e)}\n{str(perplexity_results)}"
        else:
            # Se non è un dizionario, converti direttamente in stringa
            perplexity_text = str(perplexity_results)

        search_section = f"""\
\n---
Informazioni aggiuntive dalla ricerca online (Perplexity):
---
{perplexity_text}
---
Utilizza queste informazioni per arricchire la sezione.
"""

    if edit_instructions and original_text:
        prompt_template = f"""
        Rivedi la seguente Analisi dei Rischi per {{company_name}} e applica le modifiche richieste.

        Testo Originale:
        ---
        {{original_text}}
        ---

        Istruzioni di Modifica:
        ---
        {{edit_instructions}}
        ---

        Informazioni rilevanti:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Mercato target: {{target_market}}
        {doc_section}
        {search_section}
        Restituisci solo il testo rivisto dell'Analisi dei Rischi.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            original_text=original_text,
            edit_instructions=edit_instructions,
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            target_market=state.get("target_market")
        ))
    else:
        prompt_template = f"""
        Sei un esperto di gestione del rischio aziendale. Scrivi un'Analisi dei Rischi dettagliata per {{company_name}}.

        Informazioni rilevanti:
        - Nome: {{company_name}}
        - Settore: {{business_sector}}
        - Mercato target: {{target_market}}
        {doc_section}
        {search_section}

        Identifica e analizza i principali rischi che l'azienda potrebbe affrontare, inclusi rischi di mercato,
        operativi, finanziari, legali e normativi. Per ogni rischio, fornisci strategie di mitigazione.
        Restituisci solo il testo dell'Analisi dei Rischi.
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        response = llm.invoke(prompt.format(
            company_name=state.get("company_name"),
            business_sector=state.get("business_sector"),
            target_market=state.get("target_market")
        ))

    # Ensure response is a dict with role/content
    if isinstance(response, dict):
        if "role" not in response:
            response = {"role": "assistant", "content": response.get("content", str(response))}
    else:
        try:
            content = response.content if hasattr(response, 'content') else str(response)
            response = {"role": "assistant", "content": content}
        except Exception:
             response = {"role": "assistant", "content": str(response)}

    return {"messages": [response]}

# Dizionario che mappa i nomi dei nodi alle funzioni, per l'importazione
node_functions = {
    "initial_planning": initial_planning,
    "executive_summary": executive_summary,
    "company_description": company_description,
    "products_and_services": products_and_services,
    "market_analysis": market_analysis,
    "competitor_analysis": competitor_analysis,
    "marketing_strategy": marketing_strategy,
    "operational_plan": operational_plan,
    "organization_and_management": organization_and_management,
    "risk_analysis": risk_analysis,
    "financial_plan": financial_plan,
    "human_review": human_review,
    "document_generation": document_generation,
}

# Esporta anche le funzioni di routing se necessario altrove
# (Potrebbe essere meglio definirle una sola volta e importarle dove servono)
def route_after_planning(state: BusinessPlanState) -> str:
    return "executive_summary"
def route_after_summary(state: BusinessPlanState) -> str:
    return "company_description"
def route_after_company_description(state: BusinessPlanState) -> str:
    return "products_and_services"
def route_after_products_and_services(state: BusinessPlanState) -> str:
    return "market_analysis"
def route_after_market_analysis(state: BusinessPlanState) -> str:
    return "competitor_analysis"
def route_after_competitor_analysis(state: BusinessPlanState) -> str:
    return "marketing_strategy"
def route_after_marketing_strategy(state: BusinessPlanState) -> str:
    return "operational_plan"
def route_after_operational_plan(state: BusinessPlanState) -> str:
    return "organization_and_management"
def route_after_organization_and_management(state: BusinessPlanState) -> str:
    return "risk_analysis"
def route_after_risk_analysis(state: BusinessPlanState) -> str:
    return "financial_plan"
def route_after_financial_plan(state: BusinessPlanState) -> str:
    return "human_review"
def route_after_human_review(state: BusinessPlanState) -> str:
    if state.get("human_feedback", {}).get("requires_changes", False):
        section_to_modify = state["human_feedback"].get("section_to_modify", "")
        if section_to_modify == "Sommario Esecutivo":
            return "executive_summary"
        elif section_to_modify == "Descrizione dell'Azienda":
            return "company_description"
        elif section_to_modify == "Prodotti e Servizi":
            return "products_and_services"
        elif section_to_modify == "Analisi di Mercato":
            return "market_analysis"
        elif section_to_modify == "Analisi Competitiva":
            return "competitor_analysis"
        elif section_to_modify == "Strategia di Marketing":
            return "marketing_strategy"
        elif section_to_modify == "Piano Operativo":
            return "operational_plan"
        elif section_to_modify == "Organizzazione e Team di Gestione":
            return "organization_and_management"
        elif section_to_modify == "Analisi dei Rischi":
            return "risk_analysis"
        elif section_to_modify == "Piano Finanziario":
            return "financial_plan"
        else:
            return "document_generation"
    else:
        return "document_generation"
def route_after_document_generation(state: BusinessPlanState) -> str:
    # In un'app interattiva, potremmo non voler terminare automaticamente
    # return END
    return "document_generation" # Rimani sull'ultimo nodo o gestisci diversamente
