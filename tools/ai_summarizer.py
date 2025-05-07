import os
from openai import OpenAI

def generate_market_section(aggregated_data: dict, language: str = "it") -> str:
    """
    Usa OpenAI per generare una sezione di report di mercato a partire dai dati aggregati.
    Args:
        aggregated_data: dict con chiavi come 'market_size', 'trends', 'opportunities', 'threats', 'sources', ecc.
        language: lingua della sintesi (default: italiano)
    Returns:
        Testo generato dal modello LLM.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = build_prompt(aggregated_data, language)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Sei un esperto di business plan e analisi di mercato. Scrivi in modo chiaro, sintetico e professionale in {language}."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        error_msg = f"Errore nella generazione della sintesi AI: {str(e)}"
        if "rate limit" in str(e).lower():
            error_msg += "\n\nERRORE: Hai superato la quota di richieste all'API OpenAI. Attendi qualche minuto e riprova."
        elif "authentication" in str(e).lower():
            error_msg += "\n\nERRORE: Chiave API OpenAI non valida o mancante. Verifica la chiave in .env"
        return error_msg

def build_prompt(aggregated_data: dict, language: str) -> str:
    # Costruisce un prompt dettagliato per la sintesi AI
    prompt = (
        f"Genera una sezione di analisi di mercato per un business plan nel settore Software e Consulenza IT B2B in Italia.\n"
        f"Includi:\n"
        f"- Dimensioni e crescita del mercato\n"
        f"- Trend principali\n"
        f"- Opportunità\n"
        f"- Rischi\n"
        f"- Segmentazione\n"
        f"- Fonti principali (con titolo e url)\n"
        f"\n"
        f"Dati raccolti:\n"
    )
    if "market_size" in aggregated_data and aggregated_data["market_size"]:
        prompt += f"\n**Dimensioni mercato:** {aggregated_data['market_size']}\n"
    if "trends" in aggregated_data and aggregated_data["trends"]:
        prompt += f"\n**Trend:**\n"
        for t in aggregated_data["trends"]:
            prompt += f"- {t.get('name', '')}: {t.get('description', '')}\n"
    if "opportunities" in aggregated_data and aggregated_data["opportunities"]:
        prompt += f"\n**Opportunità:**\n"
        for o in aggregated_data["opportunities"]:
            prompt += f"- {o.get('name', '')}: {o.get('description', '')}\n"
    if "threats" in aggregated_data and aggregated_data["threats"]:
        prompt += f"\n**Rischi:**\n"
        for r in aggregated_data["threats"]:
            prompt += f"- {r.get('name', '')}: {r.get('description', '')}\n"
    if "customer_segments" in aggregated_data and aggregated_data["customer_segments"]:
        prompt += f"\n**Segmenti di clientela:** {aggregated_data['customer_segments']}\n"
    if "sources" in aggregated_data and aggregated_data["sources"]:
        prompt += f"\n**Fonti principali:**\n"
        for s in aggregated_data["sources"][:10]:
            prompt += f"- {s.get('title', '')} ({s.get('url', '')})\n"
    if "api_status" in aggregated_data:
        prompt += f"\n[Stato API: {aggregated_data['api_status']}]\n"
    prompt += "\nScrivi la sezione in modo leggibile, con riferimenti alle fonti dove opportuno."
    return prompt
