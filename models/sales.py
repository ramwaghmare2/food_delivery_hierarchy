from . import db
from datetime import datetime

class Sales(db.Model):
    __tablename__ = 'sales'

    sale_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kitchen_id = db.Column(db.Integer, db.ForeignKey('kitchens.id'), nullable=True)
    cuisine = db.Column(db.String(50), nullable=True)
    item_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.DECIMAL(10, 2), nullable=False) 
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.DECIMAL(10, 2), nullable=False)
    datetime = db.Column(db.DateTime,default=datetime.utcnow)

    def __repr__(self):
        return f'<Sales {self.item_name}>'