from datetime import datetime
from app import db

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    logo_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    collaborations = db.relationship('Collaboration', backref='company', lazy=True, cascade='all, delete-orphan')
    opportunities = db.relationship('Opportunity', backref='company', lazy=True, cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='company', lazy=True, cascade='all, delete-orphan')

class Collaboration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # Active, Completed, On Hold
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)
    kpi_revenue = db.Column(db.Float)
    kpi_satisfaction = db.Column(db.Integer)  # 1-10 scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    documents = db.relationship('Document', backref='collaboration', lazy=True, cascade='all, delete-orphan')

class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    stage = db.Column(db.String(50), nullable=False)  # Lead, Meeting, Proposal, Negotiation, Closed
    expected_revenue = db.Column(db.Float)
    probability = db.Column(db.Integer)  # 0-100%
    next_meeting_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(100))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    collaboration_id = db.Column(db.Integer, db.ForeignKey('collaboration.id', ondelete='CASCADE'))
    description = db.Column(db.Text)
    version = db.Column(db.String(50))
