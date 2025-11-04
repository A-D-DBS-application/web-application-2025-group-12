from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ---------- Company ----------
class Company(db.Model):
    __tablename__ = "company"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(320), nullable=False, unique=True)

    # relaties
    clients = db.relationship("Client", back_populates="company", cascade="all, delete-orphan")
    matches = db.relationship("Match", back_populates="company", cascade="all, delete-orphan")

    # created_at not present in DB schema for company: omit to match DB

    def __repr__(self):
        return f"<Company {self.id} {self.name}>"


# ---------- Client ----------
class Client(db.Model):
    __tablename__ = "client"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(320), nullable=False)
    address = db.Column(db.String(300), nullable=True)

    company = db.relationship("Company", back_populates="clients")

    # 1-op-1 met Preferences (elk clientprofiel heeft precies één voorkeurenrecord)
    preferences = db.relationship(
        "Preferences",
        back_populates="client",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # created_at not present in DB schema for client: omit to match DB

    def __repr__(self):
        return f"<Client {self.id} {self.name}>"


# ---------- Ground ----------
class Ground(db.Model):
    # Match the existing DB schema: public.ground
    __tablename__ = "ground"

    id = db.Column(db.Integer, primary_key=True)

    # columns from db/schema.sql
    soil = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    m2 = db.Column(db.Integer, nullable=False)              # area in m2
    budget = db.Column(db.Numeric(12, 2), nullable=False)
    subdivision_type = db.Column(db.String(120), nullable=False)
    owner = db.Column(db.String(200), nullable=False)

    matches = db.relationship("Match", back_populates="ground", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ground {self.id} {self.location} ({self.m2} m2)>"


# ---------- Preferences (1-op-1 met Client) ----------
class Preferences(db.Model):
    __tablename__ = "preferences"

    id = db.Column(db.Integer, primary_key=True)

    # link naar client (uniek -> één voorkeurenrecord per client)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), nullable=False, unique=True)
    client = db.relationship("Client", back_populates="preferences")

    # gewenste kenmerken
    soil = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    subdivision_type = db.Column(db.String(120), nullable=True)

    min_m2 = db.Column(db.Integer, nullable=True)
    max_m2 = db.Column(db.Integer, nullable=True)

    min_budget = db.Column(db.Numeric(12, 2), nullable=True)
    max_budget = db.Column(db.Numeric(12, 2), nullable=True)

    matches = db.relationship("Match", back_populates="preferences", cascade="all, delete-orphan")

    # created_at not present in DB schema for preferences: omit to match DB

    def __repr__(self):
        return f"<Preferences client={self.client_id}>"


# ---------- Match ----------
class Match(db.Model):
    __tablename__ = "match"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(db.Integer, db.ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    # foreign key to the 'ground' table (schema uses singular 'ground')
    ground_id = db.Column(db.Integer, db.ForeignKey("ground.id", ondelete="CASCADE"), nullable=False)
    preferences_id = db.Column(db.Integer, db.ForeignKey("preferences.id", ondelete="CASCADE"), nullable=False)

    # status & (sub)scores zoals in ERD
    status = db.Column(db.String(30), nullable=False, default="pending")
    m2_score = db.Column(db.Float, nullable=True)
    budget_score = db.Column(db.Float, nullable=True)
    # optioneel: totale score
    total_score = db.Column(db.Float, nullable=True)

    company = db.relationship("Company", back_populates="matches")
    ground = db.relationship("Ground", back_populates="matches")
    preferences = db.relationship("Preferences", back_populates="matches")

    # created_at not present in DB schema for match: omit to match DB

    # unieke combinatie kan handig zijn om dubbele matches te vermijden
    __table_args__ = (
        db.UniqueConstraint("company_id", "ground_id", "preferences_id", name="uq_match_triplet"),
    )

    def __repr__(self):
        return f"<Match {self.id} pref={self.preferences_id} ground={self.ground_id} company={self.company_id}>"
