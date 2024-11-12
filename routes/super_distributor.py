from flask import Blueprint, render_template, request, url_for, redirect, flash
from models.distributor import Distributor
from models.kitchen import Kitchen
from models.super_distributor import SuperDistributor
from werkzeug.security import check_password_hash, generate_password_hash
from models import db


super_distributor_bp = Blueprint('super_distributor', __name__, template_folder='../templates/super_distributor', static_folder='../static')


@super_distributor_bp.route('/super-distributor', methods=['GET'])
def super_distributor():
    return render_template('sd_index.html')

@super_distributor_bp.route('/all-kitchens', methods=['GET'])
def all_kitchen():
    all_kitchens = Kitchen.query.all()
    return render_template('sd_all_kitchens.html', all_kitchens=all_kitchens)

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
                country = request.form.get('country'),
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
    

@super_distributor_bp.route('/all_distributor', methods=['GET'])
def all_distributor():
    all_distributors = Distributor.query.all()
    return render_template('sd_all_distributor.html', all_distributors=all_distributors)


@super_distributor_bp.route('/add-distributor', methods=['GET', 'POST'])
def add_distributor():
    try:
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

            return redirect(url_for('super_distributor.super_distributor'))

        return render_template('sd_add_distributor.html')

    except Exception as e:
        flash(f'Error: {e}')
        return redirect(url_for('super_distributor.add_distributor'))


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
