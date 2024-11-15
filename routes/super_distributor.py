from flask import Blueprint, render_template, request, url_for, redirect, flash, session, current_app
from models.distributor import Distributor
from models.kitchen import Kitchen
from models.super_distributor import SuperDistributor
from werkzeug.security import check_password_hash, generate_password_hash
from models import db
from werkzeug.utils import secure_filename
import bcrypt
import os


super_distributor_bp = Blueprint('super_distributor', __name__, template_folder='../templates/super_distributor', static_folder='../static')


@super_distributor_bp.route('/super-distributor', methods=['GET'])
def super_distributor():
    return render_template('sd_index.html')

@super_distributor_bp.route('/all-kitchens', methods=['GET'])
def all_kitchen():
    all_kitchens = Kitchen.query.all()
    role = session.get('role')
    return render_template('sd_all_kitchens.html', all_kitchens=all_kitchens, role=role)

@super_distributor_bp.route('/add-kitchen', methods=['GET', 'POST'])
def add_kitchen():
    try:

        if request.method == 'POST':

            if Kitchen.query.filter_by(email=request.form.get('email')).first() or Kitchen.query.filter_by(contact=request.form.get('mobile_number')).first():
                flash('Kitchen with this email or mobile number already exists.')
                return redirect(url_for('super_distributor.add_kitchen'))

            hashed_password = generate_password_hash(request.form.get('password'))

            new_kitchen = Kitchen(
                name = request.form.get('name'),
                email = request.form.get('email'),
                password = hashed_password,
                contact = request.form.get('mobile_number'),
                city = request.form.get('city'),
                pin_code = request.form.get('pin_code'),
                state = request.form.get('state'),
                district = request.form.get('district'),
                address = request.form.get('address')
            )

            db.session.add(new_kitchen)
            db.session.commit()

            return redirect(url_for('super_distributor.super_distributor'))

        return render_template('sd_add_kitchen.html')
    
    
    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('super_distributor.add_kitchen'))
    

@super_distributor_bp.route('/all-super-distributor', methods=['GET'])
def all_super_distributor():
    role = session.get('role')
    all_distributors = SuperDistributor.query.all()
    return render_template('sd_all_distributor.html', all_super_distributors=all_distributors, role=role)


@super_distributor_bp.route('/add-distributor', methods=['GET', 'POST'])
def add_distributor():
    try:

        role = session.get('role')

        if request.method == 'POST':

            if Distributor.query.filter_by(email=request.form.get('email')).first() or Distributor.query.filter_by(contact=request.form.get('mobile_number')).first():
                flash('Distributor with this email or mobile number already exists.')
                return redirect(url_for('super_distributor.add_distributor'))

            hashed_password = generate_password_hash(request.form.get('password'))

            new_distributor = Distributor(
                name=request.form.get('name'),
                email=request.form.get('email'),
                password=hashed_password,
                contact=request.form.get('mobile_number')
            )

            db.session.add(new_distributor)
            db.session.commit()
            flash('Distributor Added Successfully.')
            return redirect(url_for('super_distributor.add_distributor'))

        return render_template('sd_add_distributor.html', role=role)

    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('super_distributor.add_distributor'))
    
@super_distributor_bp.route('/add-super-distributor', methods=['GET', 'POST'])
def add_super_distributor():
    try:

        role = session.get('role')

        if request.method == 'POST':

            if SuperDistributor.query.filter_by(email=request.form.get('email')).first() or SuperDistributor.query.filter_by(contact=request.form.get('mobile_number')).first():
                flash('Super Distributor with this email or mobile number already exists.')
                return redirect(url_for('super_distributor.add_super_distributor'))

            hashed_password = generate_password_hash(request.form.get('password'))

            new_distributor = SuperDistributor(
                name=request.form.get('name'),
                email=request.form.get('email'),
                password=hashed_password,
                contact=request.form.get('mobile_number')
            )

            db.session.add(new_distributor)
            db.session.commit()
            flash('Super Distributor Added Successfully.')
            return redirect(url_for('super_distributor.add_super_distributor'))

        return render_template('add_super_distributor.html', role=role)

    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('super_distributor.add_distributor'))


