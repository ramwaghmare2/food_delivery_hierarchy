from models import db 
from flask import Blueprint,render_template, flash
from utils.services import get_model_counts
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy.exc import IntegrityError
from models import Admin, Manager, SuperDistributor, Distributor, Kitchen
from utils.services import allowed_file
from base64 import b64encode

admin_bp = Blueprint('admin_bp', __name__, static_folder='../static')


# Helper function to create a user based on role
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

# Route for displaying admin dashboard
@admin_bp.route('/admin', methods=['GET'])
@role_required('Admin')
def admin_dashboard():
    from models import Manager, SuperDistributor, Distributor, Kitchen  # Delayed imports
    user_name = session.get('user_name', 'User')
    role = session.get('role')
    user_id = session.get('user_id')
    managers = Manager.query.all()
    super_distributors = SuperDistributor.query.all()
    distributors = Distributor.query.all()
    kitchens = Kitchen.query.all()
    counts = get_model_counts()
    # Query the admin by id
    admin = Admin.query.get_or_404(user_id)

    # Encode the image to Base64 for rendering in HTML
    encoded_image = None
    if admin.image:
        encoded_image = b64encode(admin.image).decode('utf-8')

    return render_template('admin/admin_index.html',
                            **counts,
                           admin=admin,
                           encoded_image=encoded_image,
                           managers=managers, 
                           super_distributors=super_distributors, 
                           distributors=distributors, 
                           kitchens=kitchens,
                           user_name=user_name,
                           role=role)

VALID_ROLES = ["Admin", "Manager", "SuperDistributor", "Distributor", "Kitchen"]

@admin_bp.route('/add_user/<role>', methods=['GET', 'POST'])
@role_required('Admin')
def add_user(role):
    if role not in VALID_ROLES:
        return jsonify({"error": "Invalid role"}), 400

    if request.method == 'POST':
        data = request.form
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        user = create_user(data, role)
        if user:
            return redirect(url_for('admin_bp.admin_dashboard'))
        else:
            return jsonify({"error": "User already exists or invalid role"}), 400

    return render_template('admin/add_user.html', role=role)
    
# Route for Sign Up
@admin_bp.route('/signup', methods=['GET', 'POST'])
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
            return jsonify({"error": "User already exists or invalid role"}), 400

    return render_template("admin/signup.html")

# Route for Login 
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        data = request.form
        print("Form Data:", data)  
        
        role = data.get('role')
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Map roles to their respective models
        role_model_map = {
            "Admin": Admin,
            "Manager": Manager,
            "SuperDistributor": SuperDistributor,
            "Distributor": Distributor,
            "Kitchen": Kitchen
        }
        
        # Get the appropriate model for the role
        model = role_model_map.get(role)
        if not model:
            return jsonify({"error": "Invalid role"}), 400
        
        # Query the database for the user
        user = model.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({"error": "Invalid email or password"}), 401

        # Store user data in the session
        session['user_id'] = user.id
        session['role'] = role
        session['user_name'] = f"{user.name}" if hasattr(user, 'name') else user.name
        print(user.name)

        # Redirect based on role with URLs
        dashboard_routes = {
            "Admin": "admin_bp.admin_dashboard",
            "Manager": "manager.manager_dashboard",
            "SuperDistributor": "super_distributor.super_distributor",
            "Distributor": "distributor.distributor_home",
            "Kitchen": "kitchen.kitchen_dashboard"
        }
        route_name = dashboard_routes.get(role)
        
        if not route_name:
            return jsonify({"error": "Dashboard route not defined for this role"}), 500
        
        # Redirect to the dashboard using `url_for`
        return redirect(url_for(route_name))

    return render_template('admin/login.html')


"""
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        data = request.form
        print("Form Data:", data)  
        
        role = data.get('role')
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        if role == "Admin":
            user = Admin.query.filter_by(email=email).first()
        elif role == "Manager":
            user = Manager.query.filter_by(email=email).first()
        elif role == "SuperDistributor":
            user = SuperDistributor.query.filter_by(email=email).first()
        elif role == "Distributor":
            user = Distributor.query.filter_by(email=email).first()
        elif role == "Kitchen":
            user = Kitchen.query.filter_by(email=email).first()
        else:
            return jsonify({"error": "Invalid role"}), 400

        if not user or not check_password_hash(user.password, password):
            return jsonify({"error": "Invalid email or password"}), 401

        session['user_id'] = user.id
        session['role'] = role

        # Redirect based on role
        if role == "Admin":
            return redirect(url_for('admin_bp.admin_dashboard'))
        elif role == "Manager":
            return redirect(url_for('manager.manager_dashboard'))
        elif role == "SuperDistributor":
            return redirect(url_for('super_distributor.super_distributor'))
        elif role == "Distributor":
            return redirect(url_for('distributor.distributor_home'))
        elif role == "Kitchen":
            return redirect(url_for('kitchen.kitchen_dashboard'))
        
    return render_template('admin/login.html') """

