import json
import os
from typing import Dict, List, Optional, Any

def load_example_data() -> List[Dict[str, Any]]:
    """
    Carica i dati di esempio dal file JSON.
    
    Returns:
        List[Dict[str, Any]]: Lista di esempi con i loro dati
    """
    try:
        with open('example_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('examples', [])
    except Exception as e:
        print(f"Errore nel caricamento dei dati di esempio: {e}")
        return []

def get_example_names() -> List[Dict[str, str]]:
    """
    Ottiene la lista dei nomi degli esempi disponibili.
    
    Returns:
        List[Dict[str, str]]: Lista di dizionari con id e nome degli esempi
    """
    examples = load_example_data()
    return [{"id": example["id"], "name": example["name"]} for example in examples]

def get_example_by_id(example_id: str) -> Optional[Dict[str, Any]]:
    """
    Ottiene i dati di un esempio specifico in base all'ID.
    
    Args:
        example_id (str): ID dell'esempio da recuperare
        
    Returns:
        Optional[Dict[str, Any]]: Dati dell'esempio o None se non trovato
    """
    examples = load_example_data()
    for example in examples:
        if example["id"] == example_id:
            return example["data"]
    return None
