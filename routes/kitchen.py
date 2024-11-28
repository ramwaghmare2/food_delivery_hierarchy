from flask import Blueprint, request, jsonify, session, redirect, render_template, flash, current_app, url_for
from models import db, Kitchen, Distributor, FoodItem
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import bcrypt
from utils.services import get_model_counts , get_image

kitchen_bp = Blueprint('kitchen', __name__, static_folder='../static')

################################## Route to add a new Kitchen ##################################
@kitchen_bp.route('/kitchens', methods=['GET','POST'])
def create_kitchen():
    user_id = session.get('user_id')
    role = session.get('role')
    image_data= get_image(role, user_id) 
    user_name = session.get('user_name')
    distributors = Distributor.query.all()
    data = request.form
    
    if request.method == 'POST':
        if role=='Distributor':
            distributor_id = session.get('user_id')
        else:
            distributor_id = request.form.get('distributor')
            
        hashed_password = generate_password_hash(data.get('password'))
        new_kitchen = Kitchen(
            name=data.get('name'),
            email=data.get('email'),
            password=hashed_password,  # Ensure to hash passwords in production
            contact=data.get('contact'),
            city=data.get('city'),
            pin_code=data.get('pin_code'),
            state=data.get('state'),
            district=data.get('district'),
            address=data.get('address'),
            distributor_id=distributor_id
        )
        db.session.add(new_kitchen)
        db.session.commit()
        flash('Kitchen Added Successfully.')
        return render_template('kitchen/add_kitchen.html', role=role,distributors=distributors,user_name=user_name ,encoded_image = image_data)
        # return jsonify({'message': 'Kitchen created successfully', 'kitchen_id': new_kitchen.id}), 201
    return render_template('kitchen/add_kitchen.html', role=role,distributors=distributors,user_name=user_name ,encoded_image = image_data)

################################## Route to Get a list of all Kitchens ##################################
@kitchen_bp.route('/all-kitchens', methods=['GET'])
def get_kitchens():
    role = session.get('role')
    user_name = session.get('user_name')
    kitchens = Kitchen.query.all()
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    counts = get_model_counts()
    return render_template('distributor/d_all_kitchens.html', all_kitchens=kitchens, role=role ,user_name=user_name, **counts , encoded_image=image_data)

################################## Route for edit the super_distributor ##################################
@kitchen_bp.route('/edit/<int:kitchen_id>', methods=['GET', 'POST'])
def edit_kitchen(kitchen_id):
    kitchen = Kitchen.query.get_or_404(kitchen_id)

    role = session.get('role')
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form['password']

        # Validate if email already exists (excluding the current kitchen)
        existing_kitchen_email = Kitchen.query.filter(Kitchen.email == email, Kitchen.id != Kitchen.id).first()
        if existing_kitchen_email:
            flash("The email is already in use by another Kitchen.", "danger")
            return render_template('kitchen/edit_kitchen.html', kitchen=kitchen, role=role,user_name=user_name, encoded_image=image_data)

        # Validate if contact already exists (excluding the current kitchen)
        existing_kitchen_contact = Kitchen.query.filter(Kitchen.contact == contact, Kitchen.id != Kitchen.id).first()
        if existing_kitchen_contact:
            flash("The contact number is already in use by another Kitchen.", "danger")
            return render_template('kitchen/edit_kitchen.html', kitchen=kitchen, role=role ,user_name=user_name ,encoded_image= image_data)

        # Update kitchen details
        kitchen.name = name
        kitchen.email = email
        kitchen.contact = contact

        # If password is provided, hash and update it
        if password:
            kitchen.password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            db.session.commit()
            flash("Kitchen updated successfully!", "success")
            return redirect(url_for('distributor.distrubutor_all_kitchens'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating Kitchen: {str(e)}", "danger")
            return render_template('kitchen/edit_kitchen.html', kitchen=kitchen, role=role,user_name=user_name, encoded_image =image_data)

    return render_template('kitchen/edit_kitchen.html', kitchen=kitchen, role=role ,user_name=user_name ,encoded_image = image_data)

################################## Route for delete the kitchen ##################################
@kitchen_bp.route('/delete/<int:kitchen_id>', methods=['GET', 'POST'])
def delete_kitchen(kitchen_id):
    kitchen = Kitchen.query.get_or_404(kitchen_id)
    food_items = FoodItem.query.filter_by(kitchen_id=kitchen_id)
    try:
        for item in food_items:
            item.status = 'deactivated'
        kitchen.status = 'deactivated'
        db.session.commit()
        flash("Kitchen deleted successfully!", "success")
        return redirect(url_for('distributor.distrubutor_all_kitchens'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('kitchen.get_kitchens'))

################################## Route for Display Kitchen Dashboard ##################################
@kitchen_bp.route("/kitchen_dashboard", methods=['GET', 'POST'])
def kitchen_dashboard():
    user_name = session.get('user_name', 'User')
    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    return render_template('kitchen/kitchen_index.html',user_name=user_name,user_id=user_id,role=role ,encoded_image= image_data)