@admin_bp.route('/manager', methods=['GET'])
@role_required('Manager')  
def manager_dashboard():
    from models import SuperDistributor, Distributor, Kitchen
    super_distributors = SuperDistributor.query.all()
    distributors = Distributor.query.all()
    kitchens = Kitchen.query.all()

    return render_template('admin/manager_dashboard.html', 
                           super_distributors=super_distributors, 
                           distributors=distributors, 
                           kitchens=kitchens)


@admin_bp.route('/super_distributor', methods=['GET'])
@role_required('SuperDistributor')  
def super_distributor_dashboard():
    from models import Distributor, Kitchen
    distributors = Distributor.query.all()
    kitchens = Kitchen.query.all()

    return render_template('admin/super_distributor_dashboard.html', 
                           distributors=distributors, 
                           kitchens=kitchens)


@admin_bp.route('/distributor', methods=['GET'])
@role_required('Distributor')  
def distributor_dashboard():
    from models import Kitchen
    kitchens = Kitchen.query.all()

    return render_template('admin/distributor_dashboard.html', 
                           kitchens=kitchens)


@admin_bp.route('/kitchen', methods=['GET'])
@role_required('Kitchen')  
def kitchen_dashboard():
    from models import Kitchen
    kitchens = Kitchen.query.filter_by(id=session['user_id']).all()  

    return render_template('admin/kitchen_dashboard.html', kitchens=kitchens)

# Route for Logout
@admin_bp.route('/logout')
# @role_required('Admin')
def logout():
    session.pop('user_id', None)
    session.pop('role', None) 
    return render_template('admin/login.html')

# Route for profile of the manager
@admin_bp.route('/admin/<int:admin_id>', methods=['GET'])
def get_admin_profile(admin_id):
    role = session.get('role')

    # Query the admin by id
    admin = Admin.query.get_or_404(admin_id)

    # Encode the image to Base64 for rendering in HTML
    encoded_image = None
    if admin.image:
        encoded_image = b64encode(admin.image).decode('utf-8')

    return render_template('admin/admin_profile.html', admin=admin, role=role, encoded_image=encoded_image)

@admin_bp.route('/edit/<int:admin_id>', methods=['GET', 'POST'])
def edit_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)

    role = session.get('role')
    user_name = session.get('user_name')

    if isinstance(role, bytes):
        role = role.decode('utf-8')
    if isinstance(user_name, bytes):
        user_name = user_name.decode('utf-8')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form.get('contact')
        password = request.form.get('password')
        image = request.files.get('image')  # Get the image from the form if provided

        # Validate if email already exists (excluding the current manager)
        existing_admin_email = Admin.query.filter(Admin.email == email, admin.id != admin.id).first()
        if existing_admin_email:
            flash("The email is already in use by another admin.", "danger")
            return render_template('admin/edit_admin.html',admin=admin, role=role, user_name=user_name)

        # Validate if contact already exists (excluding the current manager)
        existing_admin_contact = Admin.query.filter(Admin.contact == contact, Admin.id != admin.id).first()
        if existing_admin_contact:
            flash("The contact number is already in use by another admin.", "danger")
            return render_template('admin/edit_admin.html', admin=admin, role=role, user_name=user_name)

        # Update manager details
        admin.name = name
        admin.email = email
        admin.contact = contact

        # If password is provided, hash and update it
        if password:
            admin.password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Handle image update if a new image is uploaded
        if image and allowed_file(image.filename):
            # Convert the image to binary data
            image_binary = image.read()
            admin.image = image_binary

        try:
            db.session.commit()
            flash("Admin updated successfully!", "success")
            return redirect(url_for('admin_bp.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating admin: {str(e)}", "danger")

    return render_template('admin/edit_admin.html', admin=admin, role=role, user_name=user_name)