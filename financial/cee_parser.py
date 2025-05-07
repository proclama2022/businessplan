#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parser per i bilanci CEE italiani.

Questo modulo fornisce funzioni per il parsing e la validazione dei bilanci CEE italiani
da vari formati (CSV, Excel, ecc.) e la loro conversione in un formato standardizzato.
"""

import os
import re
import csv
import json
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from .cee_schema import (
    FinancialAccount, BalanceSheet, IncomeStatement, FinancialStatement,
    AccountType, AccountCategory, BALANCE_SHEET_SCHEMA, INCOME_STATEMENT_SCHEMA,
    get_account_schema, is_valid_account_code
)

class CEEParseError(Exception):
    """Eccezione sollevata quando si verifica un errore nel parsing di un bilancio CEE"""
    pass

def parse_csv_financial_statement(file_path: str, delimiter: str = ',', encoding: str = 'utf-8') -> FinancialStatement:
    """
    Analizza un bilancio CEE da un file CSV.
    
    Args:
        file_path: Percorso del file CSV
        delimiter: Delimitatore del CSV
        encoding: Encoding del file
        
    Returns:
        FinancialStatement: Bilancio CEE analizzato
        
    Raises:
        CEEParseError: Se si verifica un errore nel parsing
    """
    try:
        # Leggi il file CSV
        df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)
        
        # Estrai le informazioni di base
        company_name = extract_company_name(df)
        year = extract_year(df)
        
        # Separa lo stato patrimoniale e il conto economico
        balance_sheet_df = extract_balance_sheet(df)
        income_statement_df = extract_income_statement(df)
        
        # Analizza lo stato patrimoniale
        balance_sheet = parse_balance_sheet(balance_sheet_df, company_name, year)
        
        # Analizza il conto economico
        income_statement = parse_income_statement(income_statement_df, company_name, year)
        
        # Crea il bilancio completo
        financial_statement: FinancialStatement = {
            "balance_sheet": balance_sheet,
            "income_statement": income_statement,
            "notes": None
        }
        
        return financial_statement
    except Exception as e:
        raise CEEParseError(f"Errore nel parsing del bilancio CEE da CSV: {str(e)}")

def parse_excel_financial_statement(file_path: str, sheet_name: Optional[str] = None) -> FinancialStatement:
    """
    Analizza un bilancio CEE da un file Excel.
    
    Args:
        file_path: Percorso del file Excel
        sheet_name: Nome del foglio Excel (se None, usa il primo foglio)
        
    Returns:
        FinancialStatement: Bilancio CEE analizzato
        
    Raises:
        CEEParseError: Se si verifica un errore nel parsing
    """
    try:
        # Leggi il file Excel
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_path)
        
        # Estrai le informazioni di base
        company_name = extract_company_name(df)
        year = extract_year(df)
        
        # Separa lo stato patrimoniale e il conto economico
        balance_sheet_df = extract_balance_sheet(df)
        income_statement_df = extract_income_statement(df)
        
        # Analizza lo stato patrimoniale
        balance_sheet = parse_balance_sheet(balance_sheet_df, company_name, year)
        
        # Analizza il conto economico
        income_statement = parse_income_statement(income_statement_df, company_name, year)
        
        # Crea il bilancio completo
        financial_statement: FinancialStatement = {
            "balance_sheet": balance_sheet,
            "income_statement": income_statement,
            "notes": None
        }
        
        return financial_statement
    except Exception as e:
        raise CEEParseError(f"Errore nel parsing del bilancio CEE da Excel: {str(e)}")

def extract_company_name(df: pd.DataFrame) -> str:
    """
    Estrae il nome dell'azienda dal DataFrame.
    
    Args:
        df: DataFrame contenente il bilancio
        
    Returns:
        str: Nome dell'azienda
    """
    # Cerca nelle prime righe del DataFrame
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        for col in df.columns:
            value = str(row[col]).lower()
            if any(keyword in value for keyword in ["ragione sociale", "denominazione", "azienda", "società", "company"]):
                # Cerca nella cella successiva o nella stessa cella
                if col != df.columns[-1]:
                    next_col = df.columns[df.columns.get_loc(col) + 1]
                    company_name = str(row[next_col])
                    if company_name and company_name.lower() != "nan":
                        return company_name.strip()
                
                # Estrai il nome dalla stessa cella
                match = re.search(r"(?:ragione sociale|denominazione|azienda|società|company)[:\s]+([^\n]+)", value, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
    
    # Se non trovato, usa un valore predefinito
    return "Azienda Sconosciuta"

def extract_year(df: pd.DataFrame) -> int:
    """
    Estrae l'anno di riferimento dal DataFrame.
    
    Args:
        df: DataFrame contenente il bilancio
        
    Returns:
        int: Anno di riferimento
    """
    # Cerca nelle prime righe del DataFrame
    for i in range(min(10, len(df))):
        row = df.iloc[i]
        for col in df.columns:
            value = str(row[col]).lower()
            if any(keyword in value for keyword in ["anno", "esercizio", "bilancio", "year"]):
                # Cerca numeri di 4 cifre che potrebbero essere anni
                years = re.findall(r"\b(20\d{2})\b", value)
                if years:
                    return int(years[0])
                
                # Cerca nella cella successiva
                if col != df.columns[-1]:
                    next_col = df.columns[df.columns.get_loc(col) + 1]
                    year_str = str(row[next_col])
                    years = re.findall(r"\b(20\d{2})\b", year_str)
                    if years:
                        return int(years[0])
    
    # Se non trovato, usa l'anno corrente
    import datetime
    return datetime.datetime.now().year

def extract_balance_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estrae lo stato patrimoniale dal DataFrame.
    
    Args:
        df: DataFrame contenente il bilancio
        
    Returns:
        pd.DataFrame: DataFrame contenente solo lo stato patrimoniale
    """
    # Cerca l'inizio dello stato patrimoniale
    start_row = None
    end_row = None
    
    for i in range(len(df)):
        row_str = " ".join(str(x).lower() for x in df.iloc[i].values if str(x).lower() != "nan")
        
        # Cerca l'inizio dello stato patrimoniale
        if start_row is None and any(keyword in row_str for keyword in ["stato patrimoniale", "balance sheet", "attivo"]):
            start_row = i
            continue
        
        # Cerca la fine dello stato patrimoniale (inizio del conto economico)
        if start_row is not None and any(keyword in row_str for keyword in ["conto economico", "income statement", "valore della produzione"]):
            end_row = i
            break
    
    # Se non trovato, usa valori predefiniti
    if start_row is None:
        start_row = 0
    if end_row is None:
        end_row = len(df) // 2  # Assume che lo stato patrimoniale sia nella prima metà
    
    return df.iloc[start_row:end_row].reset_index(drop=True)

