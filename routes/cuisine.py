from flask import Blueprint, request, jsonify
from models import db, Cuisine

cuisine_bp = Blueprint('cuisine', __name__)

# Create a new Cuisine
@cuisine_bp.route('/cuisine', methods=['POST'])
def create_cuisine():
    data = request.json
    new_cuisine = Cuisine(
        name=data.get('name'),
        description=data.get('description')
    )
    db.session.add(new_cuisine)
    db.session.commit()
    return jsonify({'message': 'Cuisine created successfully', 'cuisine_id': new_cuisine.id}), 201

# Get all Cuisines
@cuisine_bp.route('/cuisines', methods=['GET'])
def get_cuisines():
    cuisines = Cuisine.query.all()
    cuisine_list = [{'id': cuisine.id, 'name': cuisine.name, 'description': cuisine.description} for cuisine in cuisines]
    return jsonify(cuisine_list), 200

# Get a specific Cuisine by ID
@cuisine_bp.route('/cuisines/<int:id>', methods=['GET'])
def get_cuisine(id):
    cuisine = Cuisine.query.get_or_404(id)
    cuisine_data = {'id': cuisine.id, 'name': cuisine.name, 'description': cuisine.description}
    return jsonify(cuisine_data), 200

# Update a Cuisine by ID
@cuisine_bp.route('/cuisines/<int:id>', methods=['PUT'])
def update_cuisine(id):
    data = request.json
    cuisine = Cuisine.query.get_or_404(id)
    cuisine.name = data.get('name', cuisine.name)
    cuisine.description = data.get('description', cuisine.description)
    db.session.commit()
    return jsonify({'message': 'Cuisine updated successfully'}), 200

# Delete a Cuisine by ID
@cuisine_bp.route('/cuisines/<int:id>', methods=['DELETE'])
def delete_cuisine(id):
    cuisine = Cuisine.query.get_or_404(id)
    db.session.delete(cuisine)
    db.session.commit()
    return jsonify({'message': 'Cuisine deleted successfully'}), 200
