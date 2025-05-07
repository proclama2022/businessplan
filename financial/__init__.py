#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo per la gestione dei dati finanziari nel business plan builder.

Questo modulo fornisce funzionalità per importare, analizzare e visualizzare
dati finanziari, con particolare attenzione ai bilanci CEE italiani.
"""

from .cee_schema import (
    AccountType, AccountCategory, FinancialAccount, 
    BalanceSheet, IncomeStatement, FinancialStatement,
    BALANCE_SHEET_SCHEMA, INCOME_STATEMENT_SCHEMA
)

from .cee_parser import (
    parse_financial_statement, parse_csv_financial_statement,
    parse_excel_financial_statement, validate_financial_statement,
    export_financial_statement_to_json, import_financial_statement_from_json,
    CEEParseError
)

from .financial_importer import (
    import_financial_data, import_financial_data_from_path,
    convert_financial_statement_to_business_plan_data,
    FinancialImportError
)

from .financial_analyzer import (
    analyze_financial_data, generate_financial_insights,
    generate_financial_projections, generate_financial_recommendations,
    generate_financial_plan_section, FinancialAnalysisError
)

__all__ = [
    # cee_schema
    'AccountType', 'AccountCategory', 'FinancialAccount',
    'BalanceSheet', 'IncomeStatement', 'FinancialStatement',
    'BALANCE_SHEET_SCHEMA', 'INCOME_STATEMENT_SCHEMA',
    
    # cee_parser
    'parse_financial_statement', 'parse_csv_financial_statement',
    'parse_excel_financial_statement', 'validate_financial_statement',
    'export_financial_statement_to_json', 'import_financial_statement_from_json',
    'CEEParseError',
    
    # financial_importer
    'import_financial_data', 'import_financial_data_from_path',
    'convert_financial_statement_to_business_plan_data',
    'FinancialImportError',
    
    # financial_analyzer
    'analyze_financial_data', 'generate_financial_insights',
    'generate_financial_projections', 'generate_financial_recommendations',
    'generate_financial_plan_section', 'FinancialAnalysisError'
]
