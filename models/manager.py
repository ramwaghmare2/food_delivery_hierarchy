from . import db
from datetime import datetime
from extensions import bcrypt
from sqlalchemy.dialects.mysql import LONGBLOB

class Manager(db.Model):
    __tablename__ = 'managers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    #super_distributor_id = db.Column(db.Integer, db.ForeignKey('super_distributors.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    #image = db.Column(db.String(255), nullable=True)  
    image = db.Column(LONGBLOB,nullable=True)
    status = db.Column(db.Enum('activated', 'deactivated'), default='activated')
    # Method to hash password
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # Method to check password
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def __repr__(self):
        return f'<Manager {self.name}>'
    
