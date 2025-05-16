#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo per la navigazione semplificata nell'applicazione Business Plan Builder.

Questo modulo fornisce componenti UI semplificati per la navigazione
tra le diverse sezioni del business plan.
"""

import streamlit as st
from typing import List, Dict, Any, Tuple, Optional

def simplified_navigation_bar(
    sections: List[Tuple[str, str]],
    current_section: str,
    on_section_change=None
) -> None:
    """
    Crea una barra di navigazione semplificata per le sezioni del business plan.
    
    Args:
        sections: Lista di tuple (section_key, section_name)
        current_section: Chiave della sezione corrente
        on_section_change: Callback da chiamare quando l'utente cambia sezione
    """
    # Trova l'indice della sezione corrente
    current_index = -1
    for i, (section_key, _) in enumerate(sections):
        if section_key == current_section:
            current_index = i
            break
    
    # Crea una barra di progresso semplificata
    progress_percentage = 0
    if current_index >= 0 and len(sections) > 1:
        progress_percentage = current_index / (len(sections) - 1)
    
    st.progress(progress_percentage)
    
    # Mostra il nome della sezione corrente e il progresso
    if current_index >= 0:
        st.caption(f"Passo {current_index + 1} di {len(sections)}")
    
    # Crea pulsanti per la navigazione avanti/indietro
    col1, col2 = st.columns(2)
    
    with col1:
        # Pulsante indietro
        if current_index > 0:
            prev_section = sections[current_index - 1][0]
            if st.button("◀️ Indietro", key="nav_prev", use_container_width=True):
                if on_section_change:
                    on_section_change(prev_section)
                else:
                    st.session_state.current_node = prev_section
                    st.rerun()
    
    with col2:
        # Pulsante avanti
        if current_index < len(sections) - 1:
            next_section = sections[current_index + 1][0]
            if st.button("Avanti ▶️", key="nav_next", use_container_width=True, type="primary"):
                if on_section_change:
                    on_section_change(next_section)
                else:
                    st.session_state.current_node = next_section
                    st.rerun()

def simplified_section_selector(
    sections: List[Tuple[str, str]],
    current_section: str,
    history: List[Tuple[str, Dict, str]],
    on_section_change=None
) -> None:
    """
    Crea un selettore di sezioni semplificato per la barra laterale.
    
    Args:
        sections: Lista di tuple (section_key, section_name)
        current_section: Chiave della sezione corrente
        history: Cronologia delle sezioni completate
        on_section_change: Callback da chiamare quando l'utente cambia sezione
    """
    st.sidebar.subheader("🧭 Sezioni")
    
    # Crea pulsanti per ogni sezione
    for section_key, section_name in sections:
        # Evidenzia la sezione corrente
        is_current = section_key == current_section
        button_style = "primary" if is_current else "secondary"
        
        # Verifica se questa sezione ha già contenuto
        has_content = False
        for node_name, _, output in history:
            if node_name == section_key and output:
                has_content = True
                break
        
        # Aggiungi un'icona per indicare lo stato
        icon = "✅ " if has_content else "📝 "
        if is_current:
            icon = "🔍 "
        
        if st.sidebar.button(f"{icon}{section_name}", key=f"nav_{section_key}", type=button_style, use_container_width=True):
            # Ensure the state is updated before rerunning
            st.session_state.current_node = section_key
            if on_section_change:
                on_section_change(section_key)
            else:
                st.rerun()

def simplified_wizard_steps(
    steps: List[str],
    current_step: int
) -> None:
    """
    Crea una visualizzazione semplificata dei passi del wizard.
    
    Args:
        steps: Lista dei nomi dei passi
        current_step: Indice del passo corrente (0-based)
    """
    # Crea una visualizzazione più semplice e chiara degli step
    cols = st.columns(len(steps))
    for i, (col, step_name) in enumerate(zip(cols, steps)):
        with col:
            # Determina lo stile per ogni step
            if i < current_step:
                emoji = "✅"  # Completato
                color = "#28a745"
            elif i == current_step:
                emoji = "🔍"  # Attuale
                color = "#007bff" 
            else:
                emoji = "⏳"  # Da fare
                color = "#6c757d"
                
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-size: 20px; margin-bottom: 5px;">{emoji}</div>
                <div style="font-size: 0.8rem; color: {color}; font-weight: {'bold' if i == current_step else 'normal'};">
                    {i+1}. {step_name}
                </div>
            </div>
            """, unsafe_allow_html=True)

