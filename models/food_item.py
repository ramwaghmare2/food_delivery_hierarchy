from . import db
from datetime import datetime, timezone
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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    image = db.Column(LONGBLOB, nullable=True)
    status = db.Column(db.Enum('activated', 'deactivated'), default='activated', server_default='activated')

    # Relationships
    order_items = db.relationship('OrderItem', back_populates='food_item', lazy='dynamic')
    sales = db.relationship('Sales', backref='food_items', lazy=True)
   
    def __repr__(self):
        return f'<FoodItem {self.item_name}>'
    
    @staticmethod
    def validate_price(price):
        return price >= 0
