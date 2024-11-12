from flask import Blueprint, request, jsonify
from models import db, Kitchen

kitchen_bp = Blueprint('kitchen', __name__)

# Create a new Kitchen
@kitchen_bp.route('/kitchens', methods=['POST'])
def create_kitchen():
    data = request.json
    new_kitchen = Kitchen(
        name=data.get('name'),
        email=data.get('email'),
        password=data.get('password'),  # Ensure to hash passwords in production
        contact=data.get('contact'),
        location=data.get('location'),
        new_field_2=data.get('new_field_2'),
        city=data.get('city'),
        status=data.get('status'),
        order_id=data.get('order_id'),
        country=data.get('country'),
        state=data.get('state'),
        district=data.get('district'),
        address=data.get('address')
    )
    db.session.add(new_kitchen)
    db.session.commit()
    return jsonify({'message': 'Kitchen created successfully', 'kitchen_id': new_kitchen.id}), 201

# Get a list of all Kitchens
#this is kitchen route
@kitchen_bp.route('/kitchens', methods=['GET'])
def get_kitchens():
    kitchens = Kitchen.query.all()
    kitchen_list = [{
        'id': kitchen.id,
        'name': kitchen.name,
        'email': kitchen.email,
        'contact': kitchen.contact,
        'location': kitchen.location,
        # Add other fields as needed
    } for kitchen in kitchens]
    return jsonify(kitchen_list), 200

# Get a specific Kitchen by ID
@kitchen_bp.route('/kitchens/<int:id>', methods=['GET'])
def get_kitchen(id):
    kitchen = Kitchen.query.get_or_404(id)
    kitchen_data = {
        'id': kitchen.id,
        'name': kitchen.name,
        'email': kitchen.email,
        'contact': kitchen.contact,
        'location': kitchen.location,
        # Add other fields as needed
    }
    return jsonify(kitchen_data), 200

# Update a Kitchen by ID
@kitchen_bp.route('/kitchens/<int:id>', methods=['PUT'])
def update_kitchen(id):
    data = request.json
    kitchen = Kitchen.query.get_or_404(id)

    kitchen.name = data.get('name', kitchen.name)
    kitchen.email = data.get('email', kitchen.email)
    kitchen.contact = data.get('contact', kitchen.contact)
    kitchen.location = data.get('location', kitchen.location)
    # Update other fields similarly as needed

    db.session.commit()
    return jsonify({'message': 'Kitchen updated successfully'}), 200

# Delete a Kitchen by ID
@kitchen_bp.route('/kitchens/<int:id>', methods=['DELETE'])
def delete_kitchen(id):
    kitchen = Kitchen.query.get_or_404(id)
    db.session.delete(kitchen)
    db.session.commit()
    return jsonify({'message': 'Kitchen deleted successfully'}), 200

