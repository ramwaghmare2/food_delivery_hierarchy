from flask import Blueprint, redirect, render_template, url_for, request, flash
from models.kitchen import Kitchen
from models.distributor import Distributor
from werkzeug.security import check_password_hash, generate_password_hash
from models import db

distributor_bp = Blueprint('distributor', __name__, template_folder='../templates/distributor', static_folder='../static')


@distributor_bp.route('/')
def distributor_home():
    return render_template('d_index.html')

@distributor_bp.route('/all-kitchens', methods=['GET'])
def distrubutor_all_kitchens():
    all_kitchens = Kitchen.query.all()
    return render_template('d_all_kitchens.html', all_kitchens=all_kitchens)


@distributor_bp.route('/kitchen/<int:kitchen_id>')
def view_kitchen(kitchen_id):
    kitchen = Kitchen.query.get_or_404(kitchen_id)
    return render_template('d_kitchen_detail.html', kitchen=kitchen)


@distributor_bp.route('/delete-kitchen/<int:kitchen_id>', methods=['POST'])
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
    

@distributor_bp.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    # Logic for updating distributor's information
    return render_template('d_edit_profile.html')



@distributor_bp.route('/forgot-password', methods=['GET','POST'])
def distributor_forgot_password():
    if request.method == 'POST':
        return redirect(url_for('distributor.distributor_login'))
    return render_template('d_password.html')

@distributor_bp.route('/logout', methods=['GET','POST'])
def distributor_logout():
    return redirect(url_for('distributor.distributor_login'))