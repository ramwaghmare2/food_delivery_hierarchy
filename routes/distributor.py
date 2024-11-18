from flask import Blueprint, redirect, render_template, url_for, request, flash, session, current_app
from models.kitchen import Kitchen
from models.distributor import Distributor
from werkzeug.security import check_password_hash, generate_password_hash
from models import db
from werkzeug.utils import secure_filename
import bcrypt
import os

distributor_bp = Blueprint('distributor', __name__, template_folder='../templates/distributor', static_folder='../static')


@distributor_bp.route('/')
def distributor_home():
    user_name = session.get('user_name', 'User')
    return render_template('d_index.html',user_name=user_name)


@distributor_bp.route('/all-distributor', methods=['GET'])
def all_distributor():
    role = session.get('role')
    all_distributors = Distributor.query.all()
    return render_template('d_all_distributor.html', all_distributors=all_distributors,role=role)



@distributor_bp.route('/all-kitchens', methods=['GET'])
def distrubutor_all_kitchens():
    role = session.get('role')
    all_kitchens = Kitchen.query.all()
    return render_template('kitchen/all_kitchens.html', all_kitchens=all_kitchens , role=role)


@distributor_bp.route('/kitchen/<int:kitchen_id>')
def view_kitchen(kitchen_id):
    kitchen = Kitchen.query.get_or_404(kitchen_id)
    return render_template('d_kitchen_detail.html', kitchen=kitchen)


@distributor_bp.route('/delete-kitchen/<int:kitchen_id>', methods=['GET','POST'])
def delete_kitchen(kitchen_id):
    kitchen = Kitchen.query.get_or_404(kitchen_id)
    db.session.delete(kitchen)
    db.session.commit()
    flash('Kitchen deleted successfully!')
    return redirect(url_for('distributor.distrubutor_all_kitchens'))



@distributor_bp.route('/add-kitchen', methods=['GET','POST'])
def add_kitchen():
    try:

        if request.method == 'POST':

            if Kitchen.query.filter_by(email=request.form.get('email')).first() or Kitchen.query.filter_by(contact=request.form.get('mobile_number')).first():
                flash('Kitchen with this email or mobile number already exists.')
                return redirect(url_for('distributor.add_kitchen'))

            hashed_password = generate_password_hash(request.form.get('password'))

            new_kitchen = Kitchen(
                name = request.form.get('name'),
                email = request.form.get('email'),
                password = hashed_password,
                contact = request.form.get('mobile_number'),
                city = request.form.get('city'),
                country = request.form.get('country'),
                state = request.form.get('state'),
                district = request.form.get('district'),
                address = request.form.get('address')
            )

            db.session.add(new_kitchen)
            db.session.commit()

            return redirect(url_for('distributor.distributor_home'))

        return render_template('d_add_kitchen.html')
    
    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('distributor.add_kitchen'))
    

# Function for delete the distributor
@distributor_bp.route('/delete/<int:distributor_id>', methods=['GET', 'POST'])
def delete_distributor(distributor_id):
    
    distributor = Distributor.query.get_or_404(distributor_id)

    try:
        db.session.delete(distributor)
        db.session.commit()
        flash("Distributor deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting manager: {str(e)}", "danger")

    return redirect(url_for('distributor.all_distributor'))



@distributor_bp.route('/login', methods=['GET','POST'])
def distributor_login():
    
    try:

        if request.method == 'POST':

            login_id = request.form.get('email_or_mobile_number')
            password = request.form.get('password')

            sd = Distributor.query.filter(
                (Distributor.contact == login_id) | (Distributor.email == login_id)
            ).first()

            if not sd or not check_password_hash(sd.password, password):
                flash('Invalid Credentials, Please check Mobile Number, Email or Password.')
                return redirect(url_for('distributor.distributor_login'))
            
            return redirect(url_for('distributor.distributor_home'))
        
        return render_template('d_login.html')
    
    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('distributor.distributor_login'))


# Function for image storage
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']




# Function for edit the super_distributor
@distributor_bp.route('/edit/<int:distributor_id>', methods=['GET', 'POST'])
def edit_distributor(distributor_id):
    distributor = Distributor.query.get_or_404(distributor_id)

    role = session.get('role')

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

        # Handle image update if a new image is uploaded
        if image and allowed_file(image.filename):
            # If a new image is uploaded, delete the old one
            if distributor.image:
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], distributor.image))
                except Exception as e:
                    flash(f"Error deleting old image: {str(e)}", "danger")
            
            # Save the new image
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
            distributor.image = image_filename

        try:
            db.session.commit()
            flash("Distributor updated successfully!", "success")
            return redirect(url_for('distributor.all_distributor'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating Distributor: {str(e)}", "danger")
            return render_template('edit_distributor.html', distributor=distributor, role=role)

    return render_template('edit_distributor.html', distributor=distributor, role=role)




@distributor_bp.route('/forgot-password', methods=['GET','POST'])
def distributor_forgot_password():
    if request.method == 'POST':
        return redirect(url_for('distributor.distributor_login'))
    return render_template('d_password.html')

@distributor_bp.route('/logout', methods=['GET','POST'])
def distributor_logout():
    return redirect(url_for('distributor.distributor_login'))