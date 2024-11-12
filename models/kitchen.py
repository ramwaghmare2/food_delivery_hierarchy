from . import db
from datetime import datetime
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()  # Initialize Bcrypt instance

class Kitchen(db.Model):
    __tablename__ = 'kitchens'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    _password = db.Column("password", db.String(255), nullable=False)  # Private attribute for hashed password
    contact = db.Column(db.String(15), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    new_field_2 = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    order_id = db.Column(db.Integer, nullable=True)
    country = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    district = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)

    def __init__(self, password, **kwargs):
        super().__init__(**kwargs)
        self.password = password  # This will call the password setter to hash the password

    @property
    def password(self):
        return self._password  # Access the hashed password

    @password.setter
    def password(self, plaintext_password):
        # Hash the password using Bcrypt and store it in the _password field
        self._password = bcrypt.generate_password_hash(plaintext_password).decode('utf-8')

    def check_password(self, plaintext_password):
        # Check if the provided password matches the stored hashed password
        return bcrypt.check_password_hash(self._password, plaintext_password)
