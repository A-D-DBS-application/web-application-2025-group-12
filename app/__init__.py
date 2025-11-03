# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from .config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # DB check + tabellen aanmaken
    with app.app_context():
        db.session.execute(text("select 1"))
        from .models import User, Listing
        db.create_all()
        # Zorg voor een demo-user met id=1 (voor “ingelogd” simulatie)
        if not User.query.get(1):
            demo = User(id=1, email="demo@example.com")
            db.session.add(demo)
            db.session.commit()

    # Blueprints / routes
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
