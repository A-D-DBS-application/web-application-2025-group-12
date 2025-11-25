from . import db
from sqlalchemy import Numeric

class Company(db.Model):
    __tablename__ = 'company'
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    email = db.Column(db.String(320))

class Client(db.Model):
    __tablename__ = 'client'
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('public.company.id'))
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(320), nullable=False, unique=True)
    address = db.Column(db.String(300), nullable=False)

class Ground(db.Model):
    __tablename__ = 'ground'
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(200), nullable=False)
    m2 = db.Column(db.Integer, nullable=False)
    budget = db.Column(Numeric(12, 2), nullable=False)
    subdivision_type = db.Column(db.String(120), nullable=False)
    owner = db.Column(db.String(200), nullable=False)

class Preferences(db.Model):
    __tablename__ = 'preferences'
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('public.client.id'), nullable=False)
    location = db.Column(db.String(200))
    subdivision_type = db.Column(db.String(120))
    min_m2 = db.Column(db.Integer)
    max_m2 = db.Column(db.Integer)
    min_budget = db.Column(Numeric(12, 2))
    max_budget = db.Column(Numeric(12, 2))

class Match(db.Model):
    __tablename__ = 'match'
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('public.company.id'), nullable=False)
    ground_id = db.Column(db.Integer, db.ForeignKey('public.ground.id'), nullable=False)
    preferences_id = db.Column(db.Integer, db.ForeignKey('public.preferences.id'), nullable=False)
    m2_score = db.Column(Numeric(5, 2), nullable=False, default=0)
    budget_score = db.Column(Numeric(5, 2), nullable=False, default=0)
    location_score = db.Column(Numeric(5, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default='pending')
