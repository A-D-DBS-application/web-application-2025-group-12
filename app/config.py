# app/config.py
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

# Zoek .env automatisch vanaf app/… omhoog
env_path = (Path(__file__).resolve().parent.parent / ".env")
load_dotenv(env_path, override=True)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")  # geen [] -> geen KeyError
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": NullPool}  # aanbevolen met pooler
