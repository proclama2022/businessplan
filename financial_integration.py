#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo di integrazione per l'analisi finanziaria.

Questo modulo fornisce funzioni di analisi finanziaria per generare suggerimenti e insight
basati sui dati finanziari disponibili nell'applicazione.
"""

import logging
from typing import Dict, List, Any, Optional

# Configura il logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_profit_margin(financial_data: Dict[str, Any]) -> Optional[float]:
    """
    Calcola il margine di profitto medio dai dati finanziari.
    
    Args:
        financial_data: Dizionario contenente i dati finanziari
        
    Returns:
        float: Margine di profitto medio (0-1), o None se non disponibile
    """
    try:
        # Cerca i dati di ricavo e profitto
        revenues = []
        profits = []
        
        if 'raw_data' in financial_data:
            for sheet in financial_data['raw_data'].values():
                for row in sheet:
                    if 'Ricavi' in row and 'Profitto' in row:
                        revenues.append(float(row['Ricavi']))
                        profits.append(float(row['Profitto']))
        
        if revenues and profits:
            # Calcola il margine di profitto medio
            profit_margins = [p / r if r > 0 else 0 for p, r in zip(profits, revenues)]
            return sum(profit_margins) / len(profit_margins)
            
    except Exception as e:
        logger.error(f"Errore nel calcolo del margine di profitto: {e}")
    
    return None

def identify_major_expense_categories(financial_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Identifica le principali categorie di spesa dai dati finanziari.
    
    Args:
        financial_data: Dizionario contenente i dati finanziari
        
    Returns:
        Dict[str, float]: Dizionario con categorie di spesa e percentuali relative
    """
    expense_categories = {}
    
    try:
        if 'raw_data' in financial_data:
            for sheet in financial_data['raw_data'].values():
                for row in sheet:
                    # Cerca campi che indicano spese o costi
                    if 'Categoria' in row and 'Valore' in row:
                        category = str(row['Categoria'])
                        value = float(row['Valore'])
                        
                        if category in expense_categories:
                            expense_categories[category] += value
                        else:
                            expense_categories[category] = value
                    
                    elif 'Descrizione' in row and 'Importo' in row and float(row['Importo']) < 0:
                        # Gestisce importi negativi come spese
                        category = str(row['Descrizione'])
                        value = abs(float(row['Importo']))
                        
                        if category in expense_categories:
                            expense_categories[category] += value
                        else:
                            expense_categories[category] = value
        
        # Calcola il totale delle spese
        total_expenses = sum(expense_categories.values())
        
        # Se ci sono spese, calcola le percentuali
        if total_expenses > 0:
            return {category: (value / total_expenses) for category, value in expense_categories.items()}
            
    except Exception as e:
        logger.error(f"Errore nell'identificazione delle categorie di spesa: {e}")
    
    return {}

def get_financial_tips(financial_data: Dict[str, Any]) -> List[str]:
    """
    Genera suggerimenti finanziari basati sull'analisi dei dati.
    
    Args:
        financial_data: Dizionario contenente i dati finanziari
        
    Returns:
        List[str]: Lista di suggerimenti finanziari
    """
    tips = []
    
    try:
        # Calcola il margine di profitto
        profit_margin = calculate_profit_margin(financial_data)
        
        # Identifica le principali categorie di spesa
        expense_categories = identify_major_expense_categories(financial_data)
        
        # Genera suggerimenti basati sui dati
        if profit_margin is not None:
            if profit_margin < 0.2:  # Margine di profitto inferiore al 20%
                tips.append(f"Il margine di profitto medio è basso ({profit_margin*100:.1f}%). Considera di aumentare i prezzi o ridurre i costi.")
            elif profit_margin > 0.4:  # Margine di profitto superiore al 40%
                tips.append(f"Il margine di profitto medio è alto ({profit_margin*100:.1f}%). Potresti considerare investimenti per la crescita.")
            else:
                tips.append(f"Il margine di profitto medio del {profit_margin*100:.1f}% è in linea con le aspettative.")
        
        # Aggiungi suggerimenti sulle spese principali
        if expense_categories:
            # Ordina le categorie per percentuale
            sorted_expenses = sorted(expense_categories.items(), key=lambda x: x[1], reverse=True)
            
            # Suggerimenti per le prime 3 categorie di spesa
            for category, percentage in sorted_expenses[:3]:
                if percentage > 0.3:  # Categoria che rappresenta più del 30% delle spese
                    tips.append(f"La categoria '{category}' rappresenta il {percentage*100:.1f}% delle spese totali. Considera di ottimizzare questa voce.")
                elif percentage > 0.2:
                    tips.append(f"La categoria '{category}' rappresenta il {percentage*100:.1f}% delle spese totali. Potrebbe esserci spazio per miglioramenti.")
        
        # Aggiungi un suggerimento generale se non ci sono dati sufficienti
        if not tips:
            tips.append("Non sono stati trovati dati sufficienti per generare suggerimenti specifici. Carica dati finanziari più dettagliati.")
            
    except Exception as e:
        logger.error(f"Errore nella generazione dei suggerimenti finanziari: {e}")
        tips.append("Si è verificato un errore nell'elaborazione dei dati finanziari.")
    
    return tips

