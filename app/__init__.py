from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

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

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # Register custom Jinja2 filter
    app.jinja_env.filters['format_price'] = format_price
    
    from . import routes
    routes.init_routes(app)
    
    return app
