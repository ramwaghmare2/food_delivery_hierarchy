from . import db
from datetime import datetime
from sqlalchemy.dialects.mysql import LONGBLOB

class FoodItem(db.Model):
    __tablename__ = 'food_items'
    
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean, default=True)
    cuisine_id = db.Column(db.Integer, db.ForeignKey('cuisines.id'), nullable=False)
    kitchen_id = db.Column(db.Integer, db.ForeignKey('kitchens.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    image = db.Column(LONGBLOB, nullable=True)
    status = db.Column(db.Enum('activated', 'deactivated'), default='activated')

    # Relationships
    order_item = db.relationship('OrderItem', backref='food_items', lazy=True)
    sales = db.relationship('Sales', backref='food_items', lazy=True)
    # kitchen = db.relationship('Kitchen', backref='food_items')
    # orders = db.relationship('Order', secondary='order_items', back_populates='food_items')  # Many-to-Many via OrderItem
    # order_items = db.relationship('OrderItem', back_populates='food_item')  # Bidirectional link with OrderItem

    def __repr__(self):
        return f'<FoodItem {self.item_name}>'
