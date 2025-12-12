from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import func, Numeric

from . import db


# ---------- Company ----------
class Company(UserMixin, db.Model):
    __tablename__ = "company"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    email = db.Column(db.String(320), nullable=True)

    # relaties
    clients = db.relationship("Client", back_populates="company", cascade="all, delete-orphan")
    # removed matches relationship: access matches via company.clients -> each client.matches

    def __repr__(self):
        return f"<Company {self.id} {self.name}>"


# ---------- Client ----------
class Client(db.Model):
    __tablename__ = "client"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("public.company.id"), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(320), nullable=False)
    location = db.Column(db.String(200), nullable=True)  # city/municipality
    address = db.Column(db.String(300), nullable=True)   # street + number

    company = db.relationship("Company", back_populates="clients")

    # 1-op-1 met Preferences (elk clientprofiel heeft precies één voorkeurenrecord)
    preferences = db.relationship(
        "Preferences",
        back_populates="client",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # matches: link between client and ground
    matches = db.relationship("Match", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client {self.id} {self.name}>"


# ---------- Ground ----------
class Ground(db.Model):
    __tablename__ = "ground"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)

    # columns from db/schema.sql (no 'soil' column)
    location = db.Column(db.String(200), nullable=False)  # city/municipality
    address = db.Column(db.String(300), nullable=True)    # street + number
    m2 = db.Column(db.Integer, nullable=False)              # area in m2
    budget = db.Column(db.Numeric(12, 2), nullable=False)
    subdivision_type = db.Column(db.String(120), nullable=False)
    owner = db.Column(db.String(200), nullable=False)
    provider = db.Column(db.String(200), nullable=True)   # company name that added this ground
    image_url = db.Column(db.String(1024), nullable=True)  # uploaded or scraped image path/url

    matches = db.relationship("Match", back_populates="ground", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ground {self.id} {self.location} ({self.m2} m2)>"


# ---------- Preferences (1-op-1 met Client) ----------
class Preferences(db.Model):
    __tablename__ = "preferences"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)

    # link naar client (uniek -> één voorkeurenrecord per client)
    client_id = db.Column(db.Integer, db.ForeignKey("public.client.id", ondelete="CASCADE"), nullable=False, unique=True)
    client = db.relationship("Client", back_populates="preferences")

    # gewenste kenmerken
    location = db.Column(db.String(200), nullable=True)
    subdivision_type = db.Column(db.String(120), nullable=True)

    min_m2 = db.Column(db.Integer, nullable=True)
    max_m2 = db.Column(db.Integer, nullable=True)

    min_budget = db.Column(db.Numeric(12, 2), nullable=True)
    max_budget = db.Column(db.Numeric(12, 2), nullable=True)

    # removed matches relationship: a Match is between ground and client; access from preferences through preferences.client.matches

    def __repr__(self):
        return f"<Preferences client={self.client_id}>"


# ---------- Match ----------
class Match(db.Model):
    __tablename__ = "match"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)

    # link to client instead of company or preferences
    client_id = db.Column(db.Integer, db.ForeignKey("public.client.id", ondelete="CASCADE"), nullable=False)
    ground_id = db.Column(db.Integer, db.ForeignKey("public.ground.id", ondelete="CASCADE"), nullable=False)

    # status & (sub)scores zoals in ERD
    status = db.Column(db.String(30), nullable=False, default="pending")
    m2_score = db.Column(db.Float, nullable=True)
    budget_score = db.Column(db.Float, nullable=True)
    location_score = db.Column(db.Float, nullable=True)
    type_score = db.Column(db.Float, nullable=True)

    # Average of four component scores to yield 0-100 percentage
    total_score = db.column_property(
        (func.coalesce(m2_score, 0) + func.coalesce(budget_score, 0) + func.coalesce(location_score, 0) + func.coalesce(type_score, 0)) / 4.0
    )

    client = db.relationship("Client", back_populates="matches")
    ground = db.relationship("Ground", back_populates="matches")

    __table_args__ = (
        db.UniqueConstraint("client_id", "ground_id", name="uq_match_pair"),
        {"schema": "public"},
    )

    def __repr__(self):
        return f"<Match {self.id} client={self.client_id} ground={self.ground_id}>"