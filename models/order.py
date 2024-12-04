from . import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'

    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    kitchen_id = db.Column(db.Integer, db.ForeignKey('kitchens.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    order_status = db.Column(db.Enum('Pending', 'Processing', 'Completed', 'Cancelled'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    sales = db.relationship('Sales', backref='orders', lazy=True)
    customer = db.relationship('Customer', backref='orders')
    kitchen = db.relationship('Kitchen', backref='orders')
    order_items = db.relationship('OrderItem', backref='order', lazy=True)  # Bidirectional link with OrderItem
    # Many-to-Many via OrderItem

    def __repr__(self):
        return f'<Order {self.order_id}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    # Relationships
    
    # order = db.relationship('Order', back_populates='order_items')  # Bidirectional link with Order
    food_item = db.relationship('FoodItem', backref='order_items')  # Bidirectional link with FoodItem
    
    def __repr__(self):
        return f'<OrderItem {self.order_item_id}>'
