from flask import Blueprint, request, jsonify, render_template ,flash ,redirect,url_for,session
from models import db, FoodItem ,Cuisine

food_item_bp = Blueprint('food_item', __name__)


@food_item_bp.route('/add_food_item', methods=['GET', 'POST'])
def add_food_item():
    user_id = session.get('user_id')
    if request.method == 'POST':
        item_name = request.form['item_name']
        description = request.form['description']
        price = request.form['price']
        cuisine_id = request.form['cuisine_id']
        
        try:
            new_food_item = FoodItem(
                item_name=item_name,
                description=description,
                price=price,
                cuisine_id=cuisine_id,
                kitchen_id=user_id
            )
            db.session.add(new_food_item)
            db.session.commit()
            flash('Food item added successfully!', 'success')
            return redirect(url_for('food_item.add_food_item'))  # Redirect after successful POST
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'error')
    cuisines = Cuisine.query.all()  # Fetch all cuisines for the dropdown
    return render_template('add_food_item.html', cuisines=cuisines ,user_id=user_id)



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
"""@food_item_bp.route('/food_items', methods=['GET'])
def get_food_items():
    food_items = FoodItem.query.all()
    food_item_list = [
        {
            'name': item.item_name,
            'description': item.description,
            'price': item.price,
            'kitchen_id': item.kitchen_id
        } for item in food_items
    ]
    return jsonify(food_item_list), 200"""

@food_item_bp.route('/food_items/<int:kitchen_id>', methods=['GET'])
def get_food_items_by_kitchen(kitchen_id):
    user_id=session.get('user_id')
    user_name = session.get('user_name')
    # Query to get food items for the given kitchen_id
    food_items = FoodItem.query.filter_by(kitchen_id=kitchen_id).all()
    # Render the template with the food items
    return render_template('food_item.html', food_items=food_items, kitchen_id=kitchen_id, user_id=user_id,user_name=user_name)


# Get a specific FoodItem by ID
"""@food_item_bp.route('/food_items/<int:id>', methods=['GET'])
def get_food_item(id):
    food_item = FoodItem.query.get_or_404(id)
    food_item_data = {
        'id': food_item.id,
        'name': food_item.name,
        'description': food_item.description,
        'price': food_item.price,
        'cuisine_id': food_item.cuisine_id
    }
    return jsonify(food_item_data), 200"""

# Update a FoodItem by ID
@food_item_bp.route('/food_items/edit/<int:id>', methods=['GET', 'POST'])
def edit_food_item(id):
    # Retrieve the food item by ID
    food_items = FoodItem.query.get_or_404(id)
    user_id= session.get('user_id')

    if request.method == 'POST':
        # Update food item with the form data
        food_items.name = request.form['name']
        food_items.description = request.form['description']
        food_items.price = request.form['price']
        
        # Commit the changes to the database
        db.session.commit()

        # Flash success message
        flash('Food item updated successfully!', 'success')
        
        # Redirect to the food items page or another appropriate page
        return redirect(url_for('food_item.get_food_items_by_kitchen', kitchen_id=food_items.kitchen_id))

    # If it's a GET request, render the edit form with the current data
    return render_template('edit_food_item.html', food_items=food_items ,user_id=user_id)

# Delete a FoodItem by ID
@food_item_bp.route('/food_items/delete/<int:item_id>', methods=['GET'])
def delete_food_item(item_id):
    item = FoodItem.query.get_or_404(item_id)
    kitchen_id = item.kitchen_id

    # Delete the food item
    db.session.delete(item)
    db.session.commit()

    flash('Food item deleted successfully', 'danger')
    return redirect(url_for('food_item.get_food_items_by_kitchen', kitchen_id=kitchen_id))
