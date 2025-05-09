#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo avanzato per la generazione di testo con Google Gemini 2.5 Pro

Questo modulo fornisce un'interfaccia completa per generare contenuti di business plan
utilizzando i modelli Gemini di Google. Supporta generazione strutturata,
formattazione avanzata e integrazione con dati di ricerca di mercato.
"""

import os
import time
import json
from typing import Dict, Any, List, Optional, Union
import google.generativeai as genai
from config import Config

class GeminiGenerator:
    """Classe avanzata per la generazione di testo con Google Gemini"""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Inizializza il generatore Gemini

        Args:
            api_key: Chiave API Gemini (opzionale, altrimenti usa variabile d'ambiente)
            model_name: Nome del modello da utilizzare (opzionale, altrimenti usa config)
        """
        # Ottieni la chiave API da parametro o variabile d'ambiente
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY non trovata nelle variabili d'ambiente")

        # Configura l'API Gemini
        genai.configure(api_key=self.api_key)

        # Seleziona il modello
        self.model_name = model_name or Config.GEMINI_MODEL
        self.model = genai.GenerativeModel(self.model_name)

        # Cache per risultati
        self.cache = {}
        self.cache_ttl = 3600  # 1 ora di validità cache

        # Contatori per monitoraggio utilizzo
        self.request_count = 0
        self.token_count = 0
        self.error_count = 0

    def generate_content(self,
                        prompt: str,
                        temperature: float = Config.TEMPERATURE,
                        max_tokens: int = Config.MAX_TOKENS,
                        word_count: Optional[int] = None,
                        use_cache: bool = True,
                        structured_output: bool = False) -> Union[str, Dict[str, Any]]:
        """
        Genera contenuto con Gemini

        Args:
            prompt: Il prompt per la generazione
            temperature: Temperatura per la generazione (0.0-1.0)
            max_tokens: Numero massimo di token da generare
            word_count: Numero di parole desiderato nell'output
            use_cache: Se utilizzare la cache per prompt identici
            structured_output: Se restituire un dizionario strutturato invece del testo

        Returns:
            Il testo generato o un dizionario con il testo e metadati
        """
        # Verifica se il prompt è nella cache e se è ancora valido
        cache_key = f"{prompt}_{temperature}_{max_tokens}_{word_count}"
        if use_cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                print(f"Usando risultato in cache per generazione Gemini")
                return cache_entry["result"] if not structured_output else cache_entry

        # Se è specificato un conteggio parole, aggiungi istruzioni al prompt
        if word_count:
            prompt = f"{prompt}\n\nLa risposta deve essere di circa {word_count} parole."

        # Genera il contenuto
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "top_p": 0.95,
            "top_k": 40
        }

        try:
            # Incrementa contatore richieste
            self.request_count += 1

            # Esegui la generazione
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            # Estrai il testo
            generated_text = response.text

            # Aggiorna contatore token (stima)
            self.token_count += len(generated_text.split()) * 1.3  # Stima approssimativa

            # Prepara il risultato
            result = {
                "text": generated_text,
                "model": self.model_name,
                "timestamp": time.time(),
                "prompt_length": len(prompt),
                "response_length": len(generated_text)
            }

            # Salva nella cache
            if use_cache:
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "result": generated_text if not structured_output else result
                }

            return generated_text if not structured_output else result

        except Exception as e:
            # Incrementa contatore errori
            self.error_count += 1

            error_message = f"Errore nella generazione con Gemini: {str(e)}"
            error_result = {
                "error": error_message,
                "model": self.model_name,
                "timestamp": time.time()
            }

            return error_message if not structured_output else error_result

    def clear_cache(self):
        """Pulisce la cache dei risultati"""
        self.cache = {}
        print("Cache di generazione Gemini cancellata")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche di utilizzo"""
        return {
            "request_count": self.request_count,
            "token_count": int(self.token_count),
            "error_count": self.error_count,
            "cache_size": len(self.cache),
            "model": self.model_name
        }

    def generate_with_research(self,
                              prompt: str,
                              research_data: Dict[str, Any],
                              temperature: float = Config.TEMPERATURE) -> str:
        """
        Genera contenuto integrando dati di ricerca

        Args:
            prompt: Il prompt base per la generazione
            research_data: Dati di ricerca strutturati
            temperature: Temperatura per la generazione

        Returns:
            Il testo generato
        """
        # Estrai dati di ricerca rilevanti
        market_size = research_data.get("market_size", {}).get("description", "")

        trends = ""
        for trend in research_data.get("trends", [])[:5]:
            trends += f"- {trend.get('description', '')}\n"

        competitors = ""
        for comp in research_data.get("competitors", [])[:5]:
            competitors += f"- {comp.get('name', '')}: {comp.get('description', '')}\n"

        opportunities = ""
        for opp in research_data.get("opportunities", [])[:3]:
            opportunities += f"- {opp.get('description', '')}\n"

        # Costruisci il prompt arricchito
        enhanced_prompt = f"""{prompt}

