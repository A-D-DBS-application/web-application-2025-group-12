"""
VOORSTEL: Hybride model dat hun conventies combineert met jullie functionaliteit
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# ---------- Company ----------
class Company(UserMixin, db.Model):
    __tablename__ = "company"
    __table_args__ = {'schema': 'public'}

    # Hun conventie: company_id i.p.v. id
    company_id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    email = db.Column(db.String(320), nullable=False)

    # Relationships
    clients = db.relationship("Client", back_populates="company", cascade="all, delete-orphan")
    matches = db.relationship("Match", back_populates="company", cascade="all, delete-orphan")

    # Flask-Login vereist get_id()
    def get_id(self):
        return str(self.company_id)

    def __repr__(self):
        return f"<Company {self.company_id} {self.name}>"


# ---------- Client ----------
class Client(db.Model):
    __tablename__ = "client"
    __table_args__ = {'schema': 'public'}

    client_id = db.Column(db.BigInteger, primary_key=True)
    company_id = db.Column(db.BigInteger, db.ForeignKey("public.company.company_id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(320), nullable=False, unique=True)
    address = db.Column(db.String(300), nullable=True)

    # Relationships
    company = db.relationship("Company", back_populates="clients")
    preferences = db.relationship("Preferences", back_populates="client", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client {self.client_id} {self.name}>"


# ---------- Preferences ----------
class Preferences(db.Model):
    __tablename__ = "preferences"
    __table_args__ = {'schema': 'public'}

    preferences_id = db.Column(db.BigInteger, primary_key=True)
    client_id = db.Column(db.BigInteger, db.ForeignKey("public.client.client_id"), nullable=False, unique=True)
    
    location = db.Column(db.String(200), nullable=True)
    subdivision_type = db.Column(db.String(120), nullable=True)
    min_m2 = db.Column(db.Integer, nullable=True)
    max_m2 = db.Column(db.Integer, nullable=True)
    min_budget = db.Column(db.Numeric(12, 2), nullable=True)
    max_budget = db.Column(db.Numeric(12, 2), nullable=True)

    # Relationships
    client = db.relationship("Client", back_populates="preferences")
    # BELANGRIJK: preferences kan MEERDERE matches hebben!
    matches = db.relationship("Match", back_populates="preferences", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Preferences {self.preferences_id} client={self.client_id}>"


# ---------- Ground ----------
class Ground(db.Model):
    __tablename__ = "ground"
    __table_args__ = {'schema': 'public'}

    ground_id = db.Column(db.BigInteger, primary_key=True)
    
    location = db.Column(db.String(200), nullable=False)
    # Houden: budget (consistenter met preferences.min_budget/max_budget)
    budget = db.Column(db.Numeric(12, 2), nullable=False)
    m2 = db.Column(db.Integer, nullable=False)
    subdivision_type = db.Column(db.String(120), nullable=False)
    # Toevoegen: provider (nieuwe naam voor owner)
    provider = db.Column(db.String(200), nullable=False)

    # BELANGRIJK: ground kan MEERDERE matches hebben!
    matches = db.relationship("Match", back_populates="ground", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ground {self.ground_id} {self.location}>"


# ---------- Match (MANY-TO-MANY blijft behouden!) ----------
class Match(db.Model):
    __tablename__ = "match"
    __table_args__ = {'schema': 'public'}

    match_id = db.Column(db.BigInteger, primary_key=True)
    
    # Foreign keys (GEEN unique constraint - many-to-many!)
    company_id = db.Column(db.BigInteger, db.ForeignKey("public.company.company_id"), nullable=False)
    ground_id = db.Column(db.BigInteger, db.ForeignKey("public.ground.ground_id"), nullable=False)
    preferences_id = db.Column(db.BigInteger, db.ForeignKey("public.preferences.preferences_id"), nullable=False)
    
    # Scores
    budget_score = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    m2_score = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    location_score = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default='pending')

    # Relationships
    company = db.relationship("Company", back_populates="matches")
    ground = db.relationship("Ground", back_populates="matches")
    preferences = db.relationship("Preferences", back_populates="matches")

    def __repr__(self):
        return f"<Match {self.match_id} client_pref={self.preferences_id} ground={self.ground_id}>"


# MIGRATIE NOTITIES:
# ===================
# 1. Alle routes moeten aangepast: session['company_id'] blijft werken (geen wijziging)
# 2. Queries aanpassen: Company.query.get(id) → Company.query.get(company_id)
# 3. Template variabelen: {{ company.id }} → {{ company.company_id }}
# 4. Foreign keys in routes: blijven hetzelfde maar met nieuwe namen
# 5. Database schema: ALLE id kolommen hernoemen naar {table}_id
# 6. Ground.owner → Ground.provider (naam wijziging)
# 7. BELANGRIJK: Match blijft many-to-many (GEEN unique constraints op FKs!)
