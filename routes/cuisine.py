from flask import Blueprint, request, jsonify ,render_template,flash,redirect,url_for,session
from models import db, Cuisine

cuisine_bp = Blueprint('cuisine', __name__ , static_folder='../static')


@cuisine_bp.route('/cuisine', methods=['GET', 'POST'])
def add_cuisine():
    role = session.get('role')
    user_name = session.get('user_name')
    if request.method == 'POST':
        
        # Get the form data
        name = request.form.get('name')
        description = request.form.get('description', '')  # Optional field
        
        # Check if the cuisine already exists
        existing_cuisine = Cuisine.query.filter_by(name=name).first()
        if existing_cuisine:
            flash('Cuisine already exists!','info')
            return redirect(url_for('cuisine.add_cuisine'),role=role, user_name=user_name)
        
        # Create a new Cuisine object
        new_cuisine = Cuisine(name=name,description=description)
        
        try:
            # Add and commit to the database
            db.session.add(new_cuisine)
            db.session.commit()
            flash('Cuisine added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
        
        return redirect(url_for('cuisine.add_cuisine'))
    cuisines = Cuisine.query.order_by(Cuisine.id).all()
    # Render the template for GET requests
    return render_template('add_cuisine.html',cuisines=cuisines,role=role, user_name=user_name)

@cuisine_bp.route('/cuisine/delete/<int:id>', methods=['POST','GET'])
def delete_cuisine(id):
    cuisine = Cuisine.query.get_or_404(id)
    try:
        db.session.delete(cuisine)
        db.session.commit()
        flash('Cuisine deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'error')
    return redirect(url_for('cuisine.add_cuisine'))

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

""" Delete a Cuisine by ID
@cuisine_bp.route('/cuisines/<int:id>', methods=['DELETE'])
def delete_cuisine(id):
    cuisine = Cuisine.query.get_or_404(id)
    db.session.delete(cuisine)
    db.session.commit()
    return jsonify({'message': 'Cuisine deleted successfully'}), 200"""
