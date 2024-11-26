from flask import Blueprint, redirect, render_template, url_for, request, flash, session, current_app
from models.kitchen import Kitchen
from models.distributor import Distributor
from werkzeug.security import check_password_hash, generate_password_hash
from models import db ,SuperDistributor 
from werkzeug.utils import secure_filename
import bcrypt
import os
from utils.services import get_model_counts, allowed_file ,get_image
from base64 import b64encode

distributor_bp = Blueprint('distributor', __name__, template_folder='../templates/distributor', static_folder='../static')

# Route for distributor dashboard
@distributor_bp.route('/')
def distributor_home():
    user_name = session.get('user_name', 'User')
    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    return render_template('d_index.html',user_name=user_name,role=role ,encoded_image = image_data)

# Route for display all distributor
@distributor_bp.route('/all-distributor', methods=['GET'])
def all_distributor():
    role = session.get('role')
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    if role == 'Admin':
        # Admin sees all distributors
        all_distributors = Distributor.query.all()
    else:
        # Non-admin sees distributors linked to their super distributors
        super_distributors = SuperDistributor.query.filter_by(manager_id=user_id).all()
        super_distributor_ids = [sd.id for sd in super_distributors]
        all_distributors = Distributor.query.filter(Distributor.super_distributor.in_(super_distributor_ids)).all()
    # Convert images to Base64 format
    for distributors in all_distributors:
            if distributors.image:
                distributors.image_base64 = f"data:image/jpeg;base64,{b64encode(distributors.image).decode('utf-8')}"
            else:
                distributors.image_base64 = None
    return render_template('d_all_distributor.html', all_distributors=all_distributors,role=role,user_name=user_name, encoded_image=image_data)


# Route to display all kitchens
@distributor_bp.route('/all-kitchens', methods=['GET'])
def distrubutor_all_kitchens():
    role = session.get('role')
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id)  # Assuming 'user_id' is stored in the session
    counts = get_model_counts()
    if role == 'Admin':
            # Admin sees all kitchens
            all_kitchens = Kitchen.query.all()
    else:
            # Non-admin sees kitchens linked to their distributors
            super_distributors = SuperDistributor.query.filter_by(manager_id=user_id).all()
            super_distributor_ids = [sd.id for sd in super_distributors]
            distributors = Distributor.query.filter(Distributor.super_distributor.in_(super_distributor_ids)).all()
            distributor_ids = [dist.id for dist in distributors]
            all_kitchens = Kitchen.query.filter(Kitchen.distributor_id.in_(distributor_ids)).all()
    return render_template('kitchen/all_kitchens.html', all_kitchens=all_kitchens , role=role , user_name=user_name, **counts , encoded_image=image_data)

# Route to delete kitchen
@distributor_bp.route('/delete-kitchen/<int:kitchen_id>', methods=['GET','POST'])
def delete_kitchen(kitchen_id):
    kitchen = Kitchen.query.get_or_404(kitchen_id)
    db.session.delete(kitchen)
    db.session.commit()
    flash('Kitchen deleted successfully!')
    return redirect(url_for('distributor.distrubutor_all_kitchens'))

# Route for delete the distributor
@distributor_bp.route('/delete/<int:distributor_id>', methods=['GET', 'POST'])
def delete_distributor(distributor_id):
    
    distributor = Distributor.query.get_or_404(distributor_id)

    try:
        distributor.status = 'deactivated'
        # db.session.delete(distributor)
        db.session.commit()
        flash("Distributor deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('distributor.all_distributor'))

# Function for image storage
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Route for edit the distributor
@distributor_bp.route('/edit/<int:distributor_id>', methods=['GET', 'POST'])
def edit_distributor(distributor_id):
    distributor = Distributor.query.get_or_404(distributor_id)

    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form['password']
        image = request.files.get('image')  # Get the image from the form if it exists

        # Validate if email already exists (excluding the current distributor)
        existing_distributor_email = Distributor.query.filter(Distributor.email == email, Distributor.id != Distributor.id).first()
        if existing_distributor_email:
            flash("The email is already in use by another Distributor.", "danger")
            return render_template('edit_distributor.html', distributor=distributor, role=role)

        # Validate if contact already exists (excluding the current distributor)
        existing_distributor_contact = Distributor.query.filter(Distributor.contact == contact, Distributor.id != Distributor.id).first()
        if existing_distributor_contact:
            flash("The contact number is already in use by another Distributor.", "danger")
            return render_template('edit_distributor.html', distributor=distributor, role=role)

        # Update distributor details
        distributor.name = name
        distributor.email = email
        distributor.contact = contact

        # If password is provided, hash and update it
        if password:
            distributor.password = bcrypt.generate_password_hash(password).decode('utf-8')

        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            distributor.image = image_binary

        try:
            db.session.commit()
            flash("Distributor updated successfully!", "success")
            return redirect(url_for('distributor.all_distributor'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating Distributor: {str(e)}", "danger")
            return render_template('edit_distributor.html', distributor=distributor, role=role , encoded_image = image_data)

    return render_template('edit_distributor.html', distributor=distributor, role=role , encoded_image = image_data)
