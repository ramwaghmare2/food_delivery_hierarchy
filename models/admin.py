from . import db
from datetime import datetime, timezone
from sqlalchemy.dialects.mysql import LONGBLOB
import uuid
class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20), nullable=True)
    #manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'), nullable=True)
    #super_distributor_id = db.Column(db.Integer, db.ForeignKey('super_distributors.id'), nullable=True)
    #distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=True)
    #kitchen_id = db.Column(db.Integer, db.ForeignKey('kitchens.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    image = db.Column(LONGBLOB,nullable=True)
    status = db.Column(db.Boolean, nullable=True, default=False)
    online_status = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Admin {self.name}>'
    
    @staticmethod
    def generate_session_token():
        return str(uuid.uuid4())
    
    def update_last_seen(self):
        self.last_seen = datetime.now(timezone.utc)