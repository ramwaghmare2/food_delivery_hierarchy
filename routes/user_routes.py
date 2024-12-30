from models import db, Admin, Manager, SuperDistributor, Distributor, Kitchen, Sales, Order, Customer, FoodItem
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import emit
from utils.services import allowed_file, get_image, get_user_query
from sqlalchemy.exc import IntegrityError
from utils.helpers import handle_error 
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from models.order import OrderItem
from extensions import bcrypt
from base64 import b64encode
from functools import wraps
from sqlalchemy import func
from app import socketio
from flask import request, g
from models.activitylog import ActivityLog
from .activity_log_service import log_user_activity
import uuid

user_bp = Blueprint('user_bp', __name__, static_folder='../static')
# Sessions permanent with a timeput
################################## Helper function to create a user based on role ##################################
def create_user(data, role):
    from models import db  
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    try:
        if role == "Admin":
            from models import Admin  
            new_user = Admin(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        elif role == "Manager":
            from models import Manager
            new_user = Manager(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        elif role == "SuperDistributor":
            from models import SuperDistributor
            new_user = SuperDistributor(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        elif role == "Distributor":
            from models import Distributor
            new_user = Distributor(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        elif role == "Kitchen":
            from models import Kitchen
            new_user = Kitchen(name=data['name'], email=data['email'], password=hashed_password, contact=data['contact'])
        else:
            return None
        db.session.add(new_user)
        db.session.commit()
        return new_user
    except IntegrityError:
        db.session.rollback()
        return None

def role_required(required_roles):
    """
    Decorator to enforce access control based on the user role.
    `required_roles` can be a single role or a list of roles.
    """
    if isinstance(required_roles, str):
        required_roles = [required_roles]  # Convert to list if it's a single role

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'role' not in session:
                return jsonify({"error": "Unauthorized access"}), 401
            if session['role'] not in required_roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)

        return decorated_view

    return wrapper

################################## Route for signup ##################################
@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        role = data.get('role')
        if data['password'] != data['confirmPassword']:
            return jsonify({"error": "Passwords do not match"}), 400
         
        user = create_user(data, role)
        if user:
            return render_template('admin/login.html')
        else:
            flash("User already exists or invalid role", "danger")
            return redirect(url_for('admin_bp.signup'))

    return render_template("admin/signup.html")

################################## globally defined role_model_map ##################################

ROLE_MODEL_MAP = {
    "Admin": Admin,
    "Manager": Manager,
    "SuperDistributor": SuperDistributor,
    "Distributor": Distributor,
    "Kitchen": Kitchen,
}

def get_model_by_role(role):
    return ROLE_MODEL_MAP.get(role)

################################## Route for Login ##################################

from werkzeug.security import check_password_hash, generate_password_hash
import bcrypt

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            data = request.form
            
            role = data.get('role')
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                flash("Email and password are required", 'danger')
                return redirect(url_for('user_bp.login'))
            
            model = ROLE_MODEL_MAP.get(role)
            if not model:
                flash("Invalid Role", 'danger')
                return redirect(url_for('user_bp.login'))
            
            user = model.query.filter_by(email=email).first()

            if not user:
                return jsonify({"error": f"No {role} found with this email."}), 404

            if role != 'Admin' and (user.status == 'deactivated' or user.status == ''):
                flash('User is Not Active', 'danger')
                return redirect(url_for('user_bp.login'))

            # Identify hash type and validate accordingly
            password_valid = False
            if user.password.startswith('pbkdf2:sha256'):
                # Validate pbkdf2:sha256 hash
                password_valid = check_password_hash(user.password, password)
            elif user.password.startswith('$2b$') or user.password.startswith('$2a$'):
                # Validate bcrypt hash
                password_valid = bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))
            elif user.password.startswith('scrypt:'):
                # Validate scrypt hash
                password_valid = check_password_hash(user.password, password)
            else:
                return jsonify({"error": "Unsupported hash format"}), 500

            if not password_valid:
                return jsonify({"error": f"Incorrect password for {role}."}), 401

            # Re-hash the password to unify it to pbkdf2:sha256 if necessary
            if not user.password.startswith('pbkdf2:sha256'):
                user.password = generate_password_hash(password)  # Update hash to pbkdf2:sha256
                db.session.commit()
            
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id

            # Activity log for user login
            log_user_activity(
                user_id=user.id,
                session_id=session_id,
                action='login',
                details=f"{role} login successful",
                ip_address=request.remote_addr,
                browser_info=request.user_agent.string,
                role=role
            )

            session['user_id'] = user.id
            session['role'] = role
            session['user_name'] = f"{user.name}" if hasattr(user, 'name') else user.name
            user.online_status = True
            user.last_seen = datetime.now(timezone.utc)
            db.session.commit()

            current_app.socketio.emit(
                'status_update',
                {
                    'user_id': user.id,
                    'status': 'online',
                    'role': role,
                    'last_seen': user.last_seen.isoformat()
                },
                to='*/'  # Broadcast to all connected clients
            )

            dashboard_routes = {
                "Admin": "admin_bp.admin_home",
                "Manager": "manager.manager_home",
                "SuperDistributor": "super_distributor.super_distributor",
                "Distributor": "distributor.distributor_home",
                "Kitchen": "kitchen.kitchen_home"
            }
            route_name = dashboard_routes.get(role)
            
            return redirect(url_for(route_name))
        
        return render_template('admin/login.html')

    except Exception as e:
        return handle_error(e)


################################## Logout Route  ##################################
@user_bp.route('/logout')
def logout():
    try:
        # Retrieve user information from session
        user_id = session.get('user_id')
        role = session.get('role')
        session_id = session.get('session_id')
        model = ROLE_MODEL_MAP.get(role)

        # If the role and user_id are valid, update online_status
        if model and user_id:
            user = model.query.get(user_id)
            if user:
                user.online_status = False
                user.last_seen = datetime.now(timezone.utc)
                db.session.commit()

                log = ActivityLog(
                    user_id=user.id,
                    action='logout',
                    role=role,
                    details=f"{role} logout successful",
                    ip_address=request.remote_addr,
                    browser_info=request.user_agent.string,
                    session_id=session_id
                )
                db.session.add(log)
                db.session.commit()

                # Emit status_update event for logout using socketio
                current_app.socketio.emit(
                    'status_update',
                    {'user_id': user.id, 
                     'status': 'offline', 
                     'role': role,
                     'laste_seen': user.last_seen.isoformat()
                     },
                    to='*/' 
                )

        # Clear the session
        session.clear()
        flash("You have logged out successfully!", "success")
        return redirect(url_for('user_bp.login'))
    except Exception as e:
        flash(f"Error during logout: {str(e)}", "danger")
        return redirect(url_for('user_bp.login'))

################################## Get All Manager Profile ##################################
@user_bp.route('/profile', methods=['GET'])
def get_profile():
    role = session.get('role')
    user_id = session.get('user_id')
    # user_name = session.get('user_name')

    role_model_map = {
                "Admin": Admin,
                "Manager": Manager,
                "SuperDistributor": SuperDistributor,
                "Distributor": Distributor,
                "Kitchen": Kitchen
            }
            
    model = role_model_map.get(role)
    
    user = model.query.filter_by(id=user_id).first()

    # Encode the image to Base64 for rendering in HTML
    encoded_image = None
    if user.image:
        encoded_image = b64encode(user.image).decode('utf-8')



    return render_template('admin/user_profile.html', 
                           user=user, 
                           role=role, 
                           encoded_image=encoded_image,
                           user_name=user.name,
                           user_id=user_id,
                           )

################################## Edit Admin ##################################
@user_bp.route('/profile-edit', methods=['GET', 'POST'])
def edit_profile():

    user_id = session.get('user_id')
    role = session.get('role')
    user = get_user_query(role, user_id)
    encoded_image = get_image(role, user_id)
    role_model_map = {
                "Admin": Admin,
                "Manager": Manager,
                "SuperDistributor": SuperDistributor,
                "Distributor": Distributor,
                "Kitchen": Kitchen
            }
            
    model = role_model_map.get(role)
    
    user = model.query.filter_by(id=user_id).first()
    

    image_data= get_image(role, user_id)

    if isinstance(role, bytes):
        role = role.decode('utf-8')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form.get('password')
        image = request.files.get('image')  # Get the image from the form if provided

        # Validate if email already exists (excluding the current manager)
        existing_email = model.query.filter(model.email == email, model.id != user.id).first()
        if existing_email:
            flash(f"The email is already in use by another {role}.", "danger")
            return redirect(url_for('admin_bp.edit_profile'))

        # Validate if contact already exists (excluding the current manager)
        existing_contact = model.query.filter(model.contact == contact, model.id != user.id).first()
        if existing_contact:
            flash(f"The contact number is already in use by another {role}.", "danger")
            return redirect(url_for('admin_bp.edit_profile'))

        # Update manager details
        user.name = name
        user.email = email
        user.contact = contact
        
        # If password is provided, hash and update it
        if password:
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Handle image update if a new image is uploaded
        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            user.image = image_binary

        try:
            db.session.commit()
            flash(f"{role} updated successfully!", "success")
            return redirect(url_for('user_bp.get_profile'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating {role}: {str(e)}", "danger")
            return redirect(url_for('user_bp.edit_profile'))

    return render_template('admin/edit_profile.html', 
                           user=user, 
                           role=role, 
                           user_name=user.name,
                           user_id=user_id,
                           encoded_image=encoded_image
                           )