DATI DI RICERCA DI MERCATO:
{f"Dimensione del mercato: {market_size}" if market_size else ""}

Trend principali:
{trends if trends else "Dati non disponibili"}

Competitor principali:
{competitors if competitors else "Dati non disponibili"}

Opportunità:
{opportunities if opportunities else "Dati non disponibili"}

Utilizza questi dati di ricerca per arricchire il contenuto, ma integrandoli in modo naturale nel testo.
Non citare esplicitamente "secondo la ricerca" o frasi simili.
"""

        # Genera il contenuto arricchito
        return self.generate_content(enhanced_prompt, temperature=temperature)


def generate_section(section_name: str,
                    state: Dict[str, Any],
                    word_count: Optional[int] = None,
                    length_type: Optional[str] = None,
                    include_research: bool = True) -> Dict[str, Any]:
    """
    Genera una sezione del business plan usando Gemini

    Args:
        section_name: Nome della sezione da generare
        state: Stato corrente con informazioni sull'azienda
        word_count: Numero di parole desiderato
        length_type: Tipo di lunghezza (breve, media, dettagliata)
        include_research: Se includere dati di ricerca di mercato

    Returns:
        dict: Risultato con il testo generato
    """
    # Converti length_type in word_count se non specificato direttamente
    if not word_count and length_type:
        if length_type == "breve":
            word_count = 300
        elif length_type == "media":
            word_count = 800
        elif length_type == "dettagliata":
            word_count = 2000
        else:
            word_count = 1000  # Default

    # Ottieni il prompt personalizzato se presente
    custom_prompt = ""
    if "section_prompts" in state and section_name in state["section_prompts"]:
        custom_prompt = state["section_prompts"][section_name]

    # Costruisci il prompt base se non c'è un prompt personalizzato
    if not custom_prompt:
        custom_prompt = f"""
        Scrivi SOLO il testo completo e pronto da incollare della sezione '{section_name}' del business plan per l'azienda {state.get('company_name', '')}.
        NON includere meta-informazioni, intestazioni, ruoli, parentesi graffe, markdown, né alcuna spiegazione tecnica.
        Il testo deve essere scorrevole, professionale, coerente e adatto a un documento finale.
        Se la sezione è molto lunga, concludi la frase e non troncare a metà.
        Se necessario, suddividi in paragrafi ma senza titoli o numerazioni.

        Informazioni sull'azienda:
        - Nome: {state.get('company_name', '')}
        - Settore: {state.get('business_sector', '')}
        - Descrizione: {state.get('company_description', '')}
        - Anno fondazione: {state.get('year_founded', '')}
        - Dipendenti: {state.get('num_employees', '')}
        - Prodotti/Servizi: {state.get('main_products', '')}
        - Mercato target: {state.get('target_market', '')}
        - Area geografica: {state.get('area', '')}
        - Obiettivi: {state.get('plan_objectives', '')}
        - Orizzonte temporale: {state.get('time_horizon', '3 anni')}
        - Necessità di finanziamento: {state.get('funding_needs', '')}

        Scrivi in italiano con stile professionale e formale.
        """

    # Aggiungi documenti di contesto se presenti
    if state.get("section_documents_text"):
        custom_prompt += f"\n\nUtilizza queste informazioni come contesto aggiuntivo:\n{state.get('section_documents_text')}"

    # Aggiungi istruzioni specifiche per sezione
    if section_name.lower() in ["analisi di mercato", "market analysis"]:
        custom_prompt += """
        Per questa sezione di analisi di mercato, includi:
        - Dimensione attuale del mercato con dati numerici
        - Tasso di crescita previsto (CAGR)
        - Segmentazione del mercato
        - Tendenze principali
        - Opportunità e sfide
        """
    elif section_name.lower() in ["analisi competitiva", "competitor analysis"]:
        custom_prompt += """
        Per questa sezione di analisi competitiva, includi:
        - Panoramica dei principali concorrenti
        - Punti di forza e debolezza dei concorrenti
        - Posizionamento dell'azienda rispetto ai concorrenti
        - Vantaggi competitivi dell'azienda
        - Analisi SWOT sintetica
        """
    elif section_name.lower() in ["piano finanziario", "financial plan"]:
        custom_prompt += """
        Per questa sezione di piano finanziario, includi:
        - Proiezioni di fatturato per i prossimi anni
        - Struttura dei costi principali
        - Margini attesi
        - Punto di pareggio
        - Necessità di investimento e utilizzo dei fondi
        """

    # Genera il contenuto
    try:
        # Inizializza il generatore con gestione degli errori migliorata
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                # Prova a ottenere la chiave da st.secrets se disponibile
                try:
                    import streamlit as st
                    api_key = st.secrets.get("GEMINI_API_KEY")
                except:
                    pass

            if not api_key:
                raise ValueError("Chiave API Gemini non trovata nelle variabili d'ambiente o nei segreti di Streamlit")

            generator = GeminiGenerator(api_key=api_key)
            print(f"Generatore Gemini inizializzato con successo per la sezione {section_name}")
        except Exception as init_error:
            print(f"Errore nell'inizializzazione di Gemini: {init_error}")
            raise init_error

        # Aggiungi log per debug
        print(f"Generando contenuto per la sezione: {section_name}")
        print(f"Lunghezza prompt: {len(custom_prompt)} caratteri")
        print(f"Utilizzo ricerca: {include_research}")

        # Se abbiamo dati di ricerca e la sezione è pertinente, usali
        if include_research and state.get("perplexity_results") and section_name.lower() in ["analisi di mercato", "market analysis", "analisi competitiva", "competitor analysis"]:
            print(f"Utilizzo dati di ricerca per la sezione {section_name}")
            generated_text = generator.generate_with_research(
                custom_prompt,
                state.get("perplexity_results", {}),
                temperature=state.get("temperature", Config.TEMPERATURE)
            )
        else:
            # Generazione standard
            print(f"Generazione standard per la sezione {section_name}")
            generated_text = generator.generate_content(
                custom_prompt,
                temperature=state.get("temperature", Config.TEMPERATURE),
                max_tokens=state.get("max_tokens", Config.MAX_TOKENS),
                word_count=word_count
            )

        print(f"Generazione completata con successo per {section_name}")
        # Formatta il risultato nel formato atteso da LangGraph
        return {"messages": [{"role": "assistant", "content": generated_text}]}

    except Exception as e:
        error_message = f"Errore nella generazione della sezione {section_name}: {str(e)}"
        print(f"ERRORE: {error_message}")
        import traceback
        traceback.print_exc()
        return {"messages": [{"role": "assistant", "content": f"Si è verificato un errore durante la generazione del contenuto. Dettagli: {error_message}"}]}
