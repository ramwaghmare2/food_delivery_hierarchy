from flask import Blueprint, request, jsonify, session, redirect, render_template, flash, current_app, url_for
from models import db, Kitchen, Distributor
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import bcrypt
import os

kitchen_bp = Blueprint('kitchen', __name__, static_folder='../static')

# Create a new Kitchen
@kitchen_bp.route('/kitchens', methods=['GET','POST'])
def create_kitchen():
    user_name = session.get('user_name')
    distributors = Distributor.query.all()
    data = request.form
    role = session.get('role')
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
        return render_template('kitchen/add_kitchen.html', role=role,distributors=distributors,user_name=user_name)
        # return jsonify({'message': 'Kitchen created successfully', 'kitchen_id': new_kitchen.id}), 201
    return render_template('kitchen/add_kitchen.html', role=role,distributors=distributors,user_name=user_name)

# Get a list of all Kitchens
#this is kitchen route
@kitchen_bp.route('/all-kitchens', methods=['GET'])
def get_kitchens():
    role = session.get('role')
    user_name = session.get('user_name')
    kitchens = Kitchen.query.all()
    return render_template('distributor/d_all_kitchens.html', all_kitchens=kitchens, role=role ,user_name=user_name)


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

# Function for image storage
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']




# Function for edit the super_distributor
@kitchen_bp.route('/edit/<int:kitchen_id>', methods=['GET', 'POST'])
def edit_kitchen(kitchen_id):
    kitchen = Kitchen.query.get_or_404(kitchen_id)

    role = session.get('role')
    user_name = session.get('user_name')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form['password']
        image = request.files.get('image')  # Get the image from the form if it exists

        # Validate if email already exists (excluding the current kitchen)
        existing_kitchen_email = Kitchen.query.filter(Kitchen.email == email, Kitchen.id != Kitchen.id).first()
        if existing_kitchen_email:
            flash("The email is already in use by another Kitchen.", "danger")
            return render_template('kitchen/edit_kitchen.html', kitchen=kitchen, role=role,user_name=user_name)

        # Validate if contact already exists (excluding the current kitchen)
        existing_kitchen_contact = Kitchen.query.filter(Kitchen.contact == contact, Kitchen.id != Kitchen.id).first()
        if existing_kitchen_contact:
            flash("The contact number is already in use by another Kitchen.", "danger")
            return render_template('kitchen/edit_kitchen.html', kitchen=kitchen, role=role ,user_name=user_name)

        # Update kitchen details
        kitchen.name = name
        kitchen.email = email
        kitchen.contact = contact

        # If password is provided, hash and update it
        if password:
            kitchen.password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Handle image update if a new image is uploaded
        if image and allowed_file(image.filename):
            # If a new image is uploaded, delete the old one
            if kitchen.image:
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], kitchen.image))
                except Exception as e:
                    flash(f"Error deleting old image: {str(e)}", "danger")
            
            # Save the new image
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
            kitchen.image = image_filename

        try:
            db.session.commit()
            flash("Kitchen updated successfully!", "success")
            return redirect(url_for('distributor.distrubutor_all_kitchens'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating Kitchen: {str(e)}", "danger")
            return render_template('kitchen/edit_kitchen.html', kitchen=kitchen, role=role,user_name=user_name)

    return render_template('kitchen/edit_kitchen.html', kitchen=kitchen, role=role ,user_name=user_name)

# Function for delete the kitchen
@kitchen_bp.route('/delete/<int:kitchen_id>', methods=['GET', 'POST'])
def delete_kitchen(kitchen_id):
    kitchen = Kitchen.query.get_or_404(kitchen_id)

    try:
        kitchen.status = 'deactivated'
        # db.session.delete(kitchen)
        db.session.commit()
        flash("Kitchen deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('kitchen.get_kitchens'))

@kitchen_bp.route("/kitchen_dahsbord", methods=['GET', 'POST'])
def kitchen_dashboard():
    user_name = session.get('user_name', 'User')
    role = session.get('role')
    user_id = session.get('user_id')
    print(f"User Name: {user_name}, User ID: {user_id}")
    return render_template('kitchen/kitchen_index.html',user_name=user_name,user_id=user_id,role=role)
