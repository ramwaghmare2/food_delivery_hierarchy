from . import db
from datetime import datetime, timezone

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    status = db.Column(db.Enum('activated', 'deactivated'), default='activated')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<Customer {self.name}>'
    
    
