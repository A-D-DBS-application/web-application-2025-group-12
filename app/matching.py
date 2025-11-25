def compute_match_scores(ground, preferences):
    """Simple scoring: budget + m2 + location. Returns dict with scores."""
    
    # Budget score
    if preferences.min_budget and preferences.max_budget:
        if preferences.min_budget <= ground.budget <= preferences.max_budget:
            budget_score = 100
        else:
            budget_score = 50
    else:
        budget_score = 50
    
    # M2 score
    if preferences.min_m2 and preferences.max_m2:
        if preferences.min_m2 <= ground.m2 <= preferences.max_m2:
            m2_score = 100
        else:
            m2_score = 50
    else:
        m2_score = 50
    
    # Location score
    location_score = 50  # default
    if preferences.location and ground.location:
        if preferences.location.lower() in ground.location.lower():
            location_score = 100
        elif ground.location.lower() in preferences.location.lower():
            location_score = 70
        else:
            location_score = 0
    
    return {
        'budget_score': budget_score,
        'm2_score': m2_score,
        'location_score': location_score
    }
