#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Importatore di dati finanziari per il business plan builder.

Questo modulo fornisce funzioni per importare dati finanziari da varie fonti
e convertirli in un formato utilizzabile dal business plan builder.
"""

import os
import json
import tempfile
from typing import Dict, List, Optional, Any, Union, BinaryIO
import pandas as pd

from .cee_schema import FinancialStatement
from .cee_parser import parse_financial_statement, CEEParseError, validate_financial_statement

class FinancialImportError(Exception):
    """Eccezione sollevata quando si verifica un errore nell'importazione di dati finanziari"""
    pass

def import_financial_data(file: Union[str, BinaryIO], file_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Importa dati finanziari da un file.
    
    Args:
        file: Percorso del file o oggetto file
        file_name: Nome del file (usato se file è un oggetto file)
        **kwargs: Argomenti aggiuntivi per i parser specifici
        
    Returns:
        Dict[str, Any]: Dati finanziari importati
        
    Raises:
        FinancialImportError: Se si verifica un errore nell'importazione
    """
    try:
        # Se file è un oggetto file (ad es. da Streamlit), salvalo temporaneamente
        if not isinstance(file, str):
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name or "")[1]) as tmp:
                if hasattr(file, 'read'):
                    # Se è un file-like object
                    tmp.write(file.read())
                else:
                    # Se è un bytes object
                    tmp.write(file)
                tmp_path = tmp.name
            
            try:
                return import_financial_data_from_path(tmp_path, **kwargs)
            finally:
                # Rimuovi il file temporaneo
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        else:
            # Se file è un percorso
            return import_financial_data_from_path(file, **kwargs)
    except Exception as e:
        raise FinancialImportError(f"Errore nell'importazione dei dati finanziari: {str(e)}")

def import_financial_data_from_path(file_path: str, **kwargs) -> Dict[str, Any]:
    """
    Importa dati finanziari da un percorso file.
    
    Args:
        file_path: Percorso del file
        **kwargs: Argomenti aggiuntivi per i parser specifici
        
    Returns:
        Dict[str, Any]: Dati finanziari importati
        
    Raises:
        FinancialImportError: Se si verifica un errore nell'importazione
    """
    try:
        # Analizza il bilancio
        financial_statement = parse_financial_statement(file_path, **kwargs)
        
        # Valida il bilancio
        is_valid, errors = validate_financial_statement(financial_statement)
        
        # Converti il bilancio in un formato utilizzabile dal business plan builder
        financial_data = convert_financial_statement_to_business_plan_data(financial_statement)
        
        # Aggiungi informazioni sulla validazione
        financial_data["validation"] = {
            "is_valid": is_valid,
            "errors": errors
        }
        
        return financial_data
    except Exception as e:
        raise FinancialImportError(f"Errore nell'importazione dei dati finanziari: {str(e)}")

def convert_financial_statement_to_business_plan_data(statement: FinancialStatement) -> Dict[str, Any]:
    """
    Converte un bilancio CEE in dati utilizzabili dal business plan builder.
    
    Args:
        statement: Bilancio CEE
        
    Returns:
        Dict[str, Any]: Dati finanziari per il business plan
    """
    balance_sheet = statement["balance_sheet"]
    income_statement = statement["income_statement"]
    
    # Estrai i dati principali
    company_name = balance_sheet["company_name"]
    year = balance_sheet["year"]
    
    # Crea la struttura dei dati finanziari
    financial_data = {
        "company_name": company_name,
        "year": year,
        "balance_sheet": {
            "assets": {},
            "liabilities": {},
            "equity": {}
        },
        "income_statement": {
            "revenues": {},
            "expenses": {}
        },
        "key_metrics": calculate_key_metrics(statement),
        "raw_data": {
            "balance_sheet": balance_sheet,
            "income_statement": income_statement
        }
    }
    
    # Popola lo stato patrimoniale
    for code, account in balance_sheet["assets"].items():
        financial_data["balance_sheet"]["assets"][code] = {
            "name": account["name"],
            "value": account["value"],
            "previous_value": account["previous_value"],
            "is_total": account["is_total"],
            "is_subtotal": account["is_subtotal"]
        }
    
    for code, account in balance_sheet["liabilities"].items():
        financial_data["balance_sheet"]["liabilities"][code] = {
            "name": account["name"],
            "value": account["value"],
            "previous_value": account["previous_value"],
            "is_total": account["is_total"],
            "is_subtotal": account["is_subtotal"]
        }
    
    for code, account in balance_sheet["equity"].items():
        financial_data["balance_sheet"]["equity"][code] = {
            "name": account["name"],
            "value": account["value"],
            "previous_value": account["previous_value"],
            "is_total": account["is_total"],
            "is_subtotal": account["is_subtotal"]
        }
    
    # Popola il conto economico
    for code, account in income_statement["revenues"].items():
        financial_data["income_statement"]["revenues"][code] = {
            "name": account["name"],
            "value": account["value"],
            "previous_value": account["previous_value"],
            "is_total": account["is_total"],
            "is_subtotal": account["is_subtotal"]
        }
    
    for code, account in income_statement["expenses"].items():
        financial_data["income_statement"]["expenses"][code] = {
            "name": account["name"],
            "value": account["value"],
            "previous_value": account["previous_value"],
            "is_total": account["is_total"],
            "is_subtotal": account["is_subtotal"]
        }
    
    # Aggiungi i totali
    financial_data["balance_sheet"]["total_assets"] = balance_sheet["total_assets"]
    financial_data["balance_sheet"]["total_liabilities_equity"] = balance_sheet["total_liabilities_equity"]
    financial_data["income_statement"]["operating_result"] = income_statement["operating_result"]
    financial_data["income_statement"]["financial_result"] = income_statement["financial_result"]
    financial_data["income_statement"]["extraordinary_result"] = income_statement["extraordinary_result"]
    financial_data["income_statement"]["pre_tax_result"] = income_statement["pre_tax_result"]
    financial_data["income_statement"]["net_result"] = income_statement["net_result"]
    
    return financial_data

def calculate_key_metrics(statement: FinancialStatement) -> Dict[str, Any]:
    """
    Calcola le metriche chiave da un bilancio CEE.
    
    Args:
        statement: Bilancio CEE
        
    Returns:
        Dict[str, Any]: Metriche chiave
    """
    balance_sheet = statement["balance_sheet"]
    income_statement = statement["income_statement"]
    
    # Estrai i valori principali
    total_assets = balance_sheet["total_assets"]
    
    # Trova il patrimonio netto totale
    equity_total = 0.0
    for code, account in balance_sheet["equity"].items():
        if code == "A.P":  # Patrimonio netto
            equity_total = account["value"]
            break
    
    # Trova i debiti totali
    debt_total = 0.0
    for code, account in balance_sheet["liabilities"].items():
        if code == "D.P":  # Debiti
            debt_total = account["value"]
            break
    
    # Trova l'attivo circolante
    current_assets = 0.0
    for code, account in balance_sheet["assets"].items():
        if code == "C":  # Attivo circolante
            current_assets = account["value"]
            break
    
    # Trova le passività correnti (approssimazione)
    current_liabilities = 0.0
    for code, account in balance_sheet["liabilities"].items():
        if code == "D.P":  # Debiti (approssimazione delle passività correnti)
            current_liabilities = account["value"]
            break
    
    # Trova i ricavi
    revenues = 0.0
    for code, account in income_statement["revenues"].items():
        if code == "A.1":  # Ricavi delle vendite e delle prestazioni
            revenues = account["value"]
            break
    
    # Calcola le metriche
    metrics = {
        "profitability": {
            "net_profit_margin": income_statement["net_result"] / revenues if revenues else 0,
            "return_on_assets": income_statement["net_result"] / total_assets if total_assets else 0,
            "return_on_equity": income_statement["net_result"] / equity_total if equity_total else 0
        },
        "liquidity": {
            "current_ratio": current_assets / current_liabilities if current_liabilities else 0,
            "quick_ratio": (current_assets - get_inventory_value(balance_sheet)) / current_liabilities if current_liabilities else 0
        },
        "solvency": {
            "debt_to_equity": debt_total / equity_total if equity_total else 0,
            "debt_to_assets": debt_total / total_assets if total_assets else 0,
            "interest_coverage": get_interest_coverage(income_statement)
        },
        "efficiency": {
            "asset_turnover": revenues / total_assets if total_assets else 0,
            "inventory_turnover": get_inventory_turnover(income_statement, balance_sheet)
        }
    }
    
    return metrics

def get_inventory_value(balance_sheet: Dict[str, Any]) -> float:
    """
    Ottiene il valore delle rimanenze dallo stato patrimoniale.
    
    Args:
        balance_sheet: Stato patrimoniale
        
    Returns:
        float: Valore delle rimanenze
    """
    for code, account in balance_sheet["assets"].items():
        if code == "C.I":  # Rimanenze
            return account["value"]
    return 0.0

def get_interest_coverage(income_statement: Dict[str, Any]) -> float:
    """
    Calcola l'indice di copertura degli interessi.
    
    Args:
        income_statement: Conto economico
        
    Returns:
        float: Indice di copertura degli interessi
    """
    # Trova il risultato operativo
    operating_result = income_statement["operating_result"]
    
    # Trova gli oneri finanziari
    interest_expense = 0.0
    for code, account in income_statement["expenses"].items():
        if code == "C":  # Proventi e oneri finanziari (approssimazione)
            interest_expense = -account["value"] if account["value"] < 0 else 0
            break
    
    return operating_result / interest_expense if interest_expense else float('inf')

def get_inventory_turnover(income_statement: Dict[str, Any], balance_sheet: Dict[str, Any]) -> float:
    """
    Calcola l'indice di rotazione delle rimanenze.
    
    Args:
        income_statement: Conto economico
        balance_sheet: Stato patrimoniale
        
    Returns:
        float: Indice di rotazione delle rimanenze
    """
    # Trova il costo del venduto (approssimazione)
    cost_of_goods_sold = 0.0
    for code, account in income_statement["expenses"].items():
        if code == "B.6":  # Costi per materie prime
            cost_of_goods_sold += account["value"]
    
    # Trova le rimanenze
    inventory = get_inventory_value(balance_sheet)
    
    return cost_of_goods_sold / inventory if inventory else 0.0