def analyze_cash_flow(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analizza i flussi di cassa dai dati finanziari.
    
    Args:
        financial_data: Dizionario contenente i dati finanziari
        
    Returns:
        Dict[str, Any]: Analisi dei flussi di cassa
    """
    analysis = {
        "positive": [],
        "negative": [],
        "summary": {}
    }
    
    try:
        if 'raw_data' in financial_data:
            # Cerca dati di tipo flusso di cassa
            for sheet in financial_data['raw_data'].values():
                for row in sheet:
                    if 'Categoria' in row and 'Importo' in row:
                        category = str(row['Categoria'])
                        amount = float(row['Importo'])
                        
                        if amount > 0:
                            analysis['positive'].append((category, amount))
                        elif amount < 0:
                            analysis['negative'].append((category, abs(amount)))
                    
                    elif 'Descrizione' in row and 'Importo' in row:
                        category = str(row['Descrizione'])
                        amount = float(row['Importo'])
                        
                        if amount > 0:
                            analysis['positive'].append((category, amount))
                        elif amount < 0:
                            analysis['negative'].append((category, abs(amount)))
            
            # Calcola il riepilogo
            total_in = sum(amount for _, amount in analysis['positive'])
            total_out = sum(amount for _, amount in analysis['negative'])
            
            analysis['summary'] = {
                "totale_entrata": total_in,
                "totale_uscita": total_out,
                "saldo_netto": total_in - total_out,
                "copertura": total_in / total_out if total_out > 0 else float('inf')
            }
            
    except Exception as e:
        logger.error(f"Errore nell'analisi dei flussi di cassa: {e}")
    
    return analysis

def get_cash_flow_tips(financial_data: Dict[str, Any]) -> List[str]:
    """
    Genera suggerimenti specifici per la gestione dei flussi di cassa.
    
    Args:
        financial_data: Dizionario contenente i dati finanziari
        
    Returns:
        List[str]: Lista di suggerimenti per la gestione dei flussi di cassa
    """
    tips = []
    
    try:
        # Analizza i flussi di cassa
        cash_flow_analysis = analyze_cash_flow(financial_data)
        
        # Genera suggerimenti basati sui flussi di cassa
        if cash_flow_analysis['summary']:
            summary = cash_flow_analysis['summary']
            
            # Analisi del saldo netto
            if summary['saldo_netto'] < 0:
                tips.append(f"Il saldo netto è negativo ({summary['saldo_netto']:.2f}€). Considera di aumentare le entrate o ridurre le uscite.")
            elif summary['saldo_netto'] > 0 and summary['saldo_netto'] < 1000:
                tips.append(f"Il saldo netto è positivo ma limitato ({summary['saldo_netto']:.2f}€). Potresti migliorare la gestione dei flussi di cassa.")
            
            # Analisi della copertura
            if summary['copertura'] < 1:
                tips.append(f"Le uscite superano le entrate. È necessario un'attenta revisione della gestione finanziaria.")
            elif summary['copertura'] < 1.2:
                tips.append(f"Le entrate coprono appena le uscite (rapporto {summary['copertura']:.1f}). Considera di aumentare le entrate o ridurre le uscite.")
            
            # Analisi delle principali entrate
            if cash_flow_analysis['positive']:
                tips.append("Le principali entrate provengono da:")
                for category, amount in sorted(cash_flow_analysis['positive'], key=lambda x: x[1], reverse=True)[:3]:
                    tips.append(f"- {category}: {amount:.2f}€")
            
            # Analisi delle principali uscite
            if cash_flow_analysis['negative']:
                tips.append("Le principali uscite sono:")
                for category, amount in sorted(cash_flow_analysis['negative'], key=lambda x: x[1], reverse=True)[:3]:
                    tips.append(f"- {category}: {amount:.2f}€")
            
    except Exception as e:
        logger.error(f"Errore nella generazione dei suggerimenti sui flussi di cassa: {e}")
    
    return tips

# Esempio di utilizzo
if __name__ == "__main__":
    # Test dei dati di esempio
    test_financial_data = {
        "raw_data": {
            "Sheet1": [
                {"Data": "2023-01-01", "Ricavi": 10000, "Costi": 6000, "Profitto": 4000},
                {"Data": "2023-02-01", "Ricavi": 12000, "Costi": 7000, "Profitto": 5000},
                {"Data": "2023-03-01", "Ricavi": 15000, "Costi": 8000, "Profitto": 7000}
            ],
            "Sheet2": [
                {"Categoria": "A", "Valore": 100},
                {"Categoria": "B", "Valore": 200},
                {"Categoria": "C", "Valore": 150}
            ]
        },
        "metadata": {
            "file_path": "test_financial_data.xlsx",
            "file_type": "xlsx",
            "import_date": "2025-05-08T18:26:00",
            "total_sheets": 2,
            "validation_passed": True
        },
        "validation_report": {
            "total_rows": 100,
            "total_columns": 5,
            "missing_values": {"Ricavi": 0, "Costi": 0, "Profitto": 0},
            "data_types": {"Data": "datetime64[ns]", "Ricavi": "float64", "Costi": "float64", "Profitto": "float64"},
            "validation_passed": True
        }
    }
    
    # Test della generazione di suggerimenti
    print("Suggerimenti finanziari:")
    for tip in get_financial_tips(test_financial_data):
        print(f"- {tip}")
    
    # Test dell'analisi dei flussi di cassa
    print("\nAnalisi dei flussi di cassa:")
    cash_flow_analysis = analyze_cash_flow(test_financial_data)
    print(f"Totale entrata: {cash_flow_analysis['summary']['totale_entrata']:.2f}€")
    print(f"Totale uscita: {cash_flow_analysis['summary']['totale_uscita']:.2f}€")
    print(f"Saldo netto: {cash_flow_analysis['summary']['saldo_netto']:.2f}€")
