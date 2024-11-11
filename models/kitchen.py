from . import db
from datetime import datetime

class Kitchen(db.Model):
    __tablename__ = 'kitchens'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(150), nullable=True)
    new_field_2 = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    order_id = db.Column(db.Integer, nullable=True)
    country = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)

    def __repr__(self):
        return f'<Kitchen {self.name}>'
