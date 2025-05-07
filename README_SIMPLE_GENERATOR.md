# Generatore di Business Plan Semplificato

Questa è una versione semplificata dell'applicazione Business Plan Builder, progettata per risolvere i problemi di generazione delle sezioni. Questa versione si concentra esclusivamente sulla generazione delle sezioni del business plan, eliminando tutte le complessità non necessarie.

## Caratteristiche

- Interfaccia utente semplice e intuitiva
- Generazione diretta delle sezioni del business plan
- Utilizzo diretto dell'API Gemini senza dipendenze complesse
- Possibilità di esportare il business plan completo

## Requisiti

- Python 3.7 o superiore
- Streamlit
- Google Generative AI (Gemini)
- Una chiave API Gemini valida

## Installazione

1. Assicurati di avere Python installato
2. Installa le dipendenze necessarie:

```bash
pip install streamlit google-generativeai python-dotenv
```

3. Configura la tua chiave API Gemini in uno dei seguenti modi:
   - Crea un file `.env` nella stessa directory dell'applicazione con il contenuto:
     ```
     GEMINI_API_KEY=la_tua_chiave_api
     ```
   - Imposta la variabile d'ambiente `GEMINI_API_KEY` nel tuo sistema
   - Configura i segreti di Streamlit (per deployment)

## Utilizzo

1. Avvia l'applicazione:

```bash
streamlit run simple_generator_app.py
```

2. Inserisci le informazioni sulla tua azienda nella barra laterale
3. Seleziona la sezione che desideri generare
4. Clicca sul pulsante "Genera Sezione"
5. Visualizza e copia il contenuto generato
6. Ripeti per tutte le sezioni desiderate
7. Esporta il business plan completo quando hai finito

## Risoluzione dei problemi

Se riscontri problemi con la generazione delle sezioni:

1. Verifica che la tua chiave API Gemini sia valida utilizzando il pulsante "Verifica Connessione API" nella sezione "Debug e Diagnostica"
2. Controlla che le variabili d'ambiente siano configurate correttamente
3. Assicurati di avere una connessione internet stabile

## Differenze rispetto all'applicazione completa

Questa versione semplificata:

- Non utilizza il grafo LangGraph
- Non dipende da database vettoriali
- Non include la ricerca online
- Non include la modifica del contenuto
- Non include la struttura personalizzata del business plan

È progettata esclusivamente per generare le sezioni del business plan in modo affidabile e semplice.

## Nota importante

Questa applicazione è una soluzione temporanea per risolvere i problemi di generazione delle sezioni nell'applicazione completa. Una volta risolti i problemi nell'applicazione principale, è consigliabile tornare a utilizzare quella per sfruttare tutte le funzionalità disponibili.
