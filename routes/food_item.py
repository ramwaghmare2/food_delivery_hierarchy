from flask import Blueprint, request, jsonify
from models import db, FoodItem

food_item_bp = Blueprint('food_item', __name__)

# Create a new FoodItem
@food_item_bp.route('/food_items', methods=['POST'])
def create_food_item():
    data = request.json
    new_food_item = FoodItem(
        name=data.get('name'),
        description=data.get('description'),
        price=data.get('price'),
        cuisine_id=data.get('cuisine_id')
    )
    db.session.add(new_food_item)
    db.session.commit()
    return jsonify({'message': 'Food item created successfully', 'food_item_id': new_food_item.id}), 201

# Get all FoodItems
@food_item_bp.route('/food_items', methods=['GET'])
def get_food_items():
    food_items = FoodItem.query.all()
    food_item_list = [
        {
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': item.price,
            'cuisine_id': item.cuisine_id
        } for item in food_items
    ]
    return jsonify(food_item_list), 200

# Get a specific FoodItem by ID
@food_item_bp.route('/food_items/<int:id>', methods=['GET'])
def get_food_item(id):
    food_item = FoodItem.query.get_or_404(id)
    food_item_data = {
        'id': food_item.id,
        'name': food_item.name,
        'description': food_item.description,
        'price': food_item.price,
        'cuisine_id': food_item.cuisine_id
    }
    return jsonify(food_item_data), 200

# Update a FoodItem by ID
@food_item_bp.route('/food_items/<int:id>', methods=['PUT'])
def update_food_item(id):
    data = request.json
    food_item = FoodItem.query.get_or_404(id)
    food_item.name = data.get('name', food_item.name)
    food_item.description = data.get('description', food_item.description)
    food_item.price = data.get('price', food_item.price)
    food_item.cuisine_id = data.get('cuisine_id', food_item.cuisine_id)
    db.session.commit()
    return jsonify({'message': 'Food item updated successfully'}), 200

# Delete a FoodItem by ID
@food_item_bp.route('/food_items/<int:id>', methods=['DELETE'])
def delete_food_item(id):
    food_item = FoodItem.query.get_or_404(id)
    db.session.delete(food_item)
    db.session.commit()
    return jsonify({'message': 'Food item deleted successfully'}), 200
