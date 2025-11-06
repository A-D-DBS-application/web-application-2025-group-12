# app/__init__.py
from flask import Flask
from flask_login import LoginManager
from sqlalchemy import text
from .config import Config       # ← HIER je Config ophalen
from .models import db, Company  # db = SQLAlchemy() staat in models.py

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Log in om deze pagina te bekijken.'
    
    @login_manager.user_loader
    def load_user(id):
        return Company.query.get(int(id))

    # Jinja filters: euro formatting and thousands separator
    def euro_format(value):
        try:
            num = float(value)
        except Exception:
            return value
        s = f"{num:,.2f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"€ {s}"

    def thousands_format(value):
        try:
            n = int(value)
        except Exception:
            return value
        s = f"{n:,}".replace(",", ".")
        return s

    app.jinja_env.filters["euro"] = euro_format
    app.jinja_env.filters["thousands"] = thousands_format

    # 1) Laad AL je settings (SECRET_KEY, SQLALCHEMY_DATABASE_URI, …)
    app.config.from_object(Config)

    # 2) Koppel SQLAlchemy aan deze app
    db.init_app(app)

    # 3) (Optional) quick DB connectivity check — don't crash the app if remote DB is unreachable
    with app.app_context():
        try:
            db.session.execute(text("select 1"))   # snelle connectivity check
        except Exception as exc:
            # Log and continue: in many dev setups the remote DB may be unavailable.
            app.logger.warning("DB connectivity check failed: %s", exc)
        # Do NOT call db.create_all() automatically against a remote DB (Supabase).
        # If you need to create local/dev tables, run a separate script or
        # uncomment the following line when running against a local DB only.
        # db.create_all()

    # 4) Register the blueprint
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app