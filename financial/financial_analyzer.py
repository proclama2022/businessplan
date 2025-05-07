#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Analizzatore di dati finanziari per il business plan builder.

Questo modulo fornisce funzioni per analizzare dati finanziari e generare
insights e proiezioni per il business plan.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

class FinancialAnalysisError(Exception):
    """Eccezione sollevata quando si verifica un errore nell'analisi dei dati finanziari"""
    pass

def analyze_financial_data(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analizza i dati finanziari e genera insights.
    
    Args:
        financial_data: Dati finanziari importati
        
    Returns:
        Dict[str, Any]: Dati finanziari analizzati con insights
        
    Raises:
        FinancialAnalysisError: Se si verifica un errore nell'analisi
    """
    try:
        # Copia i dati originali
        analysis_result = financial_data.copy()
        
        # Aggiungi insights
        analysis_result["insights"] = generate_financial_insights(financial_data)
        
        # Aggiungi proiezioni
        analysis_result["projections"] = generate_financial_projections(financial_data)
        
        # Aggiungi raccomandazioni
        analysis_result["recommendations"] = generate_financial_recommendations(financial_data)
        
        return analysis_result
    except Exception as e:
        raise FinancialAnalysisError(f"Errore nell'analisi dei dati finanziari: {str(e)}")

def generate_financial_insights(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera insights dai dati finanziari.
    
    Args:
        financial_data: Dati finanziari importati
        
    Returns:
        Dict[str, Any]: Insights finanziari
    """
    insights = {
        "profitability": analyze_profitability(financial_data),
        "liquidity": analyze_liquidity(financial_data),
        "solvency": analyze_solvency(financial_data),
        "efficiency": analyze_efficiency(financial_data),
        "growth": analyze_growth(financial_data),
        "summary": []
    }
    
    # Genera un sommario degli insights principali
    summary = []
    
    # Profitability insights
    if insights["profitability"]["net_profit_margin_assessment"] == "positive":
        summary.append("Il margine di profitto netto è positivo, indicando una buona redditività.")
    elif insights["profitability"]["net_profit_margin_assessment"] == "negative":
        summary.append("Il margine di profitto netto è negativo, indicando problemi di redditività.")
    
    if insights["profitability"]["return_on_equity_assessment"] == "positive":
        summary.append("Il ritorno sul capitale proprio (ROE) è buono, indicando un efficace utilizzo del capitale.")
    elif insights["profitability"]["return_on_equity_assessment"] == "negative":
        summary.append("Il ritorno sul capitale proprio (ROE) è basso, indicando un inefficace utilizzo del capitale.")
    
    # Liquidity insights
    if insights["liquidity"]["current_ratio_assessment"] == "positive":
        summary.append("L'indice di liquidità corrente è buono, indicando una solida capacità di far fronte agli impegni a breve termine.")
    elif insights["liquidity"]["current_ratio_assessment"] == "negative":
        summary.append("L'indice di liquidità corrente è basso, indicando potenziali difficoltà nel far fronte agli impegni a breve termine.")
    
    # Solvency insights
    if insights["solvency"]["debt_to_equity_assessment"] == "positive":
        summary.append("Il rapporto debito/capitale è equilibrato, indicando un buon livello di solvibilità.")
    elif insights["solvency"]["debt_to_equity_assessment"] == "negative":
        summary.append("Il rapporto debito/capitale è elevato, indicando un potenziale rischio di solvibilità.")
    
    # Efficiency insights
    if insights["efficiency"]["asset_turnover_assessment"] == "positive":
        summary.append("L'indice di rotazione degli asset è buono, indicando un efficiente utilizzo degli asset.")
    elif insights["efficiency"]["asset_turnover_assessment"] == "negative":
        summary.append("L'indice di rotazione degli asset è basso, indicando un inefficiente utilizzo degli asset.")
    
    # Growth insights
    if "revenue_growth" in insights["growth"] and insights["growth"]["revenue_growth_assessment"] == "positive":
        summary.append("La crescita dei ricavi è positiva, indicando un trend di crescita dell'azienda.")
    elif "revenue_growth" in insights["growth"] and insights["growth"]["revenue_growth_assessment"] == "negative":
        summary.append("La crescita dei ricavi è negativa, indicando un trend di contrazione dell'azienda.")
    
    insights["summary"] = summary
    
    return insights

def analyze_profitability(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analizza la redditività dai dati finanziari.
    
    Args:
        financial_data: Dati finanziari importati
        
    Returns:
        Dict[str, Any]: Analisi della redditività
    """
    metrics = financial_data.get("key_metrics", {}).get("profitability", {})
    
    # Valuta il margine di profitto netto
    net_profit_margin = metrics.get("net_profit_margin", 0)
    if net_profit_margin > 0.1:
        net_profit_margin_assessment = "positive"
    elif net_profit_margin > 0:
        net_profit_margin_assessment = "neutral"
    else:
        net_profit_margin_assessment = "negative"
    
    # Valuta il ROA
    return_on_assets = metrics.get("return_on_assets", 0)
    if return_on_assets > 0.05:
        return_on_assets_assessment = "positive"
    elif return_on_assets > 0:
        return_on_assets_assessment = "neutral"
    else:
        return_on_assets_assessment = "negative"
    
    # Valuta il ROE
    return_on_equity = metrics.get("return_on_equity", 0)
    if return_on_equity > 0.1:
        return_on_equity_assessment = "positive"
    elif return_on_equity > 0:
        return_on_equity_assessment = "neutral"
    else:
        return_on_equity_assessment = "negative"
    
    return {
        "net_profit_margin": net_profit_margin,
        "net_profit_margin_assessment": net_profit_margin_assessment,
        "return_on_assets": return_on_assets,
        "return_on_assets_assessment": return_on_assets_assessment,
        "return_on_equity": return_on_equity,
        "return_on_equity_assessment": return_on_equity_assessment
    }

def analyze_liquidity(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analizza la liquidità dai dati finanziari.
    
    Args:
        financial_data: Dati finanziari importati
        
    Returns:
        Dict[str, Any]: Analisi della liquidità
    """
    metrics = financial_data.get("key_metrics", {}).get("liquidity", {})
    
    # Valuta il current ratio
    current_ratio = metrics.get("current_ratio", 0)
    if current_ratio > 2:
        current_ratio_assessment = "positive"
    elif current_ratio > 1:
        current_ratio_assessment = "neutral"
    else:
        current_ratio_assessment = "negative"
    
    # Valuta il quick ratio
    quick_ratio = metrics.get("quick_ratio", 0)
    if quick_ratio > 1:
        quick_ratio_assessment = "positive"
    elif quick_ratio > 0.5:
        quick_ratio_assessment = "neutral"
    else:
        quick_ratio_assessment = "negative"
    
    return {
        "current_ratio": current_ratio,
        "current_ratio_assessment": current_ratio_assessment,
        "quick_ratio": quick_ratio,
        "quick_ratio_assessment": quick_ratio_assessment
    }

def analyze_solvency(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analizza la solvibilità dai dati finanziari.
    
    Args:
        financial_data: Dati finanziari importati
        
    Returns:
        Dict[str, Any]: Analisi della solvibilità
    """
    metrics = financial_data.get("key_metrics", {}).get("solvency", {})
    
    # Valuta il debt to equity
    debt_to_equity = metrics.get("debt_to_equity", 0)
    if debt_to_equity < 1:
        debt_to_equity_assessment = "positive"
    elif debt_to_equity < 2:
        debt_to_equity_assessment = "neutral"
    else:
        debt_to_equity_assessment = "negative"
    
    # Valuta il debt to assets
    debt_to_assets = metrics.get("debt_to_assets", 0)
    if debt_to_assets < 0.4:
        debt_to_assets_assessment = "positive"
    elif debt_to_assets < 0.6:
        debt_to_assets_assessment = "neutral"
    else:
        debt_to_assets_assessment = "negative"
    
    # Valuta l'interest coverage
    interest_coverage = metrics.get("interest_coverage", 0)
    if interest_coverage > 3:
        interest_coverage_assessment = "positive"
    elif interest_coverage > 1.5:
        interest_coverage_assessment = "neutral"
    else:
        interest_coverage_assessment = "negative"
    
    return {
        "debt_to_equity": debt_to_equity,
        "debt_to_equity_assessment": debt_to_equity_assessment,
        "debt_to_assets": debt_to_assets,
        "debt_to_assets_assessment": debt_to_assets_assessment,
        "interest_coverage": interest_coverage,
        "interest_coverage_assessment": interest_coverage_assessment
    }

def analyze_efficiency(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analizza l'efficienza dai dati finanziari.
    
    Args:
        financial_data: Dati finanziari importati
        
    Returns:
        Dict[str, Any]: Analisi dell'efficienza
    """
    metrics = financial_data.get("key_metrics", {}).get("efficiency", {})
    
    # Valuta l'asset turnover
    asset_turnover = metrics.get("asset_turnover", 0)
    if asset_turnover > 1:
        asset_turnover_assessment = "positive"
    elif asset_turnover > 0.5:
        asset_turnover_assessment = "neutral"
    else:
        asset_turnover_assessment = "negative"
    
    # Valuta l'inventory turnover
    inventory_turnover = metrics.get("inventory_turnover", 0)
    if inventory_turnover > 6:
        inventory_turnover_assessment = "positive"
    elif inventory_turnover > 3:
        inventory_turnover_assessment = "neutral"
    else:
        inventory_turnover_assessment = "negative"
    
    return {
        "asset_turnover": asset_turnover,
        "asset_turnover_assessment": asset_turnover_assessment,
        "inventory_turnover": inventory_turnover,
        "inventory_turnover_assessment": inventory_turnover_assessment
    }

def analyze_growth(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analizza la crescita dai dati finanziari.
    
    Args:
        financial_data: Dati finanziari importati
        
    Returns:
        Dict[str, Any]: Analisi della crescita
    """
    # Verifica se ci sono dati dell'anno precedente
    income_statement = financial_data.get("income_statement", {})
    revenues = income_statement.get("revenues", {})
    
    # Trova i ricavi attuali
    current_revenue = 0
    for code, account in revenues.items():
        if code == "A.1":  # Ricavi delle vendite e delle prestazioni
            current_revenue = account.get("value", 0)
            previous_revenue = account.get("previous_value")
            break
    
    result = {}
    
    # Calcola la crescita dei ricavi se disponibile
    if previous_revenue is not None and previous_revenue != 0:
        revenue_growth = (current_revenue - previous_revenue) / abs(previous_revenue)
        if revenue_growth > 0.1:
            revenue_growth_assessment = "positive"
        elif revenue_growth > 0:
            revenue_growth_assessment = "neutral"
        else:
            revenue_growth_assessment = "negative"
        
        result["revenue_growth"] = revenue_growth
        result["revenue_growth_assessment"] = revenue_growth_assessment
    
    return result

def generate_financial_projections(financial_data: Dict[str, Any], years: int = 3) -> Dict[str, Any]:
    """
    Genera proiezioni finanziarie dai dati finanziari.
    
    Args:
        financial_data: Dati finanziari importati
        years: Numero di anni per le proiezioni
        
    Returns:
        Dict[str, Any]: Proiezioni finanziarie
    """
    # Estrai i dati necessari
    income_statement = financial_data.get("income_statement", {})
    balance_sheet = financial_data.get("balance_sheet", {})
    
    # Trova i ricavi attuali
    current_revenue = 0
    for code, account in income_statement.get("revenues", {}).items():
        if code == "A.1":  # Ricavi delle vendite e delle prestazioni
            current_revenue = account.get("value", 0)
            previous_revenue = account.get("previous_value")
            break
    
    # Trova l'utile netto attuale
    current_net_profit = income_statement.get("net_result", 0)
    
    # Calcola il tasso di crescita dei ricavi
    revenue_growth_rate = 0.05  # Default: 5% di crescita annua
    if previous_revenue is not None and previous_revenue != 0:
        historical_growth = (current_revenue - previous_revenue) / abs(previous_revenue)
        # Usa una media ponderata tra la crescita storica e il default
        revenue_growth_rate = 0.7 * historical_growth + 0.3 * revenue_growth_rate
    
    # Limita il tasso di crescita a valori realistici
    revenue_growth_rate = max(-0.2, min(0.3, revenue_growth_rate))
    
    # Calcola il margine di profitto attuale
    profit_margin = current_net_profit / current_revenue if current_revenue else 0
    
    # Proiezioni
    projections = {
        "revenue": {},
        "expenses": {},
        "net_profit": {},
        "assets": {},
        "liabilities": {},
        "equity": {},
        "cash_flow": {},
        "assumptions": {
            "revenue_growth_rate": revenue_growth_rate,
            "profit_margin": profit_margin
        }
    }
    
    # Anno corrente
    current_year = financial_data.get("year", datetime.now().year)
    
    # Genera proiezioni per ogni anno
    for year_offset in range(1, years + 1):
        year = current_year + year_offset
        
        # Proiezione dei ricavi
        projected_revenue = current_revenue * (1 + revenue_growth_rate) ** year_offset
        
        # Proiezione dell'utile netto (assumendo un margine di profitto stabile)
        projected_net_profit = projected_revenue * profit_margin
        
        # Proiezione delle spese
        projected_expenses = projected_revenue - projected_net_profit
        
        # Proiezione degli asset (crescita proporzionale ai ricavi)
        projected_assets = balance_sheet.get("total_assets", 0) * (1 + revenue_growth_rate * 0.8) ** year_offset
        
        # Proiezione del patrimonio netto
        current_equity = 0
        for code, account in balance_sheet.get("equity", {}).items():
            if code == "A.P":  # Patrimonio netto
                current_equity = account.get("value", 0)
                break
        
        projected_equity = current_equity + projected_net_profit * 0.7  # Assumendo che il 70% dell'utile venga reinvestito
        
        # Proiezione delle passività
        projected_liabilities = projected_assets - projected_equity
        
        # Proiezione del flusso di cassa (semplificata)
        projected_cash_flow = projected_net_profit * 1.2  # Assumendo che il flusso di cassa sia il 120% dell'utile netto
        
        # Aggiungi le proiezioni
        projections["revenue"][str(year)] = projected_revenue
        projections["expenses"][str(year)] = projected_expenses
        projections["net_profit"][str(year)] = projected_net_profit
        projections["assets"][str(year)] = projected_assets
        projections["liabilities"][str(year)] = projected_liabilities
        projections["equity"][str(year)] = projected_equity
        projections["cash_flow"][str(year)] = projected_cash_flow
    
    return projections

def generate_financial_recommendations(financial_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Genera raccomandazioni dai dati finanziari.
    
    Args:
        financial_data: Dati finanziari importati
        
    Returns:
        List[Dict[str, str]]: Lista di raccomandazioni
    """
    recommendations = []
    
    # Estrai gli insights
    insights = financial_data.get("insights", {})
    profitability = insights.get("profitability", {})
    liquidity = insights.get("liquidity", {})
    solvency = insights.get("solvency", {})
    efficiency = insights.get("efficiency", {})
    growth = insights.get("growth", {})
    
    # Raccomandazioni sulla redditività
    if profitability.get("net_profit_margin_assessment") == "negative":
        recommendations.append({
            "area": "Redditività",
            "issue": "Margine di profitto netto negativo",
            "recommendation": "Analizzare la struttura dei costi e identificare opportunità di riduzione. Considerare un aumento dei prezzi se il mercato lo permette."
        })
    elif profitability.get("net_profit_margin_assessment") == "neutral":
        recommendations.append({
            "area": "Redditività",
            "issue": "Margine di profitto netto basso",
            "recommendation": "Migliorare l'efficienza operativa e considerare strategie per aumentare i ricavi senza aumentare proporzionalmente i costi."
        })
    
    if profitability.get("return_on_equity_assessment") == "negative":
        recommendations.append({
            "area": "Redditività",
            "issue": "Basso ritorno sul capitale proprio (ROE)",
            "recommendation": "Rivedere l'allocazione del capitale e considerare la dismissione di asset non produttivi. Valutare opportunità di investimento con rendimenti più elevati."
        })
    
    # Raccomandazioni sulla liquidità
    if liquidity.get("current_ratio_assessment") == "negative":
        recommendations.append({
            "area": "Liquidità",
            "issue": "Basso indice di liquidità corrente",
            "recommendation": "Migliorare la gestione del capitale circolante. Considerare la rinegoziazione dei termini di pagamento con fornitori e clienti. Valutare l'accesso a linee di credito a breve termine."
        })
    
    if liquidity.get("quick_ratio_assessment") == "negative":
        recommendations.append({
            "area": "Liquidità",
            "issue": "Basso indice di liquidità immediata",
            "recommendation": "Ridurre le scorte di magazzino e migliorare la gestione dei crediti commerciali. Considerare politiche di incasso più aggressive."
        })
    
    # Raccomandazioni sulla solvibilità
    if solvency.get("debt_to_equity_assessment") == "negative":
        recommendations.append({
            "area": "Solvibilità",
            "issue": "Alto rapporto debito/capitale",
            "recommendation": "Ridurre il livello di indebitamento. Considerare l'aumento del capitale proprio attraverso nuovi investimenti o la ritenzione degli utili."
        })
    
    if solvency.get("interest_coverage_assessment") == "negative":
        recommendations.append({
            "area": "Solvibilità",
            "issue": "Basso indice di copertura degli interessi",
            "recommendation": "Rinegoziare i termini del debito per ridurre gli oneri finanziari. Migliorare la redditività operativa per aumentare la capacità di servire il debito."
        })
    
    # Raccomandazioni sull'efficienza
    if efficiency.get("asset_turnover_assessment") == "negative":
        recommendations.append({
            "area": "Efficienza",
            "issue": "Basso indice di rotazione degli asset",
            "recommendation": "Ottimizzare l'utilizzo degli asset esistenti. Considerare la dismissione di asset sottoutilizzati. Aumentare i ricavi senza aumentare proporzionalmente gli asset."
        })
    
    if efficiency.get("inventory_turnover_assessment") == "negative":
        recommendations.append({
            "area": "Efficienza",
            "issue": "Basso indice di rotazione delle scorte",
            "recommendation": "Migliorare la gestione del magazzino. Implementare sistemi just-in-time. Rivedere le politiche di approvvigionamento e le previsioni di vendita."
        })
    
    # Raccomandazioni sulla crescita
    if "revenue_growth_assessment" in growth and growth.get("revenue_growth_assessment") == "negative":
        recommendations.append({
            "area": "Crescita",
            "issue": "Crescita negativa dei ricavi",
            "recommendation": "Sviluppare nuove strategie di marketing e vendita. Considerare l'espansione in nuovi mercati o segmenti. Innovare l'offerta di prodotti/servizi."
        })
    
    # Se non ci sono raccomandazioni specifiche, aggiungi una raccomandazione generale
    if not recommendations:
        recommendations.append({
            "area": "Generale",
            "issue": "Mantenimento della performance finanziaria",
            "recommendation": "Continuare a monitorare gli indicatori finanziari chiave. Considerare opportunità di crescita e miglioramento dell'efficienza operativa."
        })
    
    return recommendations

def generate_financial_plan_section(financial_data: Dict[str, Any], company_name: str) -> str:
    """
    Genera la sezione del piano finanziario per il business plan.
    
    Args:
        financial_data: Dati finanziari analizzati
        company_name: Nome dell'azienda
        
    Returns:
        str: Testo della sezione del piano finanziario
    """
    # Estrai i dati necessari
    insights = financial_data.get("insights", {})
    projections = financial_data.get("projections", {})
    recommendations = financial_data.get("recommendations", [])
    
    # Costruisci il testo
    text = f"# Piano Finanziario - {company_name}\n\n"
    
    # Panoramica finanziaria
    text += "## Panoramica Finanziaria\n\n"
    
    # Aggiungi il sommario degli insights
    if insights.get("summary"):
        text += "### Analisi della Situazione Attuale\n\n"
        for insight in insights["summary"]:
            text += f"- {insight}\n"
        text += "\n"
    
    # Proiezioni finanziarie
    text += "## Proiezioni Finanziarie\n\n"
    
    if projections:
        text += "### Ricavi Previsti\n\n"
        text += "| Anno | Ricavi Previsti |\n"
        text += "|------|----------------|\n"
        for year, revenue in projections.get("revenue", {}).items():
            text += f"| {year} | {revenue:,.2f} € |\n"
        text += "\n"
        
        text += "### Utile Netto Previsto\n\n"
        text += "| Anno | Utile Netto Previsto |\n"
        text += "|------|----------------------|\n"
        for year, profit in projections.get("net_profit", {}).items():
            text += f"| {year} | {profit:,.2f} € |\n"
        text += "\n"
    
    # Raccomandazioni
    if recommendations:
        text += "## Raccomandazioni Finanziarie\n\n"
        for rec in recommendations:
            text += f"### {rec['area']}: {rec['issue']}\n\n"
            text += f"{rec['recommendation']}\n\n"
    
    # Conclusioni
    text += "## Conclusioni\n\n"
    text += f"Il piano finanziario di {company_name} è stato sviluppato sulla base dell'analisi dei dati finanziari storici e delle proiezioni future. "
    
    if projections:
        years = list(projections.get("revenue", {}).keys())
        if years:
            last_year = years[-1]
            text += f"Le proiezioni indicano che entro il {last_year}, l'azienda potrebbe raggiungere ricavi di circa {projections['revenue'][last_year]:,.2f} € "
            text += f"con un utile netto di circa {projections['net_profit'][last_year]:,.2f} €. "
    
    text += "L'implementazione delle raccomandazioni finanziarie proposte contribuirà a migliorare la performance finanziaria e a garantire la sostenibilità a lungo termine dell'azienda."
    
    return text
