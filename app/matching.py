# app/matching.py
from typing import List, Dict, Union
import math
from .models import Ground, Preferences

def calculate_budget_score(budget: float, min_budget: float = None, max_budget: float = None) -> float:
    """Calculate score (0-1) based on how well a budget matches preferences."""
    if min_budget is None and max_budget is None:
        return 1.0  # No preferences = perfect match
    
    if min_budget and budget < min_budget:
        return 0.0
    if max_budget and budget > max_budget:
        return 0.0
    
    if min_budget and max_budget:
        # Score based on position within range (higher = closer to middle of range)
        range_mid = (min_budget + max_budget) / 2
        max_distance = (max_budget - min_budget) / 2
        distance = abs(budget - range_mid)
        return max(0, 1 - (distance / max_distance))
    
    if min_budget:
        # Score based on how much above minimum (up to 50% above = good)
        overshoot = budget - min_budget
        return min(1, max(0, 1 - (overshoot / (min_budget * 0.5))))
    
    if max_budget:
        # Score based on how much below maximum (up to 50% below = good)
        undershoot = max_budget - budget
        return min(1, max(0, 1 - (undershoot / (max_budget * 0.5))))
    
    return 0.0

def calculate_m2_score(m2: int, min_m2: int = None, max_m2: int = None) -> float:
    """Calculate score (0-1) based on how well an area matches preferences."""
    if min_m2 is None and max_m2 is None:
        return 1.0  # No preferences = perfect match
    
    if min_m2 and m2 < min_m2:
        return 0.0
    if max_m2 and m2 > max_m2:
        return 0.0
    
    if min_m2 and max_m2:
        # Score based on position within range (higher = closer to middle of range)
        range_mid = (min_m2 + max_m2) / 2
        max_distance = (max_m2 - min_m2) / 2
        distance = abs(m2 - range_mid)
        return max(0, 1 - (distance / max_distance))
    
    if min_m2:
        # Score based on how much above minimum (up to 50% above = good)
        overshoot = m2 - min_m2
        return min(1, max(0, 1 - (overshoot / (min_m2 * 0.5))))
    
    if max_m2:
        # Score based on how much below maximum (up to 50% below = good)
        undershoot = max_m2 - m2
        return min(1, max(0, 1 - (undershoot / (max_m2 * 0.5))))
    
    return 0.0

def calculate_match_scores(ground: Ground, preferences: Preferences) -> Dict[str, Union[float, bool]]:
    """Calculate match scores between a ground and preferences."""
    scores = {
        'm2_score': calculate_m2_score(
            ground.m2,
            preferences.min_m2,
            preferences.max_m2
        ),
        'budget_score': calculate_budget_score(
            float(ground.budget),  # Convert Decimal to float
            float(preferences.min_budget) if preferences.min_budget else None,
            float(preferences.max_budget) if preferences.max_budget else None
        )
    }
    
    # Check exact matches (if preference is set)
    scores['location_match'] = (not preferences.location or 
                              ground.location == preferences.location)
    scores['soil_match'] = (not preferences.soil or 
                          ground.soil == preferences.soil)
    scores['subdivision_match'] = (not preferences.subdivision_type or 
                                 ground.subdivision_type == preferences.subdivision_type)
    
    # Calculate total score (0-10)
    weights = {
        'm2_score': 0.3,        # 30% weight
        'budget_score': 0.3,    # 30% weight
        'location_match': 0.2,  # 20% weight
        'soil_match': 0.1,      # 10% weight
        'subdivision_match': 0.1 # 10% weight
    }
    
    total_score = sum(
        scores[key] * weights[key] * 10  # Multiply by 10 to get score out of 10
        for key in weights
    )
    
    scores['total_score'] = round(total_score, 2)
    return scores