# Function for image storage
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Function for edit the super_distributor
@super_distributor_bp.route('/edit/<int:sd_id>', methods=['GET', 'POST'])
def edit_super_distributor(sd_id):
    sd = SuperDistributor.query.get_or_404(sd_id)

    role = session.get('role')

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
            return render_template('edit_super_distributor.html', super_distributor=sd, role=role)

        # Validate if contact already exists (excluding the current manager)
        existing_manager_contact = SuperDistributor.query.filter(SuperDistributor.contact == contact, SuperDistributor.id != SuperDistributor.id).first()
        if existing_manager_contact:
            flash("The contact number is already in use by another Super Distributor.", "danger")
            return render_template('edit_super_distributor.html', super_distributor=sd, role=role)

        # Update manager details
        sd.name = name
        sd.email = email
        sd.contact = contact

        # If password is provided, hash and update it
        if password:
            sd.password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Handle image update if a new image is uploaded
        if image and allowed_file(image.filename):
            # If a new image is uploaded, delete the old one
            if sd.image:
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], sd.image))
                except Exception as e:
                    flash(f"Error deleting old image: {str(e)}", "danger")
            
            # Save the new image
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
            sd.image = image_filename

        try:
            db.session.commit()
            flash("Super Distributor updated successfully!", "success")
            return redirect(url_for('super_distributor.all_super_distributor'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating Super Distributor: {str(e)}", "danger")
            return render_template('edit_super_distributor.html', super_distributor=sd, role=role)

    return render_template('edit_super_distributor.html', super_distributor=sd, role=role)


@super_distributor_bp.route('/login', methods=['GET', 'POST'])
def sd_login():
    try:

        if request.method == 'POST':

            login_id = request.form.get('mobile_number') or request.form.get('email')
            password = request.form.get('password')

            sd = SuperDistributor.query.filter(
                (SuperDistributor.contact == login_id) | (SuperDistributor.email == login_id)
            ).first()

            if not sd or not check_password_hash(sd.password, password):
                flash('Invalid Credentials, Please check Mobile Number, Email or Password.')
                return redirect(url_for('super_distributor.sd_login'))
            
            return redirect(url_for('super_distributor.super_distributor'))
        
        return render_template('sd_login.html')
    
    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('super_distributor.sd_login'))
    

@super_distributor_bp.route('/forgot-password', methods=['GET', 'POST'])
def sd_forgot_password():
    if request.method == 'POST':
        return redirect(url_for('super_distributor.sd_login'))
    return render_template('sd_password.html')


# Function for delete the super distributor
@super_distributor_bp.route('/delete/<int:sd_id>', methods=['GET', 'POST'])
def delete_super_distributor(sd_id):
    super_distributor = SuperDistributor.query.get_or_404(sd_id)

    try:
        db.session.delete(super_distributor)
        db.session.commit()
        flash("Super Distributor deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('super_distributor.all_super_distributor'))



@super_distributor_bp.route('/delete-kitchen/<int:kitchen_id>', methods=['POST'])
def delete_kitchen(kitchen_id):
    kitchen = Kitchen.query.get_or_404(kitchen_id)
    db.session.delete(kitchen)
    db.session.commit()
    flash('Kitchen deleted successfully!')
    return redirect(url_for('super_distributor.all_kitchen'))


@super_distributor_bp.route('/delete-distributor/<int:distributor_id>', methods=['POST'])
def delete_distributor(distributor_id):
    distributor = Distributor.query.get_or_404(distributor_id)
    db.session.delete(distributor)
    db.session.commit()
    flash('Distributor deleted successfully!')
    return redirect(url_for('super_distributor.all_distributor'))



@super_distributor_bp.route('/logout', methods=['GET'])
def sd_logout():
    return redirect(url_for('super_distributor.sd_login'))
