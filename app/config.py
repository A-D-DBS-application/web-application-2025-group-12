# app/config.py
import os
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=True)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": NullPool}  # goed voor Supabase pooler
