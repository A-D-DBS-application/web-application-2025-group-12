"""
Helper constants and utility functions for GroundMatch
Centralizes dropdown options, types, and shared logic
"""

# ============================================================================
# SUBDIVISION TYPES - Used for ground types and preferences
# ============================================================================

SUBDIVISION_TYPES = [
    ('detached', 'Detached'),
    ('semi_detached', 'Semi Detached'),
    ('terraced', 'Terraced'),
    ('apartment', 'Apartment'),
    ('development_plot', 'Development Plot'),
]

# For easy validation
SUBDIVISION_TYPE_VALUES = [value for value, _ in SUBDIVISION_TYPES]

def get_subdivision_types():
    """Return list of valid subdivision type values"""
    return SUBDIVISION_TYPE_VALUES

def get_subdivision_types_display():
    """Return list of (value, display_name) tuples for dropdowns"""
    return SUBDIVISION_TYPES

def normalize_subdivision_type(raw_type):
    """
    Normalize free-text subdivision type to one of the allowed values.
    Handles various Dutch and English synonyms.
    
    Args:
        raw_type: String input from form or scraper
        
    Returns:
        Normalized subdivision type or None if no match
    """
    if not raw_type:
        return None
        
    t = raw_type.strip().lower().replace('-', ' ').replace('_', ' ')
    
    # Mapping of synonyms to standard values
    mapping = {
        # Open/Detached
        'open bebouwing': 'detached',
        'open': 'detached',
        'vrijstaand': 'detached',
        'detached': 'detached',
        'residential': 'detached',
        
        # Semi-detached
        'halfopen': 'semi_detached',
        'half open': 'semi_detached',
        'halfopen bebouwing': 'semi_detached',
        'half open bebouwing': 'semi_detached',
        'semi detached': 'semi_detached',
        'semi-detached': 'semi_detached',
        
        # Terraced
        'gesloten': 'terraced',
        'rijwoning': 'terraced',
        'rij': 'terraced',
        'terraced': 'terraced',
        
        # Apartment
        'appartement': 'apartment',
        'woonst': 'apartment',
        'apartment': 'apartment',
        
        # Development plot
        'projectgrond': 'development_plot',
        'verkaveling': 'development_plot',
        'bouwgrond': 'development_plot',
        'kavel': 'development_plot',
        'plot': 'development_plot',
        'grond': 'development_plot',
        'development plot': 'development_plot',
        'mixed use': 'development_plot',
        'mixed-use': 'development_plot',
        'residual': 'development_plot',
    }
    
    # Direct mapping
    if t in mapping:
        return mapping[t]
    
    # If user typed allowed value with spaces, normalize
    normalized = t.replace(' ', '_')
    if normalized in SUBDIVISION_TYPE_VALUES:
        return normalized
    
    return None


# ============================================================================
# MATCH STATUS TYPES
# ============================================================================

MATCH_STATUSES = [
    ('approved', 'Approved'),
    ('pending', 'Pending'),
]

def get_match_statuses():
    """Return list of valid match status values"""
    return [value for value, _ in MATCH_STATUSES]


# ============================================================================
# USER ROLES
# ============================================================================

USER_ROLES = {
    'company': 'Company',
    'client': 'Client',
}

def get_user_roles():
    """Return dict of user roles"""
    return USER_ROLES


# ============================================================================
# FILTER HELPERS
# ============================================================================

def parse_int_filter(value, default=None):
    """Safely parse integer from filter input"""
    if not value:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_float_filter(value, default=None):
    """Safely parse float from filter input"""
    if not value:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
