TAVILY_API_KEY=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 os
from search.tavily_search import TavilySearch

# Carica le variabili d'ambiente dal file .env se presente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Attenzione: python-dotenv non installato. Le variabili d'ambiente potrebbero non essere caricate dal file .env.")

if __name__ == "__main__":
    tavily = TavilySearch()
    query = "Qual è la capitale d’Italia?"
    result = tavily.search(query)
    print("Risultato Tavily API:")
    print(result)
