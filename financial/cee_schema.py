#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Schema per i bilanci CEE italiani.

Questo modulo definisce la struttura dei bilanci CEE italiani secondo la normativa vigente,
includendo sia lo Stato Patrimoniale che il Conto Economico.
"""

from typing import Dict, List, Optional, Any, TypedDict
from enum import Enum

class AccountType(Enum):
    """Tipo di conto nel bilancio CEE"""
    ASSET = "asset"  # Attività
    LIABILITY = "liability"  # Passività
    EQUITY = "equity"  # Patrimonio netto
    REVENUE = "revenue"  # Ricavi
    EXPENSE = "expense"  # Costi

class AccountCategory(Enum):
    """Categoria di conto nel bilancio CEE"""
    # Stato Patrimoniale - Attivo
    FIXED_ASSETS = "immobilizzazioni"  # Immobilizzazioni
    CURRENT_ASSETS = "attivo_circolante"  # Attivo circolante
    ACCRUALS_DEFERRALS_ASSETS = "ratei_risconti_attivi"  # Ratei e risconti attivi
    
    # Stato Patrimoniale - Passivo
    EQUITY = "patrimonio_netto"  # Patrimonio netto
    PROVISIONS = "fondi_rischi_oneri"  # Fondi per rischi e oneri
    SEVERANCE_PAY = "tfr"  # Trattamento di fine rapporto
    DEBTS = "debiti"  # Debiti
    ACCRUALS_DEFERRALS_LIABILITIES = "ratei_risconti_passivi"  # Ratei e risconti passivi
    
    # Conto Economico
    PRODUCTION_VALUE = "valore_produzione"  # Valore della produzione
    PRODUCTION_COSTS = "costi_produzione"  # Costi della produzione
    FINANCIAL_INCOME_EXPENSES = "proventi_oneri_finanziari"  # Proventi e oneri finanziari
    VALUE_ADJUSTMENTS = "rettifiche_valore"  # Rettifiche di valore
    EXTRAORDINARY_ITEMS = "proventi_oneri_straordinari"  # Proventi e oneri straordinari
    INCOME_TAXES = "imposte"  # Imposte sul reddito

class FinancialAccount(TypedDict):
    """Rappresentazione di un conto nel bilancio CEE"""
    code: str  # Codice del conto (es. "A.I.1")
    name: str  # Nome del conto
    type: AccountType  # Tipo di conto
    category: AccountCategory  # Categoria di conto
    parent_code: Optional[str]  # Codice del conto padre
    is_total: bool  # Se il conto è un totale
    is_subtotal: bool  # Se il conto è un subtotale
    value: float  # Valore del conto
    previous_value: Optional[float]  # Valore dell'anno precedente

class BalanceSheet(TypedDict):
    """Rappresentazione dello Stato Patrimoniale"""
    year: int  # Anno di riferimento
    company_name: str  # Nome dell'azienda
    assets: Dict[str, FinancialAccount]  # Attività
    liabilities: Dict[str, FinancialAccount]  # Passività
    equity: Dict[str, FinancialAccount]  # Patrimonio netto
    total_assets: float  # Totale attività
    total_liabilities_equity: float  # Totale passività e patrimonio netto

class IncomeStatement(TypedDict):
    """Rappresentazione del Conto Economico"""
    year: int  # Anno di riferimento
    company_name: str  # Nome dell'azienda
    revenues: Dict[str, FinancialAccount]  # Ricavi
    expenses: Dict[str, FinancialAccount]  # Costi
    operating_result: float  # Risultato operativo
    financial_result: float  # Risultato finanziario
    extraordinary_result: float  # Risultato straordinario
    pre_tax_result: float  # Risultato prima delle imposte
    net_result: float  # Risultato netto

class FinancialStatement(TypedDict):
    """Rappresentazione completa del bilancio CEE"""
    balance_sheet: BalanceSheet  # Stato Patrimoniale
    income_statement: IncomeStatement  # Conto Economico
    notes: Optional[str]  # Note al bilancio

# Schema dello Stato Patrimoniale CEE
BALANCE_SHEET_SCHEMA = {
    # ATTIVO
    "A": {"code": "A", "name": "CREDITI VERSO SOCI", "type": AccountType.ASSET, "category": AccountCategory.FIXED_ASSETS, "is_total": False, "is_subtotal": True},
    "B": {"code": "B", "name": "IMMOBILIZZAZIONI", "type": AccountType.ASSET, "category": AccountCategory.FIXED_ASSETS, "is_total": False, "is_subtotal": True},
    "B.I": {"code": "B.I", "name": "Immobilizzazioni immateriali", "type": AccountType.ASSET, "category": AccountCategory.FIXED_ASSETS, "parent_code": "B", "is_total": False, "is_subtotal": True},
    "B.II": {"code": "B.II", "name": "Immobilizzazioni materiali", "type": AccountType.ASSET, "category": AccountCategory.FIXED_ASSETS, "parent_code": "B", "is_total": False, "is_subtotal": True},
    "B.III": {"code": "B.III", "name": "Immobilizzazioni finanziarie", "type": AccountType.ASSET, "category": AccountCategory.FIXED_ASSETS, "parent_code": "B", "is_total": False, "is_subtotal": True},
    "C": {"code": "C", "name": "ATTIVO CIRCOLANTE", "type": AccountType.ASSET, "category": AccountCategory.CURRENT_ASSETS, "is_total": False, "is_subtotal": True},
    "C.I": {"code": "C.I", "name": "Rimanenze", "type": AccountType.ASSET, "category": AccountCategory.CURRENT_ASSETS, "parent_code": "C", "is_total": False, "is_subtotal": True},
    "C.II": {"code": "C.II", "name": "Crediti", "type": AccountType.ASSET, "category": AccountCategory.CURRENT_ASSETS, "parent_code": "C", "is_total": False, "is_subtotal": True},
    "C.III": {"code": "C.III", "name": "Attività finanziarie", "type": AccountType.ASSET, "category": AccountCategory.CURRENT_ASSETS, "parent_code": "C", "is_total": False, "is_subtotal": True},
    "C.IV": {"code": "C.IV", "name": "Disponibilità liquide", "type": AccountType.ASSET, "category": AccountCategory.CURRENT_ASSETS, "parent_code": "C", "is_total": False, "is_subtotal": True},
    "D": {"code": "D", "name": "RATEI E RISCONTI", "type": AccountType.ASSET, "category": AccountCategory.ACCRUALS_DEFERRALS_ASSETS, "is_total": False, "is_subtotal": True},
    "TOTALE ATTIVO": {"code": "TOTALE ATTIVO", "name": "TOTALE ATTIVO", "type": AccountType.ASSET, "category": None, "is_total": True, "is_subtotal": False},
    
    # PASSIVO
    "A.P": {"code": "A", "name": "PATRIMONIO NETTO", "type": AccountType.EQUITY, "category": AccountCategory.EQUITY, "is_total": False, "is_subtotal": True},
    "A.I.P": {"code": "A.I", "name": "Capitale", "type": AccountType.EQUITY, "category": AccountCategory.EQUITY, "parent_code": "A.P", "is_total": False, "is_subtotal": False},
    "A.II.P": {"code": "A.II", "name": "Riserva da sovrapprezzo", "type": AccountType.EQUITY, "category": AccountCategory.EQUITY, "parent_code": "A.P", "is_total": False, "is_subtotal": False},
    "A.III.P": {"code": "A.III", "name": "Riserve di rivalutazione", "type": AccountType.EQUITY, "category": AccountCategory.EQUITY, "parent_code": "A.P", "is_total": False, "is_subtotal": False},
    "A.IV.P": {"code": "A.IV", "name": "Riserva legale", "type": AccountType.EQUITY, "category": AccountCategory.EQUITY, "parent_code": "A.P", "is_total": False, "is_subtotal": False},
    "A.V.P": {"code": "A.V", "name": "Riserve statutarie", "type": AccountType.EQUITY, "category": AccountCategory.EQUITY, "parent_code": "A.P", "is_total": False, "is_subtotal": False},
    "A.VI.P": {"code": "A.VI", "name": "Altre riserve", "type": AccountType.EQUITY, "category": AccountCategory.EQUITY, "parent_code": "A.P", "is_total": False, "is_subtotal": False},
    "A.VII.P": {"code": "A.VII", "name": "Riserva operazioni copertura flussi finanziari attesi", "type": AccountType.EQUITY, "category": AccountCategory.EQUITY, "parent_code": "A.P", "is_total": False, "is_subtotal": False},
    "A.VIII.P": {"code": "A.VIII", "name": "Utili (perdite) portati a nuovo", "type": AccountType.EQUITY, "category": AccountCategory.EQUITY, "parent_code": "A.P", "is_total": False, "is_subtotal": False},
    "A.IX.P": {"code": "A.IX", "name": "Utile (perdita) dell'esercizio", "type": AccountType.EQUITY, "category": AccountCategory.EQUITY, "parent_code": "A.P", "is_total": False, "is_subtotal": False},
    "A.X.P": {"code": "A.X", "name": "Riserva negativa per azioni proprie in portafoglio", "type": AccountType.EQUITY, "category": AccountCategory.EQUITY, "parent_code": "A.P", "is_total": False, "is_subtotal": False},
    "B.P": {"code": "B", "name": "FONDI PER RISCHI E ONERI", "type": AccountType.LIABILITY, "category": AccountCategory.PROVISIONS, "is_total": False, "is_subtotal": True},
    "C.P": {"code": "C", "name": "TRATTAMENTO DI FINE RAPPORTO", "type": AccountType.LIABILITY, "category": AccountCategory.SEVERANCE_PAY, "is_total": False, "is_subtotal": True},
    "D.P": {"code": "D", "name": "DEBITI", "type": AccountType.LIABILITY, "category": AccountCategory.DEBTS, "is_total": False, "is_subtotal": True},
    "E.P": {"code": "E", "name": "RATEI E RISCONTI", "type": AccountType.LIABILITY, "category": AccountCategory.ACCRUALS_DEFERRALS_LIABILITIES, "is_total": False, "is_subtotal": True},
    "TOTALE PASSIVO": {"code": "TOTALE PASSIVO", "name": "TOTALE PASSIVO", "type": AccountType.LIABILITY, "category": None, "is_total": True, "is_subtotal": False},
}

# Schema del Conto Economico CEE
INCOME_STATEMENT_SCHEMA = {
    "A": {"code": "A", "name": "VALORE DELLA PRODUZIONE", "type": AccountType.REVENUE, "category": AccountCategory.PRODUCTION_VALUE, "is_total": False, "is_subtotal": True},
    "A.1": {"code": "A.1", "name": "Ricavi delle vendite e delle prestazioni", "type": AccountType.REVENUE, "category": AccountCategory.PRODUCTION_VALUE, "parent_code": "A", "is_total": False, "is_subtotal": False},
    "A.2": {"code": "A.2", "name": "Variazioni delle rimanenze di prodotti", "type": AccountType.REVENUE, "category": AccountCategory.PRODUCTION_VALUE, "parent_code": "A", "is_total": False, "is_subtotal": False},
    "A.3": {"code": "A.3", "name": "Variazioni dei lavori in corso su ordinazione", "type": AccountType.REVENUE, "category": AccountCategory.PRODUCTION_VALUE, "parent_code": "A", "is_total": False, "is_subtotal": False},
    "A.4": {"code": "A.4", "name": "Incrementi di immobilizzazioni per lavori interni", "type": AccountType.REVENUE, "category": AccountCategory.PRODUCTION_VALUE, "parent_code": "A", "is_total": False, "is_subtotal": False},
    "A.5": {"code": "A.5", "name": "Altri ricavi e proventi", "type": AccountType.REVENUE, "category": AccountCategory.PRODUCTION_VALUE, "parent_code": "A", "is_total": False, "is_subtotal": False},
    "B": {"code": "B", "name": "COSTI DELLA PRODUZIONE", "type": AccountType.EXPENSE, "category": AccountCategory.PRODUCTION_COSTS, "is_total": False, "is_subtotal": True},
    "B.6": {"code": "B.6", "name": "Per materie prime, sussidiarie, di consumo e merci", "type": AccountType.EXPENSE, "category": AccountCategory.PRODUCTION_COSTS, "parent_code": "B", "is_total": False, "is_subtotal": False},
    "B.7": {"code": "B.7", "name": "Per servizi", "type": AccountType.EXPENSE, "category": AccountCategory.PRODUCTION_COSTS, "parent_code": "B", "is_total": False, "is_subtotal": False},
    "B.8": {"code": "B.8", "name": "Per godimento di beni di terzi", "type": AccountType.EXPENSE, "category": AccountCategory.PRODUCTION_COSTS, "parent_code": "B", "is_total": False, "is_subtotal": False},
    "B.9": {"code": "B.9", "name": "Per il personale", "type": AccountType.EXPENSE, "category": AccountCategory.PRODUCTION_COSTS, "parent_code": "B", "is_total": False, "is_subtotal": True},
    "B.10": {"code": "B.10", "name": "Ammortamenti e svalutazioni", "type": AccountType.EXPENSE, "category": AccountCategory.PRODUCTION_COSTS, "parent_code": "B", "is_total": False, "is_subtotal": True},
    "B.11": {"code": "B.11", "name": "Variazioni delle rimanenze", "type": AccountType.EXPENSE, "category": AccountCategory.PRODUCTION_COSTS, "parent_code": "B", "is_total": False, "is_subtotal": False},
    "B.12": {"code": "B.12", "name": "Accantonamenti per rischi", "type": AccountType.EXPENSE, "category": AccountCategory.PRODUCTION_COSTS, "parent_code": "B", "is_total": False, "is_subtotal": False},
    "B.13": {"code": "B.13", "name": "Altri accantonamenti", "type": AccountType.EXPENSE, "category": AccountCategory.PRODUCTION_COSTS, "parent_code": "B", "is_total": False, "is_subtotal": False},
    "B.14": {"code": "B.14", "name": "Oneri diversi di gestione", "type": AccountType.EXPENSE, "category": AccountCategory.PRODUCTION_COSTS, "parent_code": "B", "is_total": False, "is_subtotal": False},
    "DIFF_A_B": {"code": "DIFF_A_B", "name": "Differenza tra valore e costi della produzione (A-B)", "type": AccountType.REVENUE, "category": None, "is_total": True, "is_subtotal": False},
    "C": {"code": "C", "name": "PROVENTI E ONERI FINANZIARI", "type": AccountType.REVENUE, "category": AccountCategory.FINANCIAL_INCOME_EXPENSES, "is_total": False, "is_subtotal": True},
    "D": {"code": "D", "name": "RETTIFICHE DI VALORE DI ATTIVITÀ FINANZIARIE", "type": AccountType.REVENUE, "category": AccountCategory.VALUE_ADJUSTMENTS, "is_total": False, "is_subtotal": True},
    "RISULTATO_ANTE_IMPOSTE": {"code": "RISULTATO_ANTE_IMPOSTE", "name": "Risultato prima delle imposte", "type": AccountType.REVENUE, "category": None, "is_total": True, "is_subtotal": False},
    "20": {"code": "20", "name": "Imposte sul reddito dell'esercizio", "type": AccountType.EXPENSE, "category": AccountCategory.INCOME_TAXES, "is_total": False, "is_subtotal": False},
    "21": {"code": "21", "name": "Utile (perdita) dell'esercizio", "type": AccountType.REVENUE, "category": None, "is_total": True, "is_subtotal": False},
}

# Funzioni di utilità per lavorare con lo schema

def get_account_schema(account_code: str, statement_type: str = "balance_sheet") -> Optional[Dict[str, Any]]:
    """
    Ottiene lo schema di un conto dal codice.
    
    Args:
        account_code: Codice del conto
        statement_type: Tipo di bilancio ("balance_sheet" o "income_statement")
        
    Returns:
        Schema del conto o None se non trovato
    """
    if statement_type == "balance_sheet":
        return BALANCE_SHEET_SCHEMA.get(account_code)
    elif statement_type == "income_statement":
        return INCOME_STATEMENT_SCHEMA.get(account_code)
    return None

def get_parent_accounts(account_code: str, statement_type: str = "balance_sheet") -> List[Dict[str, Any]]:
    """
    Ottiene tutti i conti padre di un conto.
    
    Args:
        account_code: Codice del conto
        statement_type: Tipo di bilancio ("balance_sheet" o "income_statement")
        
    Returns:
        Lista di conti padre
    """
    result = []
    schema = get_account_schema(account_code, statement_type)
    if not schema:
        return result
    
    parent_code = schema.get("parent_code")
    while parent_code:
        parent_schema = get_account_schema(parent_code, statement_type)
        if parent_schema:
            result.append(parent_schema)
            parent_code = parent_schema.get("parent_code")
        else:
            break
    
    return result

def get_child_accounts(account_code: str, statement_type: str = "balance_sheet") -> List[Dict[str, Any]]:
    """
    Ottiene tutti i conti figli di un conto.
    
    Args:
        account_code: Codice del conto
        statement_type: Tipo di bilancio ("balance_sheet" o "income_statement")
        
    Returns:
        Lista di conti figli
    """
    result = []
    schema = BALANCE_SHEET_SCHEMA if statement_type == "balance_sheet" else INCOME_STATEMENT_SCHEMA
    
    for code, account in schema.items():
        if account.get("parent_code") == account_code:
            result.append(account)
    
    return result

def is_valid_account_code(account_code: str, statement_type: str = "balance_sheet") -> bool:
    """
    Verifica se un codice di conto è valido.
    
    Args:
        account_code: Codice del conto
        statement_type: Tipo di bilancio ("balance_sheet" o "income_statement")
        
    Returns:
        True se il codice è valido, False altrimenti
    """
    return get_account_schema(account_code, statement_type) is not None
