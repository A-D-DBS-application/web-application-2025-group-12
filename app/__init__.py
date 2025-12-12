from flask import Flask, session
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from .config import Config
from .helpers import get_match_score

db = SQLAlchemy()

def format_price(price):
    """Format price with period as thousands separator, no decimals (e.g., 123.456)"""
    if price is None:
        return '?'
    try:
        price = float(price)
        # Format as integer with no decimals, using comma as thousands separator
        formatted = f"{int(round(price)):,}"
        # Replace comma with period for thousands separator
        return formatted.replace(',', '.')
    except (ValueError, TypeError):
        return '?'

def format_number(number):
    """Format number with period as thousands separator (e.g., 10.000)"""
    if number is None:
        return '?'
    try:
        number = int(number)
        # Format with comma as thousands separator
        formatted = f"{number:,}"
        # Replace comma with period for thousands separator
        return formatted.replace(',', '.')
    except (ValueError, TypeError):
        return '?'

def match_percent(match):
    """Return an integer percent in [0,100] for a Match-like object.
    Wrapper around get_match_score that returns rounded integer.
    """
    return int(round(get_match_score(match)))

def status_badge(status: str):
    """Return a small HTML badge for a match status.
    Normalizes legacy values (e.g., 'accepted' -> 'approved').
    """
    try:
        s = (status or '').strip().lower()
    except Exception:
        s = ''
    if s == 'accepted':
        s = 'approved'
    if s == 'approved':
        return Markup('<div class="tag success" style="margin-top:6px">Approved</div>')
    if s == 'pending':
        return Markup('<div class="muted" style="margin-top:6px">Pending</div>')
    return Markup('<div class="muted" style="margin-top:6px"></div>')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # Register custom Jinja2 filters
    app.jinja_env.filters['format_price'] = format_price
    app.jinja_env.filters['format_number'] = format_number
    app.jinja_env.filters['match_percent'] = match_percent
    app.jinja_env.filters['status_badge'] = status_badge

    @app.context_processor
    def inject_user_context():
        """Provide current user's display name and role to all templates."""
        name = None
        role = session.get('role')
        try:
            # Import locally to avoid circular import issues during app init
            from .models import Company, Client
            if role == 'company' and session.get('company_id'):
                company = Company.query.get(session['company_id'])
                name = company.name if company else None
            elif role == 'client' and session.get('client_id'):
                client = Client.query.get(session['client_id'])
                name = client.name if client else None
        except Exception:
            # Fail quietly; templates handle None
            pass
        return dict(current_user_name=name, current_role=role)
    
    from . import routes
    routes.init_routes(app)
    
    return app
