# app/services.py
from typing import List
from sqlalchemy import and_
from .models import db, Company, Ground, Client, Preferences, Match
from .matching import calculate_match_scores

def generate_matches_for_company(company: Company, min_score: float = 5.0) -> List[Match]:
    """
    Generate matches between a company's clients and available grounds.
    Only creates matches with a score above min_score.
    """
    # Get all clients with preferences
    clients = Client.query.filter(
        and_(
            Client.company_id == company.id,
            Client.preferences != None
        )
    ).all()
    
    # Get all available grounds
    grounds = Ground.query.all()
    
    new_matches = []
    
    for client in clients:
        preferences = client.preferences
        if not preferences:
            continue
            
        for ground in grounds:
            # Skip if match already exists
            existing_match = Match.query.filter_by(
                company_id=company.id,
                ground_id=ground.id,
                preferences_id=preferences.id
            ).first()
            
            if existing_match:
                continue
                
            # Calculate scores
            scores = calculate_match_scores(ground, preferences)
            if scores['total_score'] >= min_score:
                match = Match(
                    company=company,
                    ground=ground,
                    preferences=preferences,
                    m2_score=scores['m2_score'] * 10,  # Store scores out of 10
                    budget_score=scores['budget_score'] * 10,
                    total_score=scores['total_score']
                )
                new_matches.append(match)
    
    if new_matches:
        db.session.bulk_save_objects(new_matches)
        db.session.commit()
    
    return new_matches