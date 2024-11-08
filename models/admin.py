from . import db
from datetime import datetime

class Admin(db.Model):
    __tablename__ = 'admins'
    
    admin_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'), nullable=True)
    super_distributor_id = db.Column(db.Integer, db.ForeignKey('super_distributors.id'), nullable=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=True)
    kitchen_id = db.Column(db.Integer, db.ForeignKey('kitchens.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Admin {self.name}>'
