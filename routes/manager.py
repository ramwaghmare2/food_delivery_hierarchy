from flask import Blueprint
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash,current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models.manager import Manager, db
from datetime import datetime
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from app import bcrypt
from werkzeug.utils import secure_filename
import os

manager_bp = Blueprint('manager', __name__,template_folder='../templates/manager')


@manager_bp.route('/', methods=['GET', 'POST'])
def dadmin_dashboard():
    return render_template('manager.html')

# Display the form to add manager
@manager_bp.route('/form', methods=['GET', 'POST'])
def manager():
    return render_template('add_manager.html')

# Add a new manager
@manager_bp.route('/add', methods=['GET', 'POST'])
def add_manager():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')  # Hash password
        contact = request.form.get('contact')
        image = request.files.get('image')  # Get the image from the form
        print(image)

        # Check if the image is valid
        image_filename = None
        if image and allowed_file(image.filename):
            # Secure the filename to prevent directory traversal
            image_filename = secure_filename(image.filename)
            # Save the image to the folder
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))

        # Check if the email is already in use
        existing_email = Manager.query.filter_by(email=email).first()
        if existing_email:
            flash("Error: Email is already in use.", "danger")
            return render_template('add_manager.html')

        # Check if the contact number is already in use
        existing_contact = Manager.query.filter_by(contact=contact).first()
        if existing_contact:
            flash("Error: Contact number is already in use.", "danger")
            return render_template('add_manager.html')

        # Create manager instance and add to db
        new_manager = Manager(name=name, email=email, password=password, contact=contact,image=image_filename)
        try:
            db.session.add(new_manager)
            db.session.commit()
            flash("Manager added successfully!", "success")
            return render_template('add_manager.html')  # Stay on the same page or redirect
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding manager: {str(e)}", "danger")

    return render_template('add_manager.html')

# Function for image storage
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Function for get all Managers
@manager_bp.route('/managers', methods=['GET'])
def get_managers():
    try:
        managers = Manager.query.all()
        return render_template('managers.html', managers=managers)
    except Exception as e:
        flash(f"Error retrieving managers: {str(e)}", "danger")
        return render_template('managers.html', managers=[])

# Function for edit the managers
@manager_bp.route('/edit/<int:manager_id>', methods=['GET', 'POST'])
def edit_manager(manager_id):
    manager = Manager.query.get_or_404(manager_id)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form['password']
        image = request.files.get('image')  # Get the image from the form if it exists

        # Validate if email already exists (excluding the current manager)
        existing_manager_email = Manager.query.filter(Manager.email == email, Manager.id != manager.id).first()
        if existing_manager_email:
            flash("The email is already in use by another manager.", "danger")
            return render_template('edit_manager.html', manager=manager)

        # Validate if contact already exists (excluding the current manager)
        existing_manager_contact = Manager.query.filter(Manager.contact == contact, Manager.id != manager.id).first()
        if existing_manager_contact:
            flash("The contact number is already in use by another manager.", "danger")
            return render_template('edit_manager.html', manager=manager)

        # Update manager details
        manager.name = name
        manager.email = email
        manager.contact = contact

        # If password is provided, hash and update it
        if password:
            manager.password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Handle image update if a new image is uploaded
        if image and allowed_file(image.filename):
            # If a new image is uploaded, delete the old one
            if manager.image:
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], manager.image))
                except Exception as e:
                    flash(f"Error deleting old image: {str(e)}", "danger")
            
            # Save the new image
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
            manager.image = image_filename

        try:
            db.session.commit()
            flash("Manager updated successfully!", "success")
            return redirect(url_for('manager.get_managers'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating manager: {str(e)}", "danger")
            return render_template('edit_manager.html', manager=manager)

    return render_template('edit_manager.html', manager=manager)

# Function for delete the manager
@manager_bp.route('/delete/<int:manager_id>', methods=['GET', 'POST'])
def delete_manager(manager_id):
    manager = Manager.query.get_or_404(manager_id)

    try:
        db.session.delete(manager)
        db.session.commit()
        flash("Manager deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('manager.get_managers'))

@manager_bp.route('/manager/<int:manager_id>', methods=['GET'])
def get_manager_profile(manager_id):
    try:
        # Query the manager by id
        manager = Manager.query.get_or_404(manager_id)

        return render_template('manager_profile.html', manager=manager)

    except Exception as e:
        flash(f"Error retrieving manager profile: {str(e)}", "danger")
        return redirect(url_for('manager.get_managers'))
