import os
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

# Laad .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=True)

# >>> Voeg dit toe <<<
RUNTIME_DB_URL = os.environ.get("DATABASE_URL")
print("### DATABASE_URL at runtime:", RUNTIME_DB_URL)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = RUNTIME_DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": NullPool}
