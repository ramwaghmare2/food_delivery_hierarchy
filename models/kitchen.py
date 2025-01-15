from . import db
from extensions import bcrypt
from sqlalchemy.dialects.mysql import LONGBLOB
from datetime import datetime, timezone
import pytz

class Kitchen(db.Model):
    __tablename__ = 'kitchens'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(15), nullable=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    order_id = db.Column(db.Integer, nullable=True)
    state = db.Column(db.String(50), nullable=True)
    pin_code = db.Column(db.String(6), nullable=True)
    district = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    image = db.Column(LONGBLOB,nullable=True)
    status = db.Column(db.Enum('activated', 'deactivated'), default='activated')
    online_status = db.Column(db.Boolean, nullable=True, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    
    food_items = db.relationship('FoodItem', backref='kitchen', lazy=True)
    sales = db.relationship('Sales', backref='kitchen', lazy=True)


    # Method to hash password
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # Method to check password
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def __repr__(self):
        return f'<kitchens {self.name}>'
    
    @staticmethod
    def validate_pin_code(pin_code):
        return len(pin_code) == 6 and pin_code.isdigit()