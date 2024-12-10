from flask import Blueprint
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash,current_app, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.manager import Manager, db
from datetime import datetime
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from extensions import bcrypt
from werkzeug.utils import secure_filename
import os
from utils.services import get_model_counts ,allowed_file ,get_image, get_user_query
from base64 import b64encode


manager_bp = Blueprint('manager', __name__,template_folder='../templates/manager', static_folder='../static')

# Route to display Manager's Dashboard
@manager_bp.route('/', methods=['GET', 'POST'])
def manager_dashboard():
    user_name = session.get('user_name', 'User')
    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id)
    return render_template('manager_index.html', 
                           user_name=user_name,
                           role=role, 
                           encoded_image = image_data,
                           )

# Route to Add a new manager
@manager_bp.route('/add', methods=['GET', 'POST'])
def add_manager():

    role = session.get('role')                 # Get the role from  the session
    user_name = session.get('user_name') 
    user_id = session.get('user_id')
    image_data= get_image(role, user_id)       
    user = get_user_query(role, user_id)
    if request.method == 'POST':
        name = request.form['name']     # Get the name from  the form
        email = request.form['email']   # Get the email from  the form
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')  # Hash password
        contact = request.form.get('contact')   # Get the contact from the form
        image = request.files.get('image')  # Get the image from the form

        image_binary = None
        if image and allowed_file(image.filename):
            image_binary = image.read()

        # Check if the email is already in use
        existing_email = Manager.query.filter_by(email=email).first()
        if existing_email:
            flash("Error: Email is already in use.", "danger")
            return render_template('add_manager.html',role=role, user_name=user_name)

        # Check if the contact number is already in use
        existing_contact = Manager.query.filter_by(contact=contact).first()
        if existing_contact:
            flash("Error: Contact number is already in use.", "danger")
            return render_template('add_manager.html',role=role, user_name=user_name)

        # Create manager instance and add to database
        new_manager = Manager(name=name, 
                        email=email, 
                        password=password, 
                        contact=contact,
                        image=image_binary)
        try:
            db.session.add(new_manager)
            db.session.commit()
            flash("Manager added successfully!", "success")
            return redirect(url_for('manager.add_manager'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding manager: {str(e)}", "danger")
    
    return render_template('add_manager.html', 
                           role=role,
                           user_name=user.name, 
                           encoded_image=image_data)

"""
# Route for get all Managers
@manager_bp.route('/managers', methods=['GET'])
def get_managers():
    role = session.get('role')
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    counts = get_model_counts()
    try:
        role = role.decode('utf-8') if isinstance(role, bytes) else role
        user_name = user_name.decode('utf-8') if isinstance(user_name, bytes) else user_name

        managers = Manager.query.all()
        
        # Convert images to Base64 format
        for manager in managers:
            if manager.image:
                manager.image_base64 = f"data:image/jpeg;base64,{b64encode(manager.image).decode('utf-8')}"
            else:
                manager.image_base64 = None

        return render_template('managers.html', managers=managers, role=role, user_name=user_name, **counts ,encoded_image=image_data)
    except Exception as e:
        flash(f"Error retrieving managers: {str(e)}", "danger")
        return render_template('managers.html', managers=[], role=role, user_name=user_name,encoded_image=image_data)

"""

"""
@manager_bp.route('/managers', methods=['GET'])
def get_managers():
    role = session.get('role')
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id)
    counts = get_model_counts()

    try:
        role = role.decode('utf-8') if isinstance(role, bytes) else role
        user_name = user_name.decode('utf-8') if isinstance(user_name, bytes) else user_name

        managers = Manager.query.all()
        active_managers = [manager for manager in managers if manager.status == 'activated']

        # Convert images to Base64 format
        for manager in managers:
            if manager.image:
                manager.image_base64 = f"data:image/jpeg;base64,{b64encode(manager.image).decode('utf-8')}"
            else:
                manager.image_base64 = None

        return render_template('managers.html', managers=managers, role=role, user_name=user_name, **counts, encoded_image=image_data)
    except Exception as e:
        flash(f"Error retrieving managers: {str(e)}", "danger")
        # return render_template('managers.html', managers=[], role=role, user_name=user_name, encoded_image=image_data)
        return render_template('managers.html', managers=active_managers, manager_count=len(active_managers), role=role, user_name=user_name, **counts, encoded_image=image_data)


"""
@manager_bp.route('/managers', methods=['GET'])
def get_managers():
    role = session.get('role')
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    image_data = get_image(role, user_id)  # Fetch user image
    counts = get_model_counts()  # Fetch model counts (e.g., for dashboard stats)
    user = get_user_query(role, user_id)
    # Get filter status from request parameters
    filter_status = request.args.get('status', 'all').lower()

    try:
        # Decode role and user_name if they are bytes
        role = role.decode('utf-8') if isinstance(role, bytes) else role
        # user_name = user_name.decode('utf-8') if isinstance(user_name, bytes) else user_name

        # Fetch managers based on filter
        if filter_status == 'activated':
            managers = Manager.query.filter_by(status='activated').all()
        elif filter_status == 'deactivated':
            managers = Manager.query.filter_by(status='deactivated').all()
        else:  # 'all' or no filter
            managers = Manager.query.all()

        # Convert images to Base64 format for rendering
        for manager in managers:
            if manager.image:
                manager.image_base64 = f"data:image/jpeg;base64,{b64encode(manager.image).decode('utf-8')}"
            else:
                manager.image_base64 = None

        # Render the template with filtered managers
        return render_template(
            'managers.html',
            managers=managers,
            role=role,
            user_name=user.name,
            filter=filter_status,  # Pass the filter to the template
            **counts,
            encoded_image=image_data
        )
    except Exception as e:
        flash(f"Error retrieving managers: {str(e)}", "danger")
        return render_template(
            'managers.html',
            managers=[],
            role=role,
            user_name=user.name,
            filter=filter_status,
            **counts,
            encoded_image=image_data
        )

# Route for edit the manager
@manager_bp.route('/edit/<int:manager_id>', methods=['GET', 'POST'])
def edit_manager(manager_id):
    manager = Manager.query.get_or_404(manager_id)
    user_id = session.get('user_id')
    role = session.get('role')
    image_data = get_image(role, user_id)
    user = get_user_query(role, user_id)

    if isinstance(role, bytes):
        role = role.decode('utf-8')
    # if isinstance(user_name, bytes):
    #     user_name = user_name.decode('utf-8')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form.get('password')
        image = request.files.get('image')  # Get the image from the form if provided

        # Validate if email already exists (excluding the current manager)
        existing_manager_email = Manager.query.filter(Manager.email == email, Manager.id != manager.id).first()
        if existing_manager_email:
            flash("The email is already in use by another manager.", "danger")
            return render_template('edit_manager.html', manager=manager, role=role, user_name=user.name,encoded_image=image_data)

        # Validate if contact already exists (excluding the current manager)
        existing_manager_contact = Manager.query.filter(Manager.contact == contact, Manager.id != manager.id).first()
        if existing_manager_contact:
            flash("The contact number is already in use by another manager.", "danger")
            return render_template('edit_manager.html', manager=manager, role=role, user_name=user.name,encoded_image=image_data)

        # Update manager details
        manager.name = name
        manager.email = email
        manager.contact = contact

        # If password is provided, hash and update it
        if password:
            manager.password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Handle image update if a new image is uploaded
        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            manager.image = image_binary

        try:
            db.session.commit()
            flash("Manager updated successfully!", "success")
            return redirect(url_for('manager.get_managers'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating manager: {str(e)}", "danger")

    return render_template('edit_manager.html', manager=manager, role=role, user_name=user.name,encoded_image=image_data)


# Route for delete the manager
@manager_bp.route('/delete/<int:manager_id>', methods=['GET', 'POST'])
def delete_manager(manager_id):
    manager = Manager.query.get_or_404(manager_id)

    try:
        manager.status = 'deactivated'
        # db.session.delete(manager)
        db.session.commit()
        flash("Manager deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('manager.get_managers'))


# Route for profile of the manager
@manager_bp.route('/manager/<int:manager_id>', methods=['GET'])
def get_manager_profile(manager_id):
    try:
        # Query the manager by id
        manager = Manager.query.get_or_404(manager_id)

        return render_template('manager_profile.html', manager=manager)

    except Exception as e:
        flash(f"Error retrieving manager profile: {str(e)}", "danger")
        return redirect(url_for('manager.get_managers'))