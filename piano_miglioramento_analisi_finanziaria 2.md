# Piano Ultra-Focalizzato: Potenziamento Analisi Finanziaria (B4)

**Obiettivo Principale:**

*   **Analisi Finanziaria (B4):** Rendere la sezione finanziaria più interattiva, permettendo input utente flessibili, generando visualizzazioni dinamiche e introducendo basilari capacità di "what-if" analysis, integrando il tutto nel flusso di generazione del business plan.

**Diagramma del Piano Ultra-Focalizzato:**

```mermaid
graph TD
    Start[Inizio] --> B4_1[Input Dati Finanziari Flessibile];
    B4_1 --> B4_2[Generazione Grafici Finanziari Interattivi];
    B4_2 --> B4_3[Introduzione Analisi "What-if" Semplice];
    B4_3 --> B4_4[Integrazione con Flusso Principale e Stato];
    B4_4 --> End[Fine Lavori Potenziamento Analisi Finanziaria];
```

**Dettaglio delle Attività per il Potenziamento dell'Analisi Finanziaria (B4):**

---

*   **B4.1. Input Dati Finanziari Flessibile:**
    *   **Descrizione:** Consentire un input più diretto e strutturato per i dati finanziari, superando l'attuale approccio basato su prompt o dati pre-esistenti (come si evince da `financial_tab.py`, `financial_integration.py`, e la sezione `financial_plan` in `graph_builder.py`).
    *   **Attività:**
        *   **Interfaccia Utente (in `financial_tab.py` o una nuova tab dedicata):**
            *   Creare form Streamlit per l'inserimento manuale dei dati finanziari chiave (es. ricavi previsti per anno, costi operativi, investimenti iniziali, fonti di finanziamento).
            *   Implementare una funzionalità di upload per file CSV/Excel contenenti proiezioni finanziarie o bilanci storici semplificati. Utilizzare Pandas per il parsing.
            *   Fornire un template CSV/Excel di esempio scaricabile per guidare l'utente.
        *   **Gestione Stato:** Salvare i dati finanziari inseriti/importati nello stato dell'applicazione (`state.py`).
    *   **File Coinvolti:** `financial_tab.py`, `financial_integration.py`, `state.py`, `app_streamlit.py` (per l'integrazione della tab/UI).

*   **B4.2. Generazione Grafici Finanziari Interattivi:**
    *   **Descrizione:** Visualizzare i dati e le proiezioni finanziarie in modo più comprensibile e interattivo.
    *   **Attività:**
        *   Scegliere una libreria di plotting (es. Plotly Express, Altair, Matplotlib con Streamlit) adatta a grafici interattivi.
        *   Implementare funzioni in `financial_integration.py` o un nuovo modulo `financial_visualizer.py` per generare:
            *   Grafico a barre/linee delle proiezioni di ricavi, costi e profitti.
            *   Grafico a torta per la composizione dei costi o delle fonti di finanziamento.
            *   Grafico del punto di pareggio (Break-Even Point).
        *   Integrare questi grafici nell'interfaccia utente della sezione finanziaria, aggiornandoli dinamicamente in base ai dati inseriti.
    *   **File Coinvolti:** `financial_tab.py`, `financial_integration.py` (o `financial_visualizer.py`).

*   **B4.3. Introduzione Analisi "What-if" Semplice:**
    *   **Descrizione:** Permettere all'utente di esplorare scenari finanziari alternativi.
    *   **Attività:**
        *   Nell'interfaccia della sezione finanziaria, aggiungere input (slider o campi numerici) per modificare alcuni parametri chiave (es. "% variazione vendite", "% variazione costi variabili").
        *   Ricalcolare e aggiornare dinamicamente le proiezioni e i grafici in base a questi scenari.
        *   Mostrare i risultati dello scenario "base" e dello scenario "what-if" per un confronto.
    *   **File Coinvolti:** `financial_tab.py`, `financial_integration.py`.

*   **B4.4. Integrazione con Flusso Principale e Stato:**
    *   **Descrizione:** Assicurare che i risultati dell'analisi finanziaria (testo riassuntivo, tabelle chiave, riferimenti ai grafici) siano correttamente passati alla funzione `financial_plan` in `graph_builder.py` per l'inclusione nel business plan generato dall'LLM.
    *   **Attività:**
        *   Modificare `financial_plan` in `graph_builder.py` per recuperare i dati finanziari elaborati dallo stato.
        *   Adattare il prompt per l'LLM in modo che possa utilizzare queste informazioni strutturate (tabelle, indicatori chiave) per generare una narrazione finanziaria coerente, invece di dover inventare i numeri.
        *   Assicurarsi che l'output dell'analisi finanziaria interattiva sia salvato e recuperato correttamente in `state.py`.
    *   **File Coinvolti:** `graph_builder.py`, `state.py`, `financial_tab.py`.