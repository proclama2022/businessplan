#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo per l'importazione dei dati finanziari.

Questo modulo fornisce funzionalità per importare dati finanziari da diversi formati
come Excel, CSV e PDF, e convertirli in un formato strutturato utilizzabile
dall'applicazione.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import logging
import os
import tempfile
import PyPDF2
from datetime import datetime

# Configurazione del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialImportError(Exception):
    """Eccezione base per gli errori nell'importazione dei dati finanziari."""
    pass

class FileFormatError(FinancialImportError):
    """Eccezione per formati di file non supportati."""
    pass

class DataValidationError(FinancialImportError):
    """Eccezione per dati finanziari non validi."""
    pass

@dataclass
class FinancialData:
    """Classe per rappresentare i dati finanziari strutturati."""
    raw_data: Dict[str, Any]
    metadata: Dict[str, Any]
    validation_report: Dict[str, Any]

def validate_financial_data(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Valida i dati finanziari e genera un report di validazione.

    Args:
        data: DataFrame con i dati finanziari da validare

    Returns:
        Dict con il report di validazione
    """
    report = {
        "total_rows": len(data),
        "total_columns": len(data.columns),
        "missing_values": {},
        "data_types": {},
        "validation_passed": True
    }

    # Verifica valori mancanti
    missing = data.isnull().sum()
    report["missing_values"] = {col: int(missing[col]) for col in data.columns}

    # Verifica tipi di dati
    for col, dtype in data.dtypes.items():
        report["data_types"][col] = str(dtype)
        # Se una colonna che dovrebbe essere numerica contiene stringhe
        if any(keyword in col.lower() for keyword in ['importo', 'costo', 'ricavo', 'profitto']):
            if not np.issubdtype(dtype, np.number):
                report["validation_passed"] = False
                logger.warning(f"Colonna finanziaria '{col}' non contiene dati numerici")

    return report

def import_excel_data(file_path: str) -> Dict[str, Any]:
    """
    Importa dati finanziari da un file Excel.

    Args:
        file_path: Percorso del file Excel

    Returns:
        Dict con i dati importati
    """
    try:
        # Leggi tutte le sheet
        xls = pd.ExcelFile(file_path)
        data = {sheet_name: pd.read_excel(xls, sheet_name) for sheet_name in xls.sheet_names}

        # Converte i DataFrame in dizionari per la serializzazione
        return {sheet: df.to_dict(orient='records') for sheet, df in data.items()}
    except Exception as e:
        logger.error(f"Errore nell'importazione da Excel: {e}")
        raise FinancialImportError(f"Impossibile leggere il file Excel: {e}")

def import_csv_data(file_path: str) -> Dict[str, Any]:
    """
    Importa dati finanziari da un file CSV.

    Args:
        file_path: Percorso del file CSV

    Returns:
        Dict con i dati importati
    """
    try:
        # Leggi il file CSV
        df = pd.read_csv(file_path)

        # Converte il DataFrame in dizionario
        return {"default": df.to_dict(orient='records')}
    except Exception as e:
        logger.error(f"Errore nell'importazione da CSV: {e}")
        raise FinancialImportError(f"Impossibile leggere il file CSV: {e}")

def extract_text_from_pdf(file_path: str) -> str:
    """
    Estrae il testo da un file PDF.

    Args:
        file_path: Percorso del file PDF

    Returns:
        Stringa con il testo estratto
    """
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ''
            for page in pdf_reader.pages:
                text += page.extract_text() + '\n'
            return text
    except Exception as e:
        logger.error(f"Errore nell'estrazione del testo dal PDF: {e}")
        raise FinancialImportError(f"Impossibile leggere il file PDF: {e}")

def import_financial_data(file_path: str, file_type: Optional[str] = None) -> FinancialData:
    """
    Importa dati finanziari da un file e li converte in un formato strutturato.

    Args:
        file_path: Percorso del file da cui importare i dati
        file_type: Tipo del file (opzionale, verrà dedotto dall'estensione se non fornito)

    Returns:
        Oggetto FinancialData con i dati importati
    """
    # Determina il tipo di file se non specificato
    if not file_type:
        _, file_extension = os.path.splitext(file_path.lower())
        file_type = file_extension[1:]  # Rimuove il punto iniziale

    try:
        # Importa i dati in base al tipo di file
        if file_type in ['xls', 'xlsx']:
            raw_data = import_excel_data(file_path)
        elif file_type == 'csv':
            raw_data = import_csv_data(file_path)
        elif file_type == 'pdf':
            raw_data = {"text": extract_text_from_pdf(file_path)}
        else:
            raise FileFormatError(f"Formato di file non supportato: {file_type}")

        # Se i dati sono in formato testuale (PDF), prova a estrarre informazioni finanziarie
        if file_type == 'pdf' and isinstance(raw_data, dict) and 'text' in raw_data:
            # TODO: Implementare un parser specifico per documenti finanziari PDF
            # Questo è un placeholder per la logica di estrazione
            pass

        # Valida i dati importati
        validation_report = {"validation_passed": True}

        # Se ci sono dati strutturati (non solo testo), esegui la validazione
        if any(key != 'text' for key in raw_data.keys()):
            # Prendi il primo sheet o dataset per la validazione
            first_sheet = next(iter(raw_data.values())) if raw_data else []
            if first_sheet:
                # Converte in DataFrame per la validazione
                df = pd.DataFrame(first_sheet)
                validation_report = validate_financial_data(df)

        # Crea i metadati
        metadata = {
            "file_path": file_path,
            "file_type": file_type,
            "import_date": datetime.now().isoformat(),
            "total_sheets": len(raw_data) if isinstance(raw_data, dict) else 1,
            "validation_passed": validation_report["validation_passed"]
        }

        return FinancialData(
            raw_data=raw_data,
            metadata=metadata,
            validation_report=validation_report
        )

    except FinancialImportError:
        # Rilancia le eccezioni definite in questo modulo
        raise
    except Exception as e:
        logger.error(f"Errore imprevisto durante l'importazione: {e}")
        raise FinancialImportError(f"Errore imprevisto durante l'importazione: {e}")

# Funzioni di utilità per l'integrazione con il business plan
def get_financial_summary(financial_data: FinancialData) -> Dict[str, Any]:
    """
    Genera un riepilogo dei dati finanziari.

    Args:
        financial_data: Oggetto FinancialData con i dati

    Returns:
        Dict con il riepilogo
    """
    summary = {
        "metadata": financial_data.metadata,
        "validation": financial_data.validation_report,
        "data_preview": {}
    }

    # Aggiunge un'anteprima dei dati
    for sheet_name, data in financial_data.raw_data.items():
        if sheet_name != "text" and isinstance(data, list) and data:
            summary["data_preview"][sheet_name] = data[:3]  # Prime 3 righe per ogni sheet

    return summary

def extract_key_financial_metrics(financial_data: FinancialData) -> Dict[str, float]:
    """
    Estrae metriche finanziarie chiave dai dati.

    Args:
        financial_data: Oggetto FinancialData con i dati

    Returns:
        Dict con le metriche chiave
    """
    metrics = {}

    # TODO: Implementare l'estrazione automatica di metriche finanziarie chiave
    # Questo è un placeholder per la logica di estrazione

    return metrics

if __name__ == "__main__":
    # Esempio di utilizzo
    test_file = "test_financial_data.xlsx"
    if os.path.exists(test_file):
        try:
            financial_data = import_financial_data(test_file)
            print("Dati finanziari importati con successo:")
            print(financial_data)
        except FinancialImportError as e:
            print(f"Errore nell'importazione dei dati finanziari: {e}")
    else:
        print(f"File di test '{test_file}' non trovato. Eseguire lo script dalla directory corretta.")
