from typing import List, Dict
import json

def format_badges(badges_string: str) -> List[str]:
    """
    Converte una stringa di badge in una lista.
    
    Args:
        badges_string: stringa contenente i badge separati da virgole
        
    Returns:
        Lista di badge, con spazi extra rimossi.
        Se la stringa è vuota, ritorna una lista vuota.
    
    Esempio:
        "badge1, badge2, badge3" -> ["badge1", "badge2", "badge3"]
    """
    if not badges_string:
        return []
    return [badge.strip() for badge in badges_string.split(",") if badge.strip()]

def badges_to_string(badges: List[str]) -> str:
    """
    Converte una lista di badge in una stringa.
    
    Args:
        badges: lista di badge da convertire
        
    Returns:
        Stringa con i badge separati da virgole.
    
    Esempio:
        ["badge1", "badge2", "badge3"] -> "badge1,badge2,badge3"
    """
    return ",".join(badges)

def format_score_display(score: int) -> str:
    """
    Formatta il punteggio per la visualizzazione.
    Converte i punteggi >= 1000 in formato 'k'.
    
    Args:
        score: punteggio da formattare
        
    Returns:
        Stringa formattata del punteggio.
    
    Esempio:
        1500 -> "1.5k"
        800 -> "800"
    """
    if score >= 1000:
        return f"{score/1000:.1f}k"
    return str(score)

def calculate_user_level(score: int) -> Dict[str, any]:
    """
    Calcola il livello dell'utente basato sul punteggio.
    Include il livello attuale, il prossimo livello e il progresso.
    
    Args:
        score: punteggio dell'utente
        
    Returns:
        Dizionario contenente:
        - current_level: livello attuale (dizionario con level, name, min_score)
        - next_level: prossimo livello o None se al massimo
        - progress: progresso verso il prossimo livello (0.0 - 1.0)
    """
    # Definizione dei livelli con relativi punteggi minimi
    levels = [
        {"level": 1, "name": "Novizio", "min_score": 0},      # Livello base
        {"level": 2, "name": "Apprendista", "min_score": 100}, # Primi progressi
        {"level": 3, "name": "Esperto", "min_score": 500},    # Competenza intermedia
        {"level": 4, "name": "Maestro", "min_score": 1000},   # Alta competenza
        {"level": 5, "name": "Gran Maestro", "min_score": 2500}, # Massima expertise
    ]
    
    # Trova il livello corrente dell'utente
    current_level = levels[0]
    for level in levels:
        if score >= level["min_score"]:
            current_level = level
        else:
            break
    
    # Calcola il progresso verso il prossimo livello
    next_level_index = current_level["level"]
    if next_level_index < len(levels):
        # Se non è all'ultimo livello, calcola il progresso
        next_level = levels[next_level_index]
        progress = (score - current_level["min_score"]) / (next_level["min_score"] - current_level["min_score"])
        progress = min(progress, 1.0)  # Assicura che il progresso non superi il 100%
    else:
        # Se è all'ultimo livello, imposta progresso al 100%
        progress = 1.0
        next_level = None
    
    return {
        "current_level": current_level,
        "next_level": next_level,
        "progress": progress
    }
