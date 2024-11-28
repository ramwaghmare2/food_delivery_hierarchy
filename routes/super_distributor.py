from flask import Blueprint, render_template, request, url_for, redirect, flash, session
from models.distributor import Distributor
from models.super_distributor import SuperDistributor
from models.manager import Manager
from werkzeug.security import generate_password_hash
from models import db
import bcrypt
from utils.services import get_model_counts ,allowed_file, get_image
from base64 import b64encode


super_distributor_bp = Blueprint('super_distributor', __name__, template_folder='../templates/super_distributor', static_folder='../static')

################################## Route for Super Distributor Dashboard ##################################
@super_distributor_bp.route('/super-distributor', methods=['GET'])
def super_distributor():
    user_name = session.get('user_name', 'User')
    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    return render_template('sd_index.html',user_name=user_name,role="Super Distributor" ,encoded_image = image_data)

################################## Route for Get All Super Distributor's ##################################
@super_distributor_bp.route('/all-super-distributor', methods=['GET'])
def all_super_distributor():
    role = session.get('role')
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    counts = get_model_counts() 
    if role == 'Admin':
        # Admin sees all super distributors
        all_distributors = SuperDistributor.query.all()
    else:
        # Non-admin sees only their related super distributors
        all_distributors = SuperDistributor.query.filter_by(manager_id=user_id).all()
    # Convert images to Base64 format
    for distributors in all_distributors:
            if distributors.image:
                distributors.image_base64 = f"data:image/jpeg;base64,{b64encode(distributors.image).decode('utf-8')}"
            else:
                distributors.image_base64 = None
    
    return render_template('sd_all_distributor.html', all_super_distributors=all_distributors, role=role, user_name=user_name, **counts ,encoded_image = image_data)

################################## Route for Ass Distributor ##################################
@super_distributor_bp.route('/add-distributor', methods=['GET', 'POST'])
def add_distributor():
    role = session.get('role')
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    try:

        super_distributors = SuperDistributor.query.all() 


        if request.method == 'POST':
            image = request.files.get('image')
            if role== "SuperDistributor":
                super_distributor = session.get('user_id')
            else:
                super_distributor = request.form.get('super_distributor')

            image_binary = None
            if image and allowed_file(image.filename):
                image_binary = image.read()

            if Distributor.query.filter_by(email=request.form.get('email')).first() or Distributor.query.filter_by(contact=request.form.get('mobile_number')).first():
                flash('Distributor with this email or mobile number already exists.')
                return redirect(url_for('super_distributor.add_distributor'))

            hashed_password = generate_password_hash(request.form.get('password'))

            new_distributor = Distributor(
                name=request.form.get('name'),
                email=request.form.get('email'),
                password=hashed_password,
                contact=request.form.get('mobile_number'),
                super_distributor=super_distributor,
                image=image_binary
            )

            db.session.add(new_distributor)
            db.session.commit()
            flash('Distributor Added Successfully.')
            return redirect(url_for('super_distributor.add_distributor'))

        return render_template('sd_add_distributor.html', role=role,  super_distributors=super_distributors, user_name=user_name , encoded_image=image_data)

    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('super_distributor.add_distributor'))

################################## Add Super Distributor ##################################
@super_distributor_bp.route('/add-super-distributor', methods=['GET', 'POST'])
def add_super_distributor():
    
    role = session.get('role')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 
    try:
        
        user_name = session.get('user_name')
        

        managers = Manager.query.all()

        if request.method == 'POST':
            image = request.files.get('image')

            image_binary = None
            if image and allowed_file(image.filename):
                image_binary = image.read()

            if role== "Admin":
                manager_id = request.form.get('manager')
            else:
                manager_id = session.get('user_id')

            if SuperDistributor.query.filter_by(email=request.form.get('email')).first() or SuperDistributor.query.filter_by(contact=request.form.get('mobile_number')).first():
                flash('Super Distributor with this email or mobile number already exists.')
                return redirect(url_for('super_distributor.add_super_distributor'))

            hashed_password = generate_password_hash(request.form.get('password'))

            new_distributor = SuperDistributor(
                name=request.form.get('name'),
                email=request.form.get('email'),
                password=hashed_password,
                contact=request.form.get('mobile_number'),
                manager_id=manager_id,
                image=image_binary
            )

            db.session.add(new_distributor)
            db.session.commit()
            flash('Super Distributor Added Successfully.')
            return redirect(url_for('super_distributor.add_super_distributor'))

        return render_template('add_super_distributor.html', role=role,managers=managers, user_name=user_name, encoded_image = image_data)

    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('super_distributor.add_distributor'))


################################## Function for edit the super_distributor ##################################
@super_distributor_bp.route('/edit/<int:sd_id>', methods=['GET', 'POST'])
def edit_super_distributor(sd_id):
    sd = SuperDistributor.query.get_or_404(sd_id)

    role = session.get('role')
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    image_data= get_image(role, user_id) 

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form['password']
        image = request.files.get('image')  # Get the image from the form if it exists

        # Validate if email already exists (excluding the current manager)
        existing_manager_email = SuperDistributor.query.filter(SuperDistributor.email == email, SuperDistributor.id != SuperDistributor.id).first()
        if existing_manager_email:
            flash("The email is already in use by another Super Distributor.", "danger")
            return render_template('edit_super_distributor.html', super_distributor=sd, role=role , user_name=user_name)

        # Validate if contact already exists (excluding the current manager)
        existing_manager_contact = SuperDistributor.query.filter(SuperDistributor.contact == contact, SuperDistributor.id != SuperDistributor.id).first()
        if existing_manager_contact:
            flash("The contact number is already in use by another Super Distributor.", "danger")
            return render_template('edit_super_distributor.html', super_distributor=sd, role=role, user_name=user_name)

        # Update manager details
        sd.name = name
        sd.email = email
        sd.contact = contact

        # If password is provided, hash and update it
        if password:
            sd.password = bcrypt.generate_password_hash(password).decode('utf-8')

        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            sd.image = image_binary

        try:
            db.session.commit()
            flash("Super Distributor updated successfully!", "success")
            return redirect(url_for('super_distributor.all_super_distributor'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating Super Distributor: {str(e)}", "danger")
            return render_template('edit_super_distributor.html', super_distributor=sd, role=role ,user_name=user_name, encoded_image=image_data)

    return render_template('edit_super_distributor.html', super_distributor=sd, role=role ,user_name=user_name, encoded_image = image_data)


################################## Function for delete the super distributor ##################################
@super_distributor_bp.route('/delete/<int:sd_id>', methods=['GET', 'POST'])
def delete_super_distributor(sd_id):
    super_distributor = SuperDistributor.query.get_or_404(sd_id)

    try:
        super_distributor.status = 'deactivated'
        # db.session.delete(super_distributor)
        db.session.commit()
        flash("Super Distributor deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('super_distributor.all_super_distributor'))
