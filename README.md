# Business Plan Builder - App Streamlit per Generazione di Business Plan

Questo sistema è progettato per generare business plan completi o per sezioni, con un'interfaccia utente intuitiva basata su Streamlit. Permette di creare documenti professionali, effettuare ricerche di mercato e gestire le informazioni finanziarie.

## Caratteristiche Principali

- **Interfaccia Utente Streamlit**: Facile da usare e accessibile da browser
- **Generazione per Sezioni**: Possibilità di generare singole sezioni del business plan
- **Ricerca Avanzata**: Integrazione con Perplexity API per ricerche di mercato approfondite
- **Analisi Finanziaria**: Strumenti per la creazione di proiezioni finanziarie
- **Sistema Modulare**: Permette modifiche e interventi umani su sezioni specifiche

## Requisiti

- Python 3.8 o superiore
- Chiavi API (OpenAI, Perplexity)

## Installazione

```bash
# Crea e attiva un ambiente virtuale
python -m venv venv
source venv/bin/activate  # Per Windows: venv\Scripts\activate

# Installa le dipendenze
pip install langgraph langchain langchain_openai python-docx matplotlib pandas \
  chromadb pypdf perplexity-python tabulate openai tiktoken python-dotenv requests
```

## Configurazione

Crea un file `.env` nella directory principale con le seguenti chiavi API:

```
OPENAI_API_KEY=your_openai_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
```

## Utilizzo

### Avvio dell'Applicazione Streamlit

```bash
streamlit run app_streamlit.py
```

### Utilizzo dell'Interfaccia Web

1. Accedi all'applicazione tramite browser (di default su http://localhost:8501)
2. Compila le informazioni di base dell'azienda nella barra laterale
3. Seleziona una sezione del business plan dalla barra laterale
4. Utilizza la scheda "Editor" per generare il contenuto della sezione
5. Utilizza la scheda "Ricerca" per trovare informazioni aggiornate
6. Utilizza la scheda "Finanza" per gestire le proiezioni finanziarie
7. Esporta il business plan completo quando hai finito

### Deployment su Streamlit Cloud

L'applicazione può essere facilmente deployata su Streamlit Cloud:

1. Crea un account su [Streamlit Cloud](https://streamlit.io/cloud)
2. Collega il tuo repository GitHub
3. Configura le variabili d'ambiente (OPENAI_API_KEY, PERPLEXITY_API_KEY)
4. Deploy dell'applicazione

## Architettura del Sistema

Il sistema è basato su quattro componenti chiave:

1. **Architettura Gerarchica di Documenti**: Divisione del business plan in sezioni e sottosezioni utilizzando strategie di chunking gerarchico

2. **Sistema di Memory Persistente**: Utilizzo di LangGraph con database vettoriale per mantenere lo stato e il contesto su grandi documenti

3. **Ricerca Avanzata e RAG**: Integrazione di Perplexity API e altre fonti per ricerche di mercato approfondite

4. **Sistema di Revisione Modulare**: Permette modifiche e interventi umani su sezioni specifiche del documento

## Struttura del Progetto

```
business_plan_builder/
├── app_streamlit.py           # Applicazione Streamlit principale
├── config.py                  # Configurazioni
├── direct_generator.py        # Generatore diretto di sezioni
├── financial_integration.py   # Integrazione con strumenti finanziari
├── financial_tab.py           # Tab finanziaria per Streamlit
├── node_functions.py          # Funzioni per generare le sezioni
├── search/                    # Sistemi di ricerca
│   ├── combined_search.py     # Ricerca combinata
│   ├── perplexity_search.py   # Integrazione con Perplexity
│   └── search_utils.py        # Utilità per la ricerca
├── utils/                     # Strumenti utili
│   ├── text_processing.py     # Elaborazione del testo
│   └── docx_generator.py      # Generazione DOCX
└── requirements.txt           # Dipendenze del progetto
```

## Come Funziona il Chunking Gerarchico

Il sistema utilizza un approccio di chunking gerarchico per suddividere documenti lunghi in blocchi gestibili:

1. **Rilevamento della Struttura**: Analisi del documento per identificare sezioni e sottosezioni
2. **Suddivisione Intelligente**: Creazione di chunk di dimensione ottimale rispettando la struttura del documento
3. **Mantenimento del Contesto**: Ogni chunk mantiene metadati sulla sua posizione nella gerarchia
4. **Embedding Semantici**: Generazione di embedding per permettere ricerche semantiche

Questo approccio permette di gestire documenti molto lunghi mantenendo il contesto e la coerenza tra le diverse parti.

## Licenza

Tutti i diritti riservati. © 2024