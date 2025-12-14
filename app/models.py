from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import func, Numeric, CheckConstraint, Enum

from . import db


# ---------- Company ----------
class Company(UserMixin, db.Model):
    __tablename__ = "company"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    email = db.Column(db.String(320), nullable=False)

    clients = db.relationship("Client", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company {self.id} {self.name}>"


# ---------- Client ----------
class Client(db.Model):
    __tablename__ = "client"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("public.company.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(320), nullable=False)
    location = db.Column(db.String(200), nullable=False)  # city
    address = db.Column(db.String(300), nullable=False)   # street + number

    company = db.relationship("Company", back_populates="clients")
    preferences = db.relationship("Preferences", back_populates="client", uselist=False, cascade="all, delete-orphan")
    matches = db.relationship("Match", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client {self.id} {self.name}>"


# ---------- Ground ----------
class Ground(db.Model):
    __tablename__ = "ground"
    __table_args__ = (
        CheckConstraint("m2 >= 0", name="ck_ground_m2_nonnegative"),
        CheckConstraint("budget >= 0", name="ck_ground_budget_nonnegative"),
        {"schema": "public"},
    )

    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(200), nullable=False)  # city
    address = db.Column(db.String(300), nullable=False)    # street + number
    m2 = db.Column(db.Integer, nullable=False)              # area in m2
    budget = db.Column(db.Numeric(12, 2), nullable=False)
    subdivision_type = db.Column(db.String(120), nullable=False)
    owner = db.Column(db.String(200), nullable=False) #owner of the ground
    provider = db.Column(db.String(200), nullable=False)   # company name that added this ground
    image_url = db.Column(db.Text, nullable=False)  # uploaded or scraped image path/url

    matches = db.relationship("Match", back_populates="ground", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ground {self.id} {self.location} ({self.m2} m2)>"


# ---------- Preferences (1-op-1 met Client) ----------
class Preferences(db.Model):
    __tablename__ = "preferences"
    __table_args__ = (
        CheckConstraint("min_m2 <= max_m2", name="ck_preferences_m2_range"),
        CheckConstraint("min_budget <= max_budget", name="ck_preferences_budget_range"),
        {"schema": "public"},
    )

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("public.client.id", ondelete="CASCADE"), nullable=False, unique=True)
    location = db.Column(db.String(200), nullable=False)
    subdivision_type = db.Column(db.String(120), nullable=False)
    min_m2 = db.Column(db.Integer, nullable=False)
    max_m2 = db.Column(db.Integer, nullable=False)
    min_budget = db.Column(db.Numeric(12, 2), nullable=False)
    max_budget = db.Column(db.Numeric(12, 2), nullable=False)

    client = db.relationship("Client", back_populates="preferences")

    def __repr__(self):
        return f"<Preferences client={self.client_id}>"


# ---------- Match ----------
class Match(db.Model):
    __tablename__ = "match"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("public.client.id", ondelete="CASCADE"), nullable=False)
    ground_id = db.Column(db.Integer, db.ForeignKey("public.ground.id", ondelete="CASCADE"), nullable=False)
    status = db.Column(Enum("pending", "approved", "rejected", name="match_status", create_type=False), nullable=False, server_default="pending")

    m2_score = db.Column(db.Float, nullable=False)
    budget_score = db.Column(db.Float, nullable=False)
    location_score = db.Column(db.Float, nullable=False)
    type_score = db.Column(db.Float, nullable=False)
    total_score = db.column_property( # Average of four component scores to yield 0-100 percentage
        (func.coalesce(m2_score, 0)
         + func.coalesce(budget_score, 0)
         + func.coalesce(location_score, 0)
         + func.coalesce(type_score, 0)) / 4.0
    )

    client = db.relationship("Client", back_populates="matches")
    ground = db.relationship("Ground", back_populates="matches")

    def __repr__(self):
        return f"<Match {self.id} client={self.client_id} ground={self.ground_id}>"