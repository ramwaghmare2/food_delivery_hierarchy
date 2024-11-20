from . import db
from datetime import datetime
from sqlalchemy.dialects.mysql import LONGBLOB

class Distributor(db.Model):
    __tablename__ = 'distributors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    super_distributor = db.Column(db.Integer, db.ForeignKey('super_distributors.id'), nullable =True)
    #kitchen_id = db.Column(db.Integer, db.ForeignKey('kitchens.id'), nullable=True)
    status = db.Column(db.Enum('activated', 'deactivated'), default='activated')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    image = db.Column(LONGBLOB,nullable=True)

    def __repr__(self):
        return f'<Distributor {self.name}>'
    
