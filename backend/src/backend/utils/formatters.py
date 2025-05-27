from typing import List, Dict
import json

def format_badges(badges_string: str) -> List[str]:
    """Convert badges string to list"""
    if not badges_string:
        return []
    return [badge.strip() for badge in badges_string.split(",") if badge.strip()]

def badges_to_string(badges: List[str]) -> str:
    """Convert badges list to string"""
    return ",".join(badges)

def format_score_display(score: int) -> str:
    """Format score for display"""
    if score >= 1000:
        return f"{score/1000:.1f}k"
    return str(score)

def calculate_user_level(score: int) -> Dict[str, any]:
    """Calculate user level based on score"""
    levels = [
        {"level": 1, "name": "Novizio", "min_score": 0},
        {"level": 2, "name": "Apprendista", "min_score": 100},
        {"level": 3, "name": "Esperto", "min_score": 500},
        {"level": 4, "name": "Maestro", "min_score": 1000},
        {"level": 5, "name": "Gran Maestro", "min_score": 2500},
    ]
    
    current_level = levels[0]
    for level in levels:
        if score >= level["min_score"]:
            current_level = level
        else:
            break
    
    # Calculate progress to next level
    next_level_index = current_level["level"]
    if next_level_index < len(levels):
        next_level = levels[next_level_index]
        progress = (score - current_level["min_score"]) / (next_level["min_score"] - current_level["min_score"])
        progress = min(progress, 1.0)
    else:
        progress = 1.0
        next_level = None
    
    return {
        "current_level": current_level,
        "next_level": next_level,
        "progress": progress
    }