def extract_income_statement(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estrae il conto economico dal DataFrame.
    
    Args:
        df: DataFrame contenente il bilancio
        
    Returns:
        pd.DataFrame: DataFrame contenente solo il conto economico
    """
    # Cerca l'inizio del conto economico
    start_row = None
    
    for i in range(len(df)):
        row_str = " ".join(str(x).lower() for x in df.iloc[i].values if str(x).lower() != "nan")
        
        # Cerca l'inizio del conto economico
        if any(keyword in row_str for keyword in ["conto economico", "income statement", "valore della produzione"]):
            start_row = i
            break
    
    # Se non trovato, usa un valore predefinito
    if start_row is None:
        start_row = len(df) // 2  # Assume che il conto economico sia nella seconda metà
    
    return df.iloc[start_row:].reset_index(drop=True)

def parse_balance_sheet(df: pd.DataFrame, company_name: str, year: int) -> BalanceSheet:
    """
    Analizza lo stato patrimoniale da un DataFrame.
    
    Args:
        df: DataFrame contenente lo stato patrimoniale
        company_name: Nome dell'azienda
        year: Anno di riferimento
        
    Returns:
        BalanceSheet: Stato patrimoniale analizzato
    """
    assets = {}
    liabilities = {}
    equity = {}
    total_assets = 0.0
    total_liabilities_equity = 0.0
    
    # Analizza le righe del DataFrame
    for i in range(len(df)):
        row = df.iloc[i]
        
        # Cerca codici di conto nello stato patrimoniale
        account_code = None
        account_name = None
        account_value = None
        account_prev_value = None
        
        # Estrai il codice del conto
        for col in df.columns:
            cell_value = str(row[col])
            if cell_value.lower() == "nan":
                continue
            
            # Cerca codici come "A", "B.I", ecc.
            if re.match(r"^[A-Z](\.[IVX]+)?$", cell_value):
                account_code = cell_value
                
                # Cerca il nome nella cella successiva
                if col != df.columns[-1]:
                    next_col = df.columns[df.columns.get_loc(col) + 1]
                    account_name = str(row[next_col])
                    if account_name.lower() == "nan":
                        account_name = None
                
                # Cerca il valore nelle celle successive
                for value_col in df.columns[df.columns.get_loc(col) + 1:]:
                    try:
                        value = str(row[value_col])
                        if value.lower() != "nan" and re.match(r"^-?\d+([.,]\d+)?$", value.replace(".", "").replace(",", ".")):
                            if account_value is None:
                                account_value = float(value.replace(".", "").replace(",", "."))
                            elif account_prev_value is None:
                                account_prev_value = float(value.replace(".", "").replace(",", "."))
                            break
                    except:
                        pass
                
                break
        
        # Se abbiamo trovato un conto valido
        if account_code and account_name and account_value is not None:
            # Verifica se è un conto valido nello schema
            schema_account = get_account_schema(account_code, "balance_sheet")
            if schema_account:
                account_type = schema_account["type"]
                account_category = schema_account["category"]
                is_total = schema_account["is_total"]
                is_subtotal = schema_account["is_subtotal"]
                parent_code = schema_account.get("parent_code")
                
                # Crea l'oggetto conto
                account: FinancialAccount = {
                    "code": account_code,
                    "name": account_name,
                    "type": account_type,
                    "category": account_category,
                    "parent_code": parent_code,
                    "is_total": is_total,
                    "is_subtotal": is_subtotal,
                    "value": account_value,
                    "previous_value": account_prev_value
                }
                
                # Aggiungi il conto alla sezione appropriata
                if account_type == AccountType.ASSET:
                    assets[account_code] = account
                    if account_code == "TOTALE ATTIVO":
                        total_assets = account_value
                elif account_type == AccountType.EQUITY:
                    equity[account_code] = account
                elif account_type == AccountType.LIABILITY:
                    liabilities[account_code] = account
                    if account_code == "TOTALE PASSIVO":
                        total_liabilities_equity = account_value
    
    # Crea lo stato patrimoniale
    balance_sheet: BalanceSheet = {
        "year": year,
        "company_name": company_name,
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "total_assets": total_assets,
        "total_liabilities_equity": total_liabilities_equity
    }
    
    return balance_sheet

def parse_income_statement(df: pd.DataFrame, company_name: str, year: int) -> IncomeStatement:
    """
    Analizza il conto economico da un DataFrame.
    
    Args:
        df: DataFrame contenente il conto economico
        company_name: Nome dell'azienda
        year: Anno di riferimento
        
    Returns:
        IncomeStatement: Conto economico analizzato
    """
    revenues = {}
    expenses = {}
    operating_result = 0.0
    financial_result = 0.0
    extraordinary_result = 0.0
    pre_tax_result = 0.0
    net_result = 0.0
    
    # Analizza le righe del DataFrame
    for i in range(len(df)):
        row = df.iloc[i]
        
        # Cerca codici di conto nel conto economico
        account_code = None
        account_name = None
        account_value = None
        account_prev_value = None
        
        # Estrai il codice del conto
        for col in df.columns:
            cell_value = str(row[col])
            if cell_value.lower() == "nan":
                continue
            
            # Cerca codici come "A", "B.6", ecc.
            if re.match(r"^[A-Z](\.\d+)?$", cell_value) or cell_value in ["20", "21"]:
                account_code = cell_value
                
                # Cerca il nome nella cella successiva
                if col != df.columns[-1]:
                    next_col = df.columns[df.columns.get_loc(col) + 1]
                    account_name = str(row[next_col])
                    if account_name.lower() == "nan":
                        account_name = None
                
                # Cerca il valore nelle celle successive
                for value_col in df.columns[df.columns.get_loc(col) + 1:]:
                    try:
                        value = str(row[value_col])
                        if value.lower() != "nan" and re.match(r"^-?\d+([.,]\d+)?$", value.replace(".", "").replace(",", ".")):
                            if account_value is None:
                                account_value = float(value.replace(".", "").replace(",", "."))
                            elif account_prev_value is None:
                                account_prev_value = float(value.replace(".", "").replace(",", "."))
                            break
                    except:
                        pass
                
                break
        
        # Se abbiamo trovato un conto valido
        if account_code and account_name and account_value is not None:
            # Verifica se è un conto valido nello schema
            schema_account = get_account_schema(account_code, "income_statement")
            if schema_account:
                account_type = schema_account["type"]
                account_category = schema_account["category"]
                is_total = schema_account["is_total"]
                is_subtotal = schema_account["is_subtotal"]
                parent_code = schema_account.get("parent_code")
                
                # Crea l'oggetto conto
                account: FinancialAccount = {
                    "code": account_code,
                    "name": account_name,
                    "type": account_type,
                    "category": account_category,
                    "parent_code": parent_code,
                    "is_total": is_total,
                    "is_subtotal": is_subtotal,
                    "value": account_value,
                    "previous_value": account_prev_value
                }
                
                # Aggiungi il conto alla sezione appropriata
                if account_type == AccountType.REVENUE:
                    revenues[account_code] = account
                    if account_code == "DIFF_A_B":
                        operating_result = account_value
                    elif account_code == "RISULTATO_ANTE_IMPOSTE":
                        pre_tax_result = account_value
                    elif account_code == "21":
                        net_result = account_value
                elif account_type == AccountType.EXPENSE:
                    expenses[account_code] = account
    
    # Crea il conto economico
    income_statement: IncomeStatement = {
        "year": year,
        "company_name": company_name,
        "revenues": revenues,
        "expenses": expenses,
        "operating_result": operating_result,
        "financial_result": financial_result,
        "extraordinary_result": extraordinary_result,
        "pre_tax_result": pre_tax_result,
        "net_result": net_result
    }
    
    return income_statement

def validate_financial_statement(statement: FinancialStatement) -> Tuple[bool, List[str]]:
    """
    Valida un bilancio CEE.
    
    Args:
        statement: Bilancio CEE da validare
        
    Returns:
        Tuple[bool, List[str]]: (valido, lista di errori)
    """
    errors = []
    
    # Valida lo stato patrimoniale
    balance_sheet = statement["balance_sheet"]
    
    # Verifica che il totale attivo sia uguale al totale passivo + patrimonio netto
    if abs(balance_sheet["total_assets"] - balance_sheet["total_liabilities_equity"]) > 0.01:
        errors.append(f"Il totale attivo ({balance_sheet['total_assets']}) non è uguale al totale passivo + patrimonio netto ({balance_sheet['total_liabilities_equity']})")
    
    # Valida il conto economico
    income_statement = statement["income_statement"]
    
    # Verifica che il risultato netto sia coerente
    calculated_net_result = income_statement["pre_tax_result"]
    for code, account in income_statement["expenses"].items():
        if code == "20":  # Imposte sul reddito
            calculated_net_result -= account["value"]
    
    if abs(income_statement["net_result"] - calculated_net_result) > 0.01:
        errors.append(f"Il risultato netto ({income_statement['net_result']}) non è coerente con il risultato ante imposte meno le imposte ({calculated_net_result})")
    
    return len(errors) == 0, errors

def export_financial_statement_to_json(statement: FinancialStatement, file_path: str) -> None:
    """
    Esporta un bilancio CEE in formato JSON.
    
    Args:
        statement: Bilancio CEE da esportare
        file_path: Percorso del file JSON
    """
    # Converti i tipi enum in stringhe
    def convert_enums(obj):
        if isinstance(obj, dict):
            return {k: convert_enums(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_enums(item) for item in obj]
        elif isinstance(obj, (AccountType, AccountCategory)):
            return obj.value
        else:
            return obj
    
    # Converti il bilancio
    converted_statement = convert_enums(statement)
    
    # Scrivi il file JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(converted_statement, f, ensure_ascii=False, indent=2)

def import_financial_statement_from_json(file_path: str) -> FinancialStatement:
    """
    Importa un bilancio CEE da un file JSON.
    
    Args:
        file_path: Percorso del file JSON
        
    Returns:
        FinancialStatement: Bilancio CEE importato
    """
    # Leggi il file JSON
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Converti le stringhe in enum
    def convert_strings_to_enums(obj):
        if isinstance(obj, dict):
            if "type" in obj and isinstance(obj["type"], str):
                obj["type"] = AccountType(obj["type"])
            if "category" in obj and isinstance(obj["category"], str):
                obj["category"] = AccountCategory(obj["category"])
            return {k: convert_strings_to_enums(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_strings_to_enums(item) for item in obj]
        else:
            return obj
    
    # Converti il bilancio
    converted_data = convert_strings_to_enums(data)
    
    return converted_data

def detect_file_type(file_path: str) -> str:
    """
    Rileva il tipo di file in base all'estensione.
    
    Args:
        file_path: Percorso del file
        
    Returns:
        str: Tipo di file ("csv", "excel", "json", "unknown")
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return "csv"
    elif ext in [".xls", ".xlsx", ".xlsm"]:
        return "excel"
    elif ext == ".json":
        return "json"
    else:
        return "unknown"

def parse_financial_statement(file_path: str, **kwargs) -> FinancialStatement:
    """
    Analizza un bilancio CEE da un file.
    
    Args:
        file_path: Percorso del file
        **kwargs: Argomenti aggiuntivi per i parser specifici
        
    Returns:
        FinancialStatement: Bilancio CEE analizzato
        
    Raises:
        CEEParseError: Se si verifica un errore nel parsing
    """
    file_type = detect_file_type(file_path)
    
    if file_type == "csv":
        delimiter = kwargs.get("delimiter", ",")
        encoding = kwargs.get("encoding", "utf-8")
        return parse_csv_financial_statement(file_path, delimiter, encoding)
    elif file_type == "excel":
        sheet_name = kwargs.get("sheet_name", None)
        return parse_excel_financial_statement(file_path, sheet_name)
    elif file_type == "json":
        return import_financial_statement_from_json(file_path)
    else:
        raise CEEParseError(f"Tipo di file non supportato: {file_type}")
