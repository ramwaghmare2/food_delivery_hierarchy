from flask import Blueprint, jsonify, request, render_template, redirect
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from models import Customer, db
from utils.helpers import format_response, handle_error
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'GET':
        return render_template('customer/register.html')

    try:
        data = request.form  # Use form data from the HTML form
        name = data.get('name')
        email = data.get('email')
        contact = data.get('contact')
        password = generate_password_hash(data.get('password'))
        address = data.get('address')

        # Check if email already exists
        if Customer.query.filter_by(email=email).first():
            return render_template('customer/register.html', error="Email already exists.")

        new_user = Customer(name=name, email=email, contact=contact, password=password, address=address)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/customer/login')
    except Exception as e:
        return handle_error(e)

@customer_bp.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'GET':
        return render_template('customer/login.html')

    try:
        data = request.form
        login_id = data.get('contact') or data.get('email')
        password = data.get('password')

        user = Customer.query.filter(
            (Customer.contact == login_id) | (Customer.email == login_id)
        ).first()

        if not user or not check_password_hash(user.password, password):
            return render_template('customer/login.html', error="Invalid credentials.")

        access_token = create_access_token(identity=user.id)
        return redirect(f'/customer/profile?token={access_token}')
    except Exception as e:
        return handle_error(e)

@customer_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    try:
        user_id = get_jwt_identity()
        user = Customer.query.get(user_id)

        if not user:
            return jsonify({'message': 'User not found'}), 404

        return render_template('customer/profile.html', user=user)
    except Exception as e:
        return handle_error(e)

@customer_bp.route('/logout', methods=['GET'])
def logout_user():
    return render_template('customer/logout.html')

@customer_bp.route('/delete', methods=['GET', 'POST'])
@jwt_required()
def delete_account():
    if request.method == 'GET':
        return render_template('customer/delete_account.html')

    try:
        data = request.form
        user_id = get_jwt_identity()
        user = Customer.query.get(user_id)

        if not user:
            return render_template('customer/delete_account.html', error="User not found.")
        
        if not check_password_hash(user.password, data['password']):
            return render_template('customer/delete_account.html', error="Invalid password.")

        db.session.delete(user)
        db.session.commit()
        return redirect('/customer/logout')
    except Exception as e:
        return handle_error(e)

@customer_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('customer/forgot_password.html')

    try:
        data = request.form
        user = Customer.query.filter(
            (Customer.contact == data.get('contact')) | 
            (Customer.email == data.get('email'))
        ).first()

        if not user:
            return render_template('customer/forgot_password.html', error="User not found.")

        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if new_password != confirm_password:
            return render_template('customer/forgot_password.html', error="Passwords do not match.")

        user.password = generate_password_hash(new_password)
        db.session.commit()
        return redirect('/customer/login')
    except Exception as e:
        return handle_error(e)