def add_help_sidebar() -> None:
    """
    Aggiunge una sezione di aiuto semplificata nella barra laterale.
    """
    with st.sidebar.expander("❓ Guida Rapida", expanded=False):
        st.markdown("""
        ### Come usare l'applicazione:
        
        1. **Seleziona una sezione** dalla barra laterale
        2. **Genera il contenuto** con il pulsante "Genera"
        3. **Modifica il testo** se necessario
        4. **Salva le modifiche** con il pulsante "Salva"
        5. **Passa alla sezione successiva** con il pulsante "Avanti"
        6. Alla fine, **genera il documento completo**
        
        Per assistenza, contatta il supporto.
        """)

def add_context_help(section_key: str) -> None:
    """
    Aggiunge suggerimenti contestuali in base alla sezione corrente.
    
    Args:
        section_key: Chiave della sezione corrente
    """
    help_text = {
        "executive_summary": """
            **Suggerimenti per il Sommario Esecutivo:**
            - Riassumi i punti chiave del business plan
            - Includi la proposta di valore dell'azienda
            - Descrivi brevemente il mercato target
            - Menziona i principali obiettivi finanziari
        """,
        "company_description": """
            **Suggerimenti per la Descrizione dell'Azienda:**
            - Descrivi la storia e la missione dell'azienda
            - Spiega la struttura legale e organizzativa
            - Includi informazioni sui fondatori e il team
            - Descrivi la sede e le strutture
        """,
        "products_and_services": """
            **Suggerimenti per Prodotti e Servizi:**
            - Descrivi in dettaglio i prodotti o servizi offerti
            - Spiega i benefici per i clienti
            - Menziona eventuali brevetti o proprietà intellettuale
            - Descrivi il ciclo di vita del prodotto
        """,
        "market_analysis": """
            **Suggerimenti per l'Analisi di Mercato:**
            - Identifica il mercato target e la sua dimensione
            - Descrivi le tendenze del settore
            - Analizza la domanda dei clienti
            - Identifica i segmenti di mercato chiave
        """,
        "financial_plan": """
            **Suggerimenti per il Piano Finanziario:**
            - Includi proiezioni di vendita e ricavi
            - Descrivi i costi operativi e di avviamento
            - Presenta il punto di pareggio
            - Includi flussi di cassa previsti
        """,
        "document_generation": """
            **Suggerimenti per la Generazione del Documento:**
            - Rivedi tutte le sezioni prima di generare
            - Assicurati che i dati finanziari siano accurati
            - Controlla la coerenza tra le diverse sezioni
            - Personalizza il formato del documento finale
        """
    }
    
    if section_key in help_text:
        with st.expander("💡 Suggerimenti", expanded=True):
            st.markdown(help_text[section_key])

if __name__ == "__main__":
    # Test dei componenti di navigazione
    st.set_page_config(page_title="Test Navigazione Semplificata", layout="wide")
    st.title("Test Componenti di Navigazione Semplificata")
    
    # Definisci le sezioni di test
    test_sections = [
        ("executive_summary", "Sommario Esecutivo"),
        ("company_description", "Descrizione Azienda"),
        ("products_and_services", "Prodotti e Servizi"),
        ("market_analysis", "Analisi di Mercato"),
        ("financial_plan", "Piano Finanziario"),
        ("document_generation", "Genera Documento")
    ]
    
    # Inizializza lo stato della sessione per il test
    if 'test_current_section' not in st.session_state:
        st.session_state.test_current_section = "executive_summary"
    
    if 'test_history' not in st.session_state:
        st.session_state.test_history = [
            ("executive_summary", {}, "Questo è un sommario di esempio."),
            ("company_description", {}, "")
        ]
    
    # Funzione di callback per il cambio di sezione
    def on_test_section_change(section_key):
        st.session_state.test_current_section = section_key
        st.rerun()
    
    # Test del selettore di sezioni
    with st.sidebar:
        simplified_section_selector(
            test_sections,
            st.session_state.test_current_section,
            st.session_state.test_history,
            on_test_section_change
        )
        
        add_help_sidebar()
    
    # Test della barra di navigazione
    simplified_navigation_bar(
        test_sections,
        st.session_state.test_current_section,
        on_test_section_change
    )
    
    # Test dei passi del wizard
    st.subheader("Progresso")
    simplified_wizard_steps(
        [name for _, name in test_sections],
        test_sections.index((st.session_state.test_current_section, next(name for key, name in test_sections if key == st.session_state.test_current_section)))
    )
    
    # Test dell'aiuto contestuale
    st.subheader("Aiuto Contestuale")
    add_context_help(st.session_state.test_current_section